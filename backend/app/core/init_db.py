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

    # 2. Seed Comprehensive Knowledge Base FAQs
    faqs = [
        {
            "question": "Bagaimana cara reset password akun saya?",
            "answer": "Untuk mereset password akun, silakan klik tautan 'Lupa Password' di halaman login, masukkan email Anda, lalu ikuti petunjuk verifikasi yang dikirimkan ke email.",
            "category": "ACCOUNT",
            "keywords": "reset lupa password kata sandi akun login sandi"
        },
        {
            "question": "Bagaimana cara mendaftar akun baru di CIHEUL?",
            "answer": "Untuk membuat akun baru, klik tombol 'Daftar' di portal pelanggan, masukkan nama lengkap, email aktif, dan kata sandi minimal 8 karakter, lalu lakukan verifikasi email.",
            "category": "ACCOUNT",
            "keywords": "daftar registrasi register buat akun baru sign up pendaftaran baru"
        },
        {
            "question": "Bagaimana cara mengubah alamat email atau nomor telepon profil saya?",
            "answer": "Anda dapat memperbarui kontak melalui menu Profil Akun -> Pengaturan -> Edit Profil. Perubahan email memerlukan konfirmasi OTP ke email terdaftar demi keamanan.",
            "category": "ACCOUNT",
            "keywords": "ubah ganti edit email nomor telepon ganti no kontak profil data diri"
        },
        {
            "question": "Metode pembayaran apa saja yang didukung?",
            "answer": "Kami menerima pembayaran melalui Transfer Virtual Account (BCA, Mandiri, BRI, BNI), QRIS, E-Wallet (GoPay, OVO), dan Kartu Kredit Visa/Mastercard.",
            "category": "BILLING",
            "keywords": "bayar pembayaran payment qris transfer invoice tagihan biaya va bca mandiri bri bni gopay ovo"
        },
        {
            "question": "Bagaimana kebijakan pengembalian dana (refund) dan pembatalan transaksi?",
            "answer": "Pengajuan pengembalian dana dapat diproses maksimal 7 hari kerja setelah transaksi dengan melampirkan nomor invoice dan bukti transfer kepada Customer Support.",
            "category": "BILLING",
            "keywords": "refund pengembalian dana kembali batal pembatalan uang kembali retur klaim"
        },
        {
            "question": "Apakah ada promo, diskon, atau voucher untuk pelanggan baru?",
            "answer": "Informasi promo dan voucher diskon berlangganan dapat Anda cek langsung di halaman promo aplikasi atau melalui newsletter resmi CIHEUL.",
            "category": "BILLING",
            "keywords": "promo diskon voucher potongan harga penawaran kode kupon cashback hemat"
        },
        {
            "question": "Mengapa aplikasi mobile loading terus atau error?",
            "answer": "Silakan pastikan koneksi internet stabil. Anda dapat mencoba menghapus cache aplikasi melalui menu Pengaturan HP -> Aplikasi -> Hapus Cache, atau restart aplikasi.",
            "category": "TECHNICAL",
            "keywords": "aplikasi mobile loading lambat error crash tidak bisa dibuka kendala jaringan lag gangguan lemot"
        },
        {
            "question": "File dan dokumen apa saja yang bisa dilampirkan dalam chat bantuan?",
            "answer": "Sistem mendukung lampiran format gambar (PNG, JPG, JPEG) dan dokumen PDF hingga ukuran maksimal 10MB per berkas untuk mempermudah pengecekan bukti kendala.",
            "category": "TECHNICAL",
            "keywords": "lampiran file upload kirim gambar foto screenshot pdf dokumen bukti unggah"
        },
        {
            "question": "Apakah CIHEUL menyediakan API publik atau webhook integrasi?",
            "answer": "Ya, CIHEUL menyediakan RESTful API dan WebSocket untuk integrasi helpdesk dengan CRM pihak ketiga. Dokumentasi API interaktif tersedia di endpoint /docs (Swagger UI).",
            "category": "TECHNICAL",
            "keywords": "api webhook integrasi developer endpoint dokumentasi swagger rest sdk crm"
        },
        {
            "question": "Berapa jam operasional Customer Support?",
            "answer": "Customer Support manusia kami beroperasi setiap hari Senin - Minggu pukul 08.00 - 21.00 WIB. Di luar jam tersebut, Asisten AI kami siaga 24 jam penuh.",
            "category": "GENERAL",
            "keywords": "jam buka waktu operasional cs layanan kontak jadwal hari jam kerja tutup"
        },
        {
            "question": "Apa itu CIHEUL Technologies dan produk apa saja yang ditawarkan?",
            "answer": "PT CIHEUL Technologies adalah perusahaan penyedia solusi enterprise digital, mencakup platform Omnichannel Helpdesk modern, integrasi AI Support, dan software cloud bisnis.",
            "category": "GENERAL",
            "keywords": "ciheul tentang perusahaan profil produk teknologi software omnichannel layanan pt siapa apa itu"
        },
        {
            "question": "Bagaimana cara mengetahui status tiket laporan kendala saya?",
            "answer": "Anda dapat memantau status tiket langsung melalui widget live chat ini atau membuka link tiket yang dikirimkan ke email Anda. Riwayat chat tersinkronisasi realtime.",
            "category": "GENERAL",
            "keywords": "status tiket lacak tracking cek progress kendala nomor laporan id tindak lanjut"
        },
        {
            "question": "Apakah data dan transaksi saya dijamin aman?",
            "answer": "Seluruh data dilindungi enkripsi SSL/TLS HTTPS, sanitasi data pribadi sensitif (PII Masking), dan hashing password PBKDF2 HMAC-SHA256 berstandar perbankan.",
            "category": "GENERAL",
            "keywords": "aman keamanan enkripsi privasi pii data perlindungan ssl aman kah proteksi rahasia"
        },
        {
            "question": "Bagaimana cara menghubungi tim bisnis untuk kerja sama enterprise?",
            "answer": "Untuk kerja sama B2B dan enterprise, silakan kirimkan proposal atau pertanyaan Anda ke email partnership@ciheul.com atau jadwalkan pertemuan dengan konsultan kami.",
            "category": "GENERAL",
            "keywords": "partnership kerja sama bisnis enterprise b2b kontak sales marketing vendor kolaborasi"
        },
        {
            "question": "Kapan pertanyaan saya dijawab oleh Bot dan kapan oleh Agen manusia?",
            "answer": "Asisten AI CIHEUL menjawab pertanyaan umum dan panduan teknis secara instan 24/7. Anda dapat memilih berbicara dengan Customer Support manusia kapan saja dengan mengetik 'Hubungi CS'.",
            "category": "GENERAL",
            "keywords": "perbedaan bot agen manusia eskalasi sistem kerja otomatis bantuan langsung cs live agent"
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
