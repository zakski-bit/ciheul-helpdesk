import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Isolate test database: configure dedicated test SQLite DB so helpdesk.db is never touched
TEST_DB_PATH = os.path.join(backend_dir, "test_isolated.db")
if os.path.exists(TEST_DB_PATH):
    try:
        os.remove(TEST_DB_PATH)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, engine, Base
from app.core.init_db import init_database
from app.models.ticket import Ticket
from app.services.ai_bot_service import AIBotService

# Initialize clean isolated test database schema & seeds
init_database()

from main import app
client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def teardown_test_environment():
    """Ensure clean shutdown of TestClient and database connections so pytest exits cleanly."""
    yield
    client.close()
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_login_cs_agent():
    # CS Agent login
    res = client.post("/api/v1/auth/login", json={
        "email": "cs@ciheul.com",
        "password": "cs123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "CS_AGENT"

def test_login_invalid_password():
    res = client.post("/api/v1/auth/login", json={
        "email": "cs@ciheul.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_ai_bot_deflection():
    db = SessionLocal()
    try:
        # Question about reset password should match seeded FAQ
        result = AIBotService.evaluate_message(db, "bagaimana cara reset password akun?")
        assert result["should_escalate"] is False
        assert result["confidence"] >= 0.5
        assert "Lupa Password" in result["reply"]
    finally:
        db.close()

def test_ai_bot_escalation_intent():
    db = SessionLocal()
    try:
        # Explicit escalation keyword
        result = AIBotService.evaluate_message(db, "saya mau bicara dengan cs manusia sekarang!")
        assert result["should_escalate"] is True
        assert result["confidence"] == 1.0
    finally:
        db.close()

def test_widget_create_ticket_and_flow():
    # 1. Customer creates ticket via widget
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "test_session_token_12345",
        "customer_name": "Budi Pengujian",
        "customer_email": "budi@tester.com",
        "initial_message": "halo mau tanya cara bayar tagihan dengan qris"
    })
    assert create_res.status_code == 200
    ticket_data = create_res.json()
    ticket_id = ticket_data["id"]
    assert ticket_id is not None
    assert len(ticket_data["messages"]) >= 2  # Customer msg + AI reply

    # 2. Login as CS Agent to claim
    login_res = client.post("/api/v1/auth/login", json={
        "email": "cs@ciheul.com",
        "password": "cs123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. CS claims ticket
    claim_res = client.post(f"/api/v1/tickets/{ticket_id}/claim", headers=headers)
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "AGENT_ACTIVE"

    # 4. CS resolves ticket
    resolve_res = client.post(f"/api/v1/tickets/{ticket_id}/resolve", headers=headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

    # 5. Customer submits rating with valid session token on resolved ticket
    rate_res = client.post(f"/api/v1/tickets/{ticket_id}/rate", json={
        "session_token": "test_session_token_12345",
        "rating": 5,
        "feedback": "Sangat cepat dan solutif!"
    })
    assert rate_res.status_code == 200
    assert rate_res.json()["status"] == "success"

def test_password_unique_random_salts():
    from app.core.security import hash_password, verify_password
    h1 = hash_password("secretpassword")
    h2 = hash_password("secretpassword")
    assert h1 != h2
    assert "$" in h1
    assert "$" in h2
    assert verify_password("secretpassword", h1) is True
    assert verify_password("secretpassword", h2) is True
    assert verify_password("wrongpassword", h1) is False

def test_ticket_escalate_authorization():
    # Create ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "token_esc_123",
        "customer_name": "Testing Escalation",
        "initial_message": "Mohon bantuan teknis"
    })
    ticket_id = create_res.json()["id"]

    # 1. Anonymous escalate without valid session token -> 403 Forbidden
    res_bad = client.post(f"/api/v1/tickets/{ticket_id}/escalate", json={
        "session_token": "wrong_token_xyz"
    })
    assert res_bad.status_code == 403

    # 2. Escalate with matching customer session token -> 200 OK
    res_good = client.post(f"/api/v1/tickets/{ticket_id}/escalate", json={
        "session_token": "token_esc_123"
    })
    assert res_good.status_code == 200
    assert res_good.json()["status"] == "WAITING_AGENT"

def test_ticket_rating_security_and_validation():
    # 1. Create ticket (in BOT_ACTIVE status)
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "token_rate_456",
        "customer_name": "Testing Rating",
        "initial_message": "halo mau tanya fitur"
    })
    ticket_id = create_res.json()["id"]

    # 2. Try rating active ticket before it's resolved -> 400 Bad Request
    rate_unresolved = client.post(f"/api/v1/tickets/{ticket_id}/rate", json={
        "session_token": "token_rate_456",
        "rating": 5
    })
    assert rate_unresolved.status_code == 400

    # 3. Resolve ticket as CS Agent
    login_res = client.post("/api/v1/auth/login", json={"email": "cs@ciheul.com", "password": "cs123"})
    token = login_res.json()["access_token"]
    client.post(f"/api/v1/tickets/{ticket_id}/resolve", headers={"Authorization": f"Bearer {token}"})

    # 4. Try rating with wrong session token -> 403 Forbidden
    rate_wrong_cust = client.post(f"/api/v1/tickets/{ticket_id}/rate", json={
        "session_token": "different_session_999",
        "rating": 5
    })
    assert rate_wrong_cust.status_code == 403

    # 5. Try rating out of bounds (score 7) -> 422 Unprocessable Entity
    rate_invalid_score = client.post(f"/api/v1/tickets/{ticket_id}/rate", json={
        "session_token": "token_rate_456",
        "rating": 7
    })
    assert rate_invalid_score.status_code == 422

    # 6. Valid rating -> 200 OK
    rate_ok = client.post(f"/api/v1/tickets/{ticket_id}/rate", json={
        "session_token": "token_rate_456",
        "rating": 5,
        "feedback": "Layanan responsif"
    })
    assert rate_ok.status_code == 200

def test_knowledge_base_rbac():
    # 1. CS Agent tries to create KB article -> 403 Forbidden
    login_cs = client.post("/api/v1/auth/login", json={"email": "cs@ciheul.com", "password": "cs123"})
    cs_token = login_cs.json()["access_token"]
    kb_res_cs = client.post("/api/v1/knowledge-base", headers={"Authorization": f"Bearer {cs_token}"}, json={
        "question": "Apakah CS Agent bisa buat FAQ?",
        "answer": "Tidak boleh, khusus Admin"
    })
    assert kb_res_cs.status_code == 403

    # 2. Administrator creates KB article -> 200 OK
    login_admin = client.post("/api/v1/auth/login", json={"email": "admin@ciheul.com", "password": "admin123"})
    admin_token = login_admin.json()["access_token"]
    kb_res_admin = client.post("/api/v1/knowledge-base", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "question": "Kebijakan keamanan data perusahaan",
        "answer": "Data dienkripsi end-to-end sesuai standar ISO 27001",
        "category": "SECURITY"
    })
    assert kb_res_admin.status_code == 200
    assert kb_res_admin.json()["category"] == "SECURITY"

