import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.core.security import hash_password

def init_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    from app.core.config import settings

    # Validate non-empty passwords before seeding
    if not settings.ADMIN_PASSWORD or not settings.ADMIN_PASSWORD.strip():
        raise RuntimeError("Refusing to seed database: ADMIN_PASSWORD is empty or whitespace.")
    if not settings.CS_PASSWORD or not settings.CS_PASSWORD.strip():
        raise RuntimeError("Refusing to seed database: CS_PASSWORD is empty or whitespace.")

    # 1. Seed Users (using environment settings or configurable values)
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not admin:
        admin = User(
            email=settings.ADMIN_EMAIL,
            full_name="Administrator CIHEUL",
            role="ADMIN",
            password_hash=hash_password(settings.ADMIN_PASSWORD)
        )
        db.add(admin)
    elif "$" not in admin.password_hash:
        # Upgrade legacy un-salted hash to new secure per-user cryptographic salt
        admin.password_hash = hash_password(settings.ADMIN_PASSWORD)

    cs_agent = db.query(User).filter(User.email == settings.CS_EMAIL).first()
    if not cs_agent:
        cs_agent = User(
            email=settings.CS_EMAIL,
            full_name="Budi Pratama (CS Support)",
            role="CS_AGENT",
            password_hash=hash_password(settings.CS_PASSWORD)
        )
        db.add(cs_agent)
    elif "$" not in cs_agent.password_hash:
        # Upgrade legacy un-salted hash to new secure per-user cryptographic salt
        cs_agent.password_hash = hash_password(settings.CS_PASSWORD)

    # 2. Seed Knowledge Base FAQs
    faqs = [
        {
            "question": "Bagaimana cara reset password akun saya?",
            "answer": "Untuk mereset password akun, silakan klik tautan 'Lupa Password' di halaman login, masukkan email Anda, lalu ikuti petunjuk verifikasi yang dikirimkan ke email.",
            "category": "ACCOUNT",
            "keywords": "reset lupa password kata sandi akun login"
        },
        {
            "question": "Metode pembayaran apa saja yang didukung?",
            "answer": "Kami menerima pembayaran melalui Transfer Virtual Account (BCA, Mandiri, BRI, BNI), QRIS, E-Wallet (GoPay, OVO), dan Kartu Kredit Visa/Mastercard.",
            "category": "BILLING",
            "keywords": "bayar pembayaran payment qris transfer invoice tagihan biaya"
        },
        {
            "question": "Mengapa aplikasi mobile loading terus atau error?",
            "answer": "Silakan pastikan koneksi internet stabil. Anda dapat mencoba menghapus cache aplikasi melalui menu Pengaturan HP -> Aplikasi -> Hapus Cache, atau restart aplikasi.",
            "category": "TECHNICAL",
            "keywords": "aplikasi mobile loading lambat error crash tidak bisa dibuka kendala jaringan"
        },
        {
            "question": "Berapa jam operasional Customer Support?",
            "answer": "Customer Support manusia kami beroperasi setiap hari Senin - Minggu pukul 08.00 - 21.00 WIB. Di luar jam tersebut, Asisten AI kami siaga 24 jam penuh.",
            "category": "GENERAL",
            "keywords": "jam buka waktu operasional cs layanan kontak jadwal hari"
        }
    ]

    for faq in faqs:
        exists = db.query(KnowledgeBase).filter(KnowledgeBase.question == faq["question"]).first()
        if not exists:
            kb_item = KnowledgeBase(
                question=faq["question"],
                answer=faq["answer"],
                category=faq["category"],
                keywords=faq["keywords"],
                is_active=True
            )
            db.add(kb_item)

    db.commit()
    db.close()
    print("Database initialized & seeded successfully.")

if __name__ == "__main__":
    init_database()
