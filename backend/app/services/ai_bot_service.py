import os
import re
import json
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.models.ticket import Ticket
from app.models.message import Message

class AIBotService:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    ESCALATION_KEYWORDS = [
        "cs", "manusia", "orang", "operator", "agent", "human",
        "bicara dengan cs", "hubungi cs", "tidak membantu", "buntu",
        "kecewa", "komplain", "parah", "tolong cs", "butuh orang"
    ]

    GREETING_KEYWORDS = ["halo", "hai", "hi", "pagi", "siang", "sore", "malam", "assalamualaikum", "help"]

    @classmethod
    def evaluate_message(cls, db: Session, user_message: str) -> Dict[str, Any]:
        """
        Evaluate customer message, match with Knowledge Base,
        and decide whether to deflect with AI answer or escalate to human CS.
        No emojis used in any responses.
        """
        cleaned_msg = user_message.lower().strip()
        words = set(re.findall(r'\b\w+\b', cleaned_msg))

        # 1. Check explicit escalation intent
        for kw in cls.ESCALATION_KEYWORDS:
            if kw in cleaned_msg:
                return {
                    "reply": "Baik, saya mengerti Anda ingin berbicara langsung dengan Customer Support. Menghubungkan Anda ke antrean agen kami.",
                    "confidence": 1.0,
                    "should_escalate": True,
                    "matched_kb_id": None
                }

        # 2. Check simple greeting
        if any(w in cls.GREETING_KEYWORDS for w in words) and len(words) <= 3:
            return {
                "reply": "Halo, saya Asisten AI Ciheul. Apa yang bisa saya bantu terkait kendala atau akun Anda hari ini?",
                "confidence": 0.95,
                "should_escalate": False,
                "matched_kb_id": None
            }

        # 3. Match with Knowledge Base in DB
        active_kb = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).all()
        best_match: Optional[KnowledgeBase] = None
        highest_score = 0.0

        for kb in active_kb:
            kb_words = set(re.findall(r'\b\w+\b', kb.question.lower()))
            if kb.keywords:
                kb_words.update(re.findall(r'\b\w+\b', kb.keywords.lower()))
            
            intersection = words.intersection(kb_words)
            if not intersection:
                continue

            score = len(intersection) / (len(words.union(kb_words)) ** 0.6)
            if score > highest_score:
                highest_score = score
                best_match = kb

        if best_match and highest_score >= 0.35:
            best_match.helpful_count += 1
            db.commit()
            
            reply_text = (
                f"{best_match.answer}\n\n"
                f"Apakah informasi ini membantu menyelesaikan kendala Anda? "
                f"Jika belum selesai, Anda dapat memilih Hubungi CS kapan saja."
            )
            return {
                "reply": reply_text,
                "confidence": round(min(highest_score * 1.5, 0.95), 2),
                "should_escalate": False,
                "matched_kb_id": best_match.id
            }

        # 4. Fallback: No confident match in Knowledge Base (Informative guide without premature escalation)
        return {
            "reply": (
                "Maaf, saya belum menemukan jawaban yang tepat untuk pertanyaan tersebut di basis pengetahuan kami.\n\n"
                "Anda dapat menanyakan informasi seputar:\n"
                "• Cara reset password dan ubah profil akun\n"
                "• Metode pembayaran dan refund/pengembalian dana\n"
                "• Kendala teknis aplikasi mobile\n"
                "• Profil dan integrasi API CIHEUL\n\n"
                "Atau ketik 'Hubungi CS' jika Anda ingin terhubung langsung ke Customer Support manusia."
            ),
            "confidence": 0.2,
            "should_escalate": False,
            "matched_kb_id": None
        }

    @classmethod
    def sanitize_pii(cls, text: str, customer_name: Optional[str] = None, agent_name: Optional[str] = None) -> str:
        """
        Sanitize all PII (emails, phone numbers, card numbers, national IDs, bank accounts, 
        and customer/agent personal names) from text before passing to external LLMs.
        """
        # 1. Mask credit/payment cards first (e.g. 16 digits grouped by 4 with spaces or hyphens)
        text = re.sub(r'\b(?:\d{4}[ -]){3}\d{4}\b', '[CARD_REDACTED]', text)

        # 2. Mask national ID (Indonesian NIK / KTP: 16 contiguous digits)
        text = re.sub(r'\b\d{16}\b', '[NIK_REDACTED]', text)

        # 3. Mask emails
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL_REDACTED]', text)

        # 4. Mask phone numbers (starts with +62, 08, 021, or formatted international pattern)
        text = re.sub(r'\b(?:\+?62|0)8[1-9]\d{7,10}\b', '[PHONE_REDACTED]', text)
        text = re.sub(r'\+?\d{1,3}[-.\s]\(?\d{2,4}\)?[-.\s]\d{3,5}[-.\s]\d{3,5}\b', '[PHONE_REDACTED]', text)

        # 5. Mask bank account numbers (10 to 14 contiguous digits)
        text = re.sub(r'\b\d{10,14}\b', '[ACCOUNT_REDACTED]', text)

        # 6. Mask customer name occurrences in message body
        if customer_name and len(customer_name.strip()) > 1:
            clean_cust = customer_name.strip()
            text = re.sub(re.escape(clean_cust), '[NAMA_PELANGGAN]', text, flags=re.IGNORECASE)

        # 7. Mask agent name occurrences in message body
        if agent_name and len(agent_name.strip()) > 1:
            clean_agent = agent_name.strip()
            text = re.sub(re.escape(clean_agent), '[NAMA_AGEN]', text, flags=re.IGNORECASE)

        # 8. Mask explicit name introductions (e.g. "nama saya Ahmad", "panggil saya Lisa")
        # Exclude common Indonesian verbs, prepositions, and non-name words from false-positive masking
        indonesian_non_name_words = {
            "belum", "sudah", "tidak", "bukan", "mau", "ingin", "bisa", "dapat",
            "lagi", "sedang", "akan", "hanya", "tetap", "ada", "juga", "pun",
            "selalu", "sering", "pernah", "tapi", "namun", "dan", "atau", "karena",
            "agar", "supaya", "untuk", "dengan", "pada", "di", "ke", "dari",
            "yang", "ini", "itu", "adalah", "yaitu", "akun", "email", "user",
            "nomor", "no", "terkendala", "error", "rusak", "hilang", "terblokir",
            "terkunci", "kenapa", "mengapa", "bagaimana", "tolong", "mohon"
        }

        def _mask_name_intro(match):
            prefix = match.group(1)
            candidate = match.group(2).strip()
            first_token = candidate.split()[0].lower()
            if first_token in indonesian_non_name_words:
                return match.group(0)
            return f"{prefix} [NAMA_PELANGGAN]"

        text = re.sub(
            r'\b(nama saya|nama ku|namaku|panggil saya|atas nama)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            _mask_name_intro,
            text,
            flags=re.IGNORECASE
        )

        return text

    @classmethod
    def generate_copilot_analysis(cls, db: Session, ticket: Ticket, messages: List[Message]) -> Dict[str, Any]:
        """
        Generate proactive Copilot 2 analysis:
        - What happened (summary)
        - Draft reply for the CS agent
        - Follow-up actions
        """
        if not messages:
            return {
                "summary": "Belum ada pesan yang tercatat pada tiket ini.",
                "draft_reply": f"Halo {ticket.customer.name if ticket.customer else 'Pelanggan'}, ada yang bisa kami bantu?",
                "follow_ups": ["Menunggu pesan pelanggan"]
            }

        # Anonymize participant identities before external processing
        anonymized_lines = []
        for m in messages:
            role = "Pelanggan" if m.sender_type == "CUSTOMER" else ("Agen CS" if m.sender_type == "AGENT" else m.sender_type)
            anonymized_lines.append(f"{role}: {m.content}")
        anonymized_conversation = "\n".join(anonymized_lines)

        cust_name = ticket.customer.name if ticket.customer else "Pelanggan"
        agent_name = ticket.assigned_agent.full_name if ticket.assigned_agent else None
        first_cust_msg = next((m.content for m in messages if m.sender_type == "CUSTOMER"), ticket.subject)

        # 1. If Gemini API key is available, call Gemini API with sanitized PII & anonymized identities
        if cls.GEMINI_API_KEY:
            try:
                sanitized_conversation = cls.sanitize_pii(anonymized_conversation, customer_name=cust_name, agent_name=agent_name)
                prompt = (
                    f"Anda adalah Copilot AI untuk agen Customer Support CIHEUL Technologies.\n"
                    f"Percakapan obrolan:\n{sanitized_conversation}\n\n"
                    f"Berikan output dalam format JSON valid tanpa markdown formatting dengan kunci:\n"
                    f"1. 'summary': Ringkasan 2 kalimat tentang masalah apa yang dialami pelanggan.\n"
                    f"2. 'draft_reply': Draf balasan profesional dan solutif untuk agen CS kirimkan ke pelanggan. Gunakan sapaan 'Halo [NAMA_PELANGGAN]'. DILARANG menggunakan emoji.\n"
                    f"3. 'follow_ups': Array berisi 2 rekomendasi tindakan teknis selanjutnya."
                )
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={cls.GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(gemini_url, json=payload)
                    if resp.status_code == 200:
                        content_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        cleaned_json = re.sub(r'^```json\s*|\s*```$', '', content_text.strip(), flags=re.MULTILINE)
                        res_data = json.loads(cleaned_json)
                        if isinstance(res_data, dict) and "draft_reply" in res_data:
                            res_data["draft_reply"] = res_data["draft_reply"].replace("[NAMA_PELANGGAN]", cust_name)
                        return res_data
            except Exception as e:
                pass  # Fallback to local intelligent analysis

        # 2. Local Intelligent Contextual Analysis (Dynamic KB Semantic Matching & Recency Awareness)
        cust_messages = [m.content for m in messages if m.sender_type == "CUSTOMER"]
        latest_cust_msg = cust_messages[-1] if cust_messages else ticket.subject
        combined_context = f"{ticket.subject} {latest_cust_msg}".lower()
        context_words = set(re.findall(r'\b\w+\b', combined_context))

        # Check explicit mention of file attachment or screenshot
        if any(w in combined_context for w in ["lampir", "file", "screenshot", "tangkapan", "layar", "ngirim berkas", "kirim berkas"]):
            summary = f"Pelanggan {cust_name} menanyakan atau mengeluhkan cara melampirkan berkas bukti kendala (tangkapan layar)."
            draft = (
                f"Halo {cust_name}, Anda dapat melampirkan gambar tangkapan layar atau berkas bukti kendala "
                f"(format PNG, JPG, atau PDF) secara langsung dengan menekan tombol ikon klip kertas di sebelah kiri kolom pesan."
            )
            follow_ups = [
                "Pandu pelanggan menekan ikon klip lampiran",
                "Tanyakan apakah kendala sudah jelas terlihat di gambar",
                "Tandai tiket Selesai"
            ]
            return {"summary": summary, "draft_reply": draft, "follow_ups": follow_ups}

        # Handle specific escalation domains that require human CS verification
        if "password" in combined_context or "kata sandi" in combined_context:
            summary = f"Pelanggan {cust_name} mengalami kendala akses atau reset kata sandi pada akunnya. Sistem otomatis telah mengarahkan panduan awal namun sesi dialihkan ke CS."
            draft = f"Halo {cust_name}, saya memahami kendala akses kata sandi pada akun Anda. Untuk membantu proses reset, mohon konfirmasikan apakah Anda masih memiliki akses ke alamat email terdaftar Anda?"
            follow_ups = ["Verifikasi kepemilikan email akun", "Kirim instruksi reset kata sandi", "Tandai tiket Selesai"]
            return {"summary": summary, "draft_reply": draft, "follow_ups": follow_ups}

        if "bayar" in combined_context or "pembayaran" in combined_context or "qris" in combined_context or "tagihan" in combined_context:
            summary = f"Pelanggan {cust_name} menanyakan konfirmasi transaksi atau kendala pembayaran. Agen perlu menanyakan nomor referensi transaksi."
            draft = f"Halo {cust_name}, terima kasih telah menghubungi kami. Untuk membantu pengecekan status pembayaran, mohon informasikan nomor referensi transaksi atau bukti transfer yang Anda miliki agar tim kami dapat melakukan verifikasi."
            follow_ups = ["Cek riwayat transaksi di modul pembayaran", "Kirim invoice resmi", "Tandai tiket Selesai"]
            return {"summary": summary, "draft_reply": draft, "follow_ups": follow_ups}

        if "aplikasi" in combined_context or "error" in combined_context or "bug" in combined_context or "loading" in combined_context or "crash" in combined_context:
            summary = f"Pelanggan {cust_name} melaporkan kendala teknis pada aplikasi (loading atau kegagalan sistem). Perlu investigasi log server."
            draft = f"Halo {cust_name}, mohon maaf atas ketidaknyamanan ini. Untuk membantu pemeriksaan kendala aplikasi, silakan coba tutup aplikasi sepenuhnya dan bersihkan cache perangkat Anda terlebih dahulu. Jika kendala masih berlanjut, mohon informasikan versi aplikasi serta detail pesan kesalahan yang muncul."
            follow_ups = ["Periksa error log pada server", "Laporkan ke tim Engineering jika berulang", "Tandai tiket Selesai"]
            return {"summary": summary, "draft_reply": draft, "follow_ups": follow_ups}

        # Match against 15 Knowledge Base FAQs using word overlap scoring
        active_kbs = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).all()
        best_kb = None
        best_score = 0.0

        for kb in active_kbs:
            kb_words = set(re.findall(r'\b\w+\b', kb.question.lower()))
            if kb.keywords:
                kb_words.update(re.findall(r'\b\w+\b', kb.keywords.lower()))
            intersection = context_words.intersection(kb_words)
            if not intersection:
                continue
            score = len(intersection) / (len(context_words.union(kb_words)) ** 0.55)
            if score > best_score:
                best_score = score
                best_kb = kb

        if best_kb and best_score >= 0.28:
            topic_clean = best_kb.question.rstrip('?').lower()
            summary = f"Pelanggan {cust_name} menanyakan kendala terkait: '{best_kb.question}'. Solusi tersedia di basis pengetahuan resmi CIHEUL."
            draft = (
                f"Halo {cust_name}, terkait pertanyaan Anda mengenai {topic_clean}:\n\n"
                f"{best_kb.answer}\n\n"
                f"Apakah panduan di atas membantu menyelesaikan kendala yang Anda alami?"
            )
            follow_ups = [
                f"Tawarkan bantuan teknis lanjutan terkait {best_kb.category}",
                "Konfirmasi apakah kendala sudah teratasi",
                "Tandai tiket Selesai"
            ]
            return {"summary": summary, "draft_reply": draft, "follow_ups": follow_ups}

        summary = f"Pelanggan {cust_name} sedang berkonsultasi mengenai: '{latest_cust_msg[:90]}'."
        draft = f"Halo {cust_name}, terima kasih telah menghubungi tim Support CIHEUL. Saya telah meninjau laporan Anda dan siap membantu menyelesaikan kendala ini. Mohon informasikan detail tambahan yang Anda alami."
        follow_ups = ["Minta detail tangkapan layar jika relevan", "Konfirmasi apakah kendala sudah teratasi", "Tandai tiket Selesai"]

        return {
            "summary": summary,
            "draft_reply": draft,
            "follow_ups": follow_ups
        }

    @classmethod
    def ask_copilot(cls, question: str, ticket: Ticket, messages: List[Message]) -> str:
        """Agent asks a custom question to Copilot about the active ticket."""
        cust_name = ticket.customer.name if ticket.customer else "Pelanggan"
        conv_summary = f"Tiket: {ticket.subject}, Status: {ticket.status}, Kategori: {ticket.category}."
        
        lower_q = question.lower()
        if "refund" in lower_q or "kembali" in lower_q:
            return f"Berdasarkan kebijakan standar CIHEUL, pengembalian dana dapat diproses dalam waktu 3x24 jam kerja jika transaksi terbukti gagal namun saldo terpotong."
        elif "sla" in lower_q or "waktu" in lower_q:
            return f"Batas waktu respons (SLA) untuk kategori {ticket.category} adalah maksimal 15 menit. Tiket ini dibuat pada {ticket.created_at.strftime('%H:%M WIB')}."
        elif "prioritas" in lower_q:
            return f"Tiket saat ini berada pada prioritas {ticket.priority}. Anda dapat menaikkan ke URGENT melalui panel rincian tiket jika terdapat eskalasi dampak besar."
        else:
            return f"Copilot siap membantu. Berdasarkan percakapan dengan {cust_name}, solusi tercepat adalah menanyakan detail identitas kendala dan memberikan instruksi langkah demi langkah."