def test_websocket_agents_channel_security():
    # 1. Connect without token -> Rejected with 1008 Policy Violation
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/agents") as ws:
            ws.receive_text()

    # 2. Connect with valid CS Agent token -> Accepted
    login_res = client.post("/api/v1/auth/login", json={"email": "cs@ciheul.com", "password": "cs123"})
    token = login_res.json()["access_token"]
    with client.websocket_connect(f"/ws/agents?token={token}") as ws:
        ws.send_text('{"event":"ping"}')
        resp = ws.receive_text()
        assert "pong" in resp

def test_websocket_ticket_room_security_and_anti_spoofing():
    # Create ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "sess_ws_test_88",
        "customer_name": "Customer Security Test",
        "initial_message": "testing websocket security"
    })
    ticket_id = create_res.json()["id"]

    # 1. Connect without auth -> Rejected with 1008
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/ticket/{ticket_id}") as ws:
            ws.receive_text()

    # 2. Connect with customer session token -> Accepted
    with client.websocket_connect(f"/ws/ticket/{ticket_id}?session_token=sess_ws_test_88") as ws:
        # Customer attempts to spoof sender_type as "ADMIN"
        ws.send_text('{"event":"send_message","content":"Percobaan spoofing","sender_type":"ADMIN","sender_name":"Hacker"}')
        resp = ws.receive_text()
        import json
        data = json.loads(resp)
        # Server must enforce verified identity as CUSTOMER
        assert data["sender_type"] == "CUSTOMER"
        assert data["sender_name"] == "Customer Security Test"

