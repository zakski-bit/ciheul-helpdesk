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

        # 4. Fallback: Confidence too low -> Escalate to human
        return {
            "reply": "Maaf, sistem kami belum memiliki catatan spesifik terkait kendala ini. Sesi obrolan diteruskan ke Customer Support kami.",
            "confidence": 0.2,
            "should_escalate": True,
            "matched_kb_id": None
        }

    @classmethod
    def sanitize_pii(cls, text: str) -> str:
        """Sanitize PII (emails, phone numbers, card numbers) from text before passing to external LLMs."""
        # 1. Mask credit/payment cards first (e.g. 16 digits grouped by 4 or contiguous)
        text = re.sub(r'\b(?:\d{4}[ -]?){3}\d{4}\b', '[CARD_REDACTED]', text)
        # 2. Mask emails
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL_REDACTED]', text)
        # 3. Mask phone numbers
        text = re.sub(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', '[PHONE_REDACTED]', text)
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

        conversation_text = "\n".join([f"{m.sender_name}: {m.content}" for m in messages])
        cust_name = ticket.customer.name if ticket.customer else "Pelanggan"
        first_cust_msg = next((m.content for m in messages if m.sender_type == "CUSTOMER"), ticket.subject)

        # 1. If Gemini API key is available, call Gemini API with sanitized PII
        if cls.GEMINI_API_KEY:
            try:
                sanitized_conversation = cls.sanitize_pii(conversation_text)
                prompt = (
                    f"Anda adalah Copilot AI untuk agen Customer Support CIHEUL Technologies.\n"
                    f"Percakapan pelanggan:\n{sanitized_conversation}\n\n"
                    f"Berikan output dalam format JSON valid tanpa markdown formatting dengan kunci:\n"
                    f"1. 'summary': Ringkasan 2 kalimat tentang masalah apa yang dialami pelanggan.\n"
                    f"2. 'draft_reply': Draf balasan profesional dan solutif untuk agen CS kirimkan ke {cust_name}. DILARANG menggunakan emoji.\n"
                    f"3. 'follow_ups': Array berisi 2 rekomendasi tindakan teknis selanjutnya."
                )
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={cls.GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(gemini_url, json=payload)
                    if resp.status_code == 200:
                        content_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        cleaned_json = re.sub(r'^```json\s*|\s*```$', '', content_text.strip(), flags=re.MULTILINE)
                        return json.loads(cleaned_json)
            except Exception as e:
                pass  # Fallback to local intelligent analysis

        # 2. Local Intelligent Contextual Analysis (RAG & Rules)
        lower_first = first_cust_msg.lower()
        if "password" in lower_first or "kata sandi" in lower_first:
            summary = f"Pelanggan {cust_name} mengalami kendala akses atau reset kata sandi pada akunnya. Sistem otomatis telah mengarahkan panduan awal namun sesi dialihkan ke CS."
            draft = f"Halo {cust_name}, saya memahami kendala akses kata sandi pada akun Anda. Untuk membantu proses reset, mohon konfirmasikan apakah Anda masih memiliki akses ke alamat email terdaftar Anda?"
            follow_ups = ["Verifikasi status kepemilikan email akun", "Tandai kategori Akun & Keamanan"]
        elif "bayar" in lower_first or "pembayaran" in lower_first or "qris" in lower_first or "tagihan" in lower_first:
            summary = f"Pelanggan {cust_name} menanyakan metode pembayaran atau konfirmasi status transaksi. Membutuhkan verifikasi gateway pembayaran."
            draft = f"Halo {cust_name}, terima kasih telah menunggu. Transaksi Anda saat ini sedang kami verifikasi pada gateway pembayaran kami. Bisa tolong sebutkan nomor referensi transaksi atau bukti transfer Anda?"
            follow_ups = ["Cek riwayat mutasi pembayaran di dashboard finance", "Kirim invoice resmi"]
        elif "aplikasi" in lower_first or "error" in lower_first or "bug" in lower_first or "loading" in lower_first:
            summary = f"Pelanggan {cust_name} melaporkan kendala teknis pada aplikasi (loading atau kegagalan sistem). Perlu investigasi log server."
            draft = f"Halo {cust_name}, mohon maaf atas ketidaknyamanan ini. Untuk membantu pemeriksaan kendala aplikasi, silakan coba tutup aplikasi sepenuhnya dan bersihkan cache perangkat Anda terlebih dahulu. Jika kendala masih berlanjut, mohon informasikan versi aplikasi serta detail pesan kesalahan yang muncul."
            follow_ups = ["Periksa error log pada server", "Laporkan ke tim Engineering jika berulang"]
        else:
            summary = f"Pelanggan {cust_name} membuka konsultasi terkait: '{first_cust_msg[:90]}'. Tiket telah masuk dalam antrean aktif penanganan CS."
            draft = f"Halo {cust_name}, terima kasih telah menghubungi tim Support CIHEUL. Saya sedang meninjau kendala Anda dan siap membantu menyelesaikan masalah ini hingga tuntas. Bisa jelaskan lebih lanjut detail yang Anda alami?"
            follow_ups = ["Minta detail tangkapan layar jika relevan", "Update status tiket ke Aktif"]

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
