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
        "initial_message": "halo rate"
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