def test_copilot_analysis_and_ask():
    # 1. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "cs@ciheul.com",
        "password": "cs123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "test_copilot_session_99",
        "customer_name": "Ravi Shankar",
        "initial_message": "Aplikasi sering logout sendiri setelah update terbaru"
    })
    ticket_id = create_res.json()["id"]

    # 3. Analyze with Copilot
    analysis_res = client.post(f"/api/v1/copilot/{ticket_id}/analyze", headers=headers)
    assert analysis_res.status_code == 200
    data = analysis_res.json()
    assert "summary" in data
    assert "draft_reply" in data
    assert len(data["follow_ups"]) >= 1

    # 4. Ask Copilot
    ask_res = client.post(f"/api/v1/copilot/{ticket_id}/ask", headers=headers, json={
        "question": "Berapa lama batas waktu SLA untuk kendala ini?"
    })
    assert ask_res.status_code == 200
    assert "SLA" in ask_res.json()["answer"]

def test_ai_bot_pii_sanitization():
    raw_text = "Nama saya Ahmad Syarif. NIK saya 3201012345670001 dan no rek 123456789012. Email user.test@gmail.com dan WhatsApp 081234567890. Kartu kredit 4111 2222 3333 4444."
    sanitized = AIBotService.sanitize_pii(raw_text, customer_name="Ahmad Syarif")
    assert "user.test@gmail.com" not in sanitized
    assert "[EMAIL_REDACTED]" in sanitized
    assert "081234567890" not in sanitized
    assert "[PHONE_REDACTED]" in sanitized
    assert "4111 2222 3333 4444" not in sanitized
    assert "[CARD_REDACTED]" in sanitized
    assert "3201012345670001" not in sanitized
    assert "[NIK_REDACTED]" in sanitized
    assert "123456789012" not in sanitized
    assert "[ACCOUNT_REDACTED]" in sanitized
    assert "Ahmad Syarif" not in sanitized

    # Test false-positive prevention on Indonesian verbs following 'nama saya'
    false_positive_sentence = "Nama saya belum bisa login ke aplikasi."
    sanitized_fp = AIBotService.sanitize_pii(false_positive_sentence)
    assert "belum bisa" in sanitized_fp
    assert "[NAMA_PELANGGAN]" not in sanitized_fp

    # Test genuine name introduction masking
    intro_sentence = "Halo tim support, perkenalkan nama saya Lisa Wardhana mohon bantuannya."
    sanitized_intro = AIBotService.sanitize_pii(intro_sentence)
    assert "Lisa Wardhana" not in sanitized_intro
    assert "[NAMA_PELANGGAN]" in sanitized_intro

def test_copilot_fallback_no_hallucination():
    db = SessionLocal()
    try:
        from app.models.ticket import Ticket
        from app.models.message import Message
        ticket = Ticket(
            subject="Kendala password akun",
            category="ACCOUNT",
            priority="HIGH",
            status="WAITING_AGENT"
        )
        msg = Message(
            ticket_id=ticket.id,
            sender_type="CUSTOMER",
            sender_name="Budi",
            content="Saya lupa password akun saya dan tidak bisa login"
        )
        analysis = AIBotService.generate_copilot_analysis(db, ticket, [msg])
        draft = analysis["draft_reply"]
        # Must not claim email was already sent
        assert "baru saja kami kirimkan" not in draft
        assert "apakah Anda masih memiliki akses" in draft
    finally:
        db.close()

def test_ticket_input_validation_boundaries():
    # Message exceeding 3000 chars should be rejected with 422
    huge_message = "A" * 3500
    res = client.post("/api/v1/tickets", json={
        "session_token": "token_boundary_test",
        "customer_name": "Boundary Tester",
        "initial_message": huge_message
    })
    assert res.status_code == 422

def test_customer_facing_agent_id_masking():
    # 1. Create ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "session_masking_99",
        "customer_name": "Masking Tester",
        "initial_message": "Mohon bantuan akun"
    })
    ticket_id = create_res.json()["id"]

    # 2. Login CS & claim ticket
    login_res = client.post("/api/v1/auth/login", json={"email": "cs@ciheul.com", "password": "cs123"})
    token = login_res.json()["access_token"]
    claim_res = client.post(f"/api/v1/tickets/{ticket_id}/claim", headers={"Authorization": f"Bearer {token}"})
    assert claim_res.status_code == 200
    assert claim_res.json()["assigned_agent_id"] is not None

    # 3. Check customer-facing active ticket endpoint -> assigned_agent_id must be None
    active_res = client.get("/api/v1/tickets/active/session_masking_99")
    assert active_res.status_code == 200
    active_data = active_res.json()
    assert active_data["assigned_agent_id"] is None
    assert active_data["agent_name"] is not None

def test_production_safeguards_raise_error():
    from app.core.config import Settings
    import os
    # Temporarily simulate production environment with default secret key
    old_env = os.environ.get("ENVIRONMENT")
    try:
        # Test exact lowercase and uppercase 'PROD' and 'staging' aliases
        for env_val in ["production", "PROD", "Production", "staging", "STAGING"]:
            os.environ["ENVIRONMENT"] = env_val
            with pytest.raises(RuntimeError) as exc_info:
                Settings()
            assert "FATAL SECURITY ERROR" in str(exc_info.value)
    finally:
        if old_env:
            os.environ["ENVIRONMENT"] = old_env
        else:
            del os.environ["ENVIRONMENT"]

def test_websocket_in_band_auth_handshake():
    # 1. Create ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "inband_auth_sess_1",
        "customer_name": "Inband Customer",
        "initial_message": "halo inband"
    })
    ticket_id = create_res.json()["id"]

    # 2. Connect WITHOUT token in query string, then send auth event
    with client.websocket_connect(f"/ws/ticket/{ticket_id}") as ws:
        import json
        ws.send_text(json.dumps({
            "event": "auth",
            "session_token": "inband_auth_sess_1"
        }))
        # Now send chat message
        ws.send_text(json.dumps({
            "event": "send_message",
            "content": "Pesan via inband handshake auth"
        }))
        resp = ws.receive_text()
        data = json.loads(resp)
        assert data["event"] == "new_message"
        assert data["sender_type"] == "CUSTOMER"
        assert data["content"] == "Pesan via inband handshake auth"

def test_websocket_payload_and_content_length_limits():
    # 1. Create ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "limit_test_sess_2",
        "customer_name": "Limit Tester",
        "initial_message": "halo limit"
    })
    ticket_id = create_res.json()["id"]

    # 2. Connect and send oversized message (> 3000 chars)
    with client.websocket_connect(f"/ws/ticket/{ticket_id}?session_token=limit_test_sess_2") as ws:
        import json
        huge_text = "X" * 3500
        ws.send_text(json.dumps({
            "event": "send_message",
            "content": huge_text
        }))
        resp = ws.receive_text()
        data = json.loads(resp)
        assert data["event"] == "error"
        assert "3000" in data["message"]

def test_websocket_rate_limiting():
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "rate_test_sess_3",
        "customer_name": "Rate Tester",
        "initial_message": "halo tolong cs"
    })
    ticket_id = create_res.json()["id"]

    with client.websocket_connect(f"/ws/ticket/{ticket_id}?session_token=rate_test_sess_3") as ws:
        import json
        error_received = False
        for i in range(8):
            ws.send_text(json.dumps({
                "event": "send_message",
                "content": f"Pesan cepat {i}"
            }))
            resp = ws.receive_text()
            data = json.loads(resp)
            if data.get("event") == "error" and ("Batas" in data.get("message", "") or "rate" in data.get("message", "").lower()):
                error_received = True
                break
        assert error_received is True

def test_honest_payment_fallback_draft():
    db = SessionLocal()
    try:
        from app.models.ticket import Ticket
        from app.models.message import Message
        ticket = Ticket(
            subject="Pembayaran via QRIS belum masuk",
            category="BILLING",
            priority="HIGH",
            status="WAITING_AGENT"
        )
        msg = Message(
            ticket_id=ticket.id,
            sender_type="CUSTOMER",
            sender_name="Siti",
            content="Saya sudah bayar qris tapi statusnya belum terupdate"
        )
        analysis = AIBotService.generate_copilot_analysis(db, ticket, [msg])
        draft = analysis["draft_reply"]
        # Must not falsely claim gateway has verified the transaction
        assert "sedang kami verifikasi pada gateway" not in draft
        assert "nomor referensi transaksi atau bukti transfer" in draft
    finally:
        db.close()

def test_production_safeguards_reject_empty_and_weak_passwords():
    from app.core.config import Settings
    import os
    old_env = os.environ.get("ENVIRONMENT")
    old_secret = os.environ.get("SECRET_KEY")
    old_admin_pwd = os.environ.get("ADMIN_PASSWORD")
    old_cs_pwd = os.environ.get("CS_PASSWORD")
    try:
        # 1. Unset ENVIRONMENT should raise error (fail-closed)
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
        with pytest.raises(RuntimeError) as exc:
            Settings()
        assert "ENVIRONMENT variable is required and must be explicitly set" in str(exc.value)

        # 2. Whitespace-only ENVIRONMENT should raise error
        os.environ["ENVIRONMENT"] = "   "
        with pytest.raises(RuntimeError) as exc:
            Settings()
        assert "ENVIRONMENT variable is required and must be explicitly set" in str(exc.value)

        # 3. Unknown ENVIRONMENT should raise error
        os.environ["ENVIRONMENT"] = "invalid_unknown_env"
        with pytest.raises(RuntimeError) as exc:
            Settings()
        assert "Unknown ENVIRONMENT" in str(exc.value)

        # 4. Production with strong secret but empty ADMIN_PASSWORD
        os.environ["ENVIRONMENT"] = "production"
        os.environ["SECRET_KEY"] = "a" * 35
        os.environ["ADMIN_PASSWORD"] = ""
        os.environ["CS_PASSWORD"] = "strong_cs_password_2026"
        with pytest.raises(RuntimeError) as exc:
            Settings()
        assert "ADMIN_PASSWORD cannot be empty" in str(exc.value)

        # 4. Production with strong secret but weak ADMIN_PASSWORD
        os.environ["ADMIN_PASSWORD"] = "password123"
        with pytest.raises(RuntimeError) as exc:
            Settings()
        assert "rejected weak or default ADMIN_PASSWORD" in str(exc.value)

        # 5. Production with strong secret and short CS_PASSWORD (< 8 chars)
        os.environ["ADMIN_PASSWORD"] = "super_strong_admin_pass"
        os.environ["CS_PASSWORD"] = "short"
        with pytest.raises(RuntimeError) as exc:
            Settings()
        assert "minimum 8 characters" in str(exc.value)
    finally:
        for k, v in [("ENVIRONMENT", old_env), ("SECRET_KEY", old_secret), ("ADMIN_PASSWORD", old_admin_pwd), ("CS_PASSWORD", old_cs_pwd)]:
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]

def test_login_schema_rejects_empty_password():
    # Password empty should fail with 422 Unprocessable Entity
    res = client.post("/api/v1/auth/login", json={"email": "cs@ciheul.com", "password": ""})
    assert res.status_code == 422
    # Password too short (< 5 chars) should fail with 422
    res2 = client.post("/api/v1/auth/login", json={"email": "cs@ciheul.com", "password": "123"})
    assert res2.status_code == 422

def test_rate_limiter_login():
    from app.core.rate_limiter import login_rate_limiter
    try:
        test_ip = "192.168.77.88"
        hit_429 = False
        for i in range(25):
            res = client.post(
                "/api/v1/auth/login",
                json={"email": "cs@ciheul.com", "password": "wrongpassword123"},
                headers={"x-forwarded-for": test_ip}
            )
            if res.status_code == 429:
                hit_429 = True
                assert "Retry-After" in res.headers
                assert "Terlalu banyak percobaan login" in res.json()["detail"]
                break
        assert hit_429 is True
    finally:
        login_rate_limiter.reset()

def test_rate_limiter_ticket_creation():
    from app.core.rate_limiter import ticket_create_rate_limiter
    try:
        test_ip = "192.168.77.99"
        hit_429 = False
        for i in range(35):
            res = client.post(
                "/api/v1/tickets",
                json={
                    "customer_name": f"Spam Tester {i}",
                    "customer_email": f"spam{i}@test.com",
                    "session_token": f"rate_limit_token_{i}",
                    "subject": f"Spam Ticket {i}",
                    "category": "GENERAL",
                    "initial_message": f"Spam message {i}"
                },
                headers={"x-forwarded-for": test_ip}
            )
            if res.status_code == 429:
                hit_429 = True
                assert "Retry-After" in res.headers
                assert "Terlalu banyak permintaan pembuatan tiket" in res.json()["detail"]
                break
        assert hit_429 is True
    finally:
        ticket_create_rate_limiter.reset()

def test_ticket_active_via_header():
    # 1. Create a ticket with a distinct session token
    sess_token = "sess_secure_header_test_999"
    create_res = client.post("/api/v1/tickets", json={
        "customer_name": "Header Test Customer",
        "customer_email": "header@test.com",
        "session_token": sess_token,
        "subject": "Header Ticket Test",
        "category": "GENERAL",
        "initial_message": "Testing active ticket via X-Session-Token header"
    })
    assert create_res.status_code == 200
    created_id = create_res.json()["id"]

    # 2. Query GET /api/v1/tickets/active WITHOUT token in URL path, but with X-Session-Token header
    res = client.get("/api/v1/tickets/active", headers={"X-Session-Token": sess_token})
    assert res.status_code == 200
    data = res.json()
    assert data is not None
    assert data["id"] == created_id
    assert data["customer_name"] == "Header Test Customer"

def test_rate_limiter_anti_spoofing_ignores_untrusted_forwarded_for():
    from app.core.config import settings
    from app.core.rate_limiter import InMemoryRateLimiter
    from fastapi import Request, HTTPException
    from unittest.mock import Mock
    import asyncio

    # Ensure proxy headers are untrusted (default)
    original_trust = getattr(settings, "TRUST_PROXY_HEADERS", False)
    settings.TRUST_PROXY_HEADERS = False

    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60, name="test_anti_spoof")

    # Simulate 4 requests from the same socket client host ("192.168.1.100"),
    # but the client maliciously sends changing X-Forwarded-For headers
    mock_request = Mock(spec=Request)
    mock_request.client = Mock()
    mock_request.client.host = "192.168.1.100"

    hit_429 = False
    for i in range(4):
        mock_request.headers = {"x-forwarded-for": f"10.0.0.{i}"}
        try:
            asyncio.run(limiter(mock_request))
        except HTTPException as e:
            if e.status_code == 429:
                hit_429 = True
                break

    settings.TRUST_PROXY_HEADERS = original_trust
    assert hit_429 is True, "Rate limiter was bypassed by spoofed X-Forwarded-For header!"

def test_rate_limiter_bounded_memory_cleanup():
    import time
    from app.core.rate_limiter import InMemoryRateLimiter
    from fastapi import Request
    from unittest.mock import Mock
    import asyncio

    limiter = InMemoryRateLimiter(max_requests=10, window_seconds=1, name="test_mem", max_tracked_ips=50)

    # Populate 80 keys
    mock_request = Mock(spec=Request)
    mock_request.client = Mock()
    mock_request.headers = {}
    for i in range(80):
        mock_request.client.host = f"10.20.{i // 256}.{i % 256}"
        asyncio.run(limiter(mock_request))

    # Force cleanup with timestamp in the future: records must not exceed max_tracked_ips
    limiter._cleanup_expired(time.time() + 2)
    assert len(limiter._records) <= 50

def test_file_attachment_upload_and_validation():
    import io
    # 1. Create a ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "test_upload_session_999",
        "customer_name": "Rian Pengunggah",
        "initial_message": "ada kendala pembayaran eror"
    })
    assert create_res.status_code == 200
    ticket_id = create_res.json()["id"]

    # 2. Upload valid image
    fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest_image_bytes")
    fake_img.name = "screenshot_kendala.png"
    upload_res = client.post(
        f"/api/v1/tickets/{ticket_id}/upload",
        files={"file": ("screenshot_kendala.png", fake_img, "image/png")},
        data={"session_token": "test_upload_session_999"}
    )
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert data["status"] == "success"
    assert "screenshot_kendala.png" in data["content"]
    assert "/uploads/" in data["file_url"]

    # 3. Reject unsupported extension
    bad_file = io.BytesIO(b"malicious script")
    bad_file.name = "exploit.exe"
    bad_res = client.post(
        f"/api/v1/tickets/{ticket_id}/upload",
        files={"file": ("exploit.exe", bad_file, "application/octet-stream")},
        data={"session_token": "test_upload_session_999"}
    )
    assert bad_res.status_code == 400
    assert "tidak didukung" in bad_res.json()["detail"]

    # 4. Upload as authenticated CS agent
    login_res = client.post("/api/v1/auth/login", json={
        "email": "cs@ciheul.com",
        "password": "cs123"
    })
    agent_token = login_res.json()["access_token"]
    doc_file = io.BytesIO(b"%PDF-1.4 test pdf content")
    doc_file.name = "panduan_resolusi.pdf"
    agent_upload_res = client.post(
        f"/api/v1/tickets/{ticket_id}/upload",
        files={"file": ("panduan_resolusi.pdf", doc_file, "application/pdf")},
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert agent_upload_res.status_code == 200
    assert agent_upload_res.json()["status"] == "success"

def test_copilot_recency_and_followup_generation():
    # 1. Create a ticket
    create_res = client.post("/api/v1/tickets", json={
        "session_token": "test_copilot_session_777",
        "customer_name": "Dewi Analisis",
        "initial_message": "halo bot"
    })
    ticket_id = create_res.json()["id"]

    # 2. CS Agent logs in and analyzes ticket
    login_res = client.post("/api/v1/auth/login", json={
        "email": "cs@ciheul.com",
        "password": "cs123"
    })
    agent_token = login_res.json()["access_token"]

    copilot_res = client.post(
        f"/api/v1/copilot/{ticket_id}/analyze",
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert copilot_res.status_code == 200
    analysis = copilot_res.json()
    assert "draft_reply" in analysis
    assert len(analysis["follow_ups"]) >= 1
    assert analysis["customer_name"] == "Dewi Analisis"





