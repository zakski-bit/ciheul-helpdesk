# CIHEUL TECHNOLOGIES - Take Home Programming Test
## Omnichannel Helpdesk & Realtime Live Support System (Software Engineer)

Repositori ini memuat solusi lengkap untuk Take Home Test Software Engineer CIHEUL TECHNOLOGIES untuk **Opsi 1: Aplikasi Helpdesk**.

Sistem ini menghubungkan **3 platform utama secara real-time** (*Always-Connected WebSocket Hub*):
1. **Live Chat Widget** (Embeddable Vanilla JavaScript ala Intercom).
2. **Web App CS & Admin Dashboard** (Dark Mode modern Obsidian/Slate).
3. **Mobile App (Flutter)** untuk operasional Customer Support di mana saja.
4. **AI Bot Assistant Engine** (Penanganan FAQ otomatis, deteksi kebuntuan, dan *auto-escalation* ke CS manusia).

---

## Daftar Deliverables Soal

| Soal | Komponen | Lokasi File Deliverables | Keterangan |
| :--- | :--- | :--- | :--- |
| **Soal 1a** | Swimlane BPMN | [`docs/bpmn/helpdesk_process_swimlane.drawio`](file:///C:/Users/Dell%203490/.gemini/antigravity/scratch/ciheul-helpdesk/docs/bpmn/helpdesk_process_swimlane.drawio)<br/>[`docs/bpmn/PREVIEW_BPMN.html`](file:///C:/Users/Dell%203490/.gemini/antigravity/scratch/ciheul-helpdesk/docs/bpmn/PREVIEW_BPMN.html) | Diagram swimlane 4 role (Pelanggan, AI Bot, CS Agent, Supervisor). Buka di draw.io lalu export ke PDF. |
| **Soal 1b** | WBS Spreadsheet | [`docs/wbs/wbs_helpdesk_system.xlsx`](file:///C:/Users/Dell%203490/.gemini/antigravity/scratch/ciheul-helpdesk/docs/wbs/wbs_helpdesk_system.xlsx) | File Excel resmi berisi 8 modul, 24 fitur, durasi, bobot (100%), dan DoD. |
| **Soal 2** | Source Code Monorepo | `backend/`, `web-dashboard/`, `widget-js/`, `mobile-flutter/` | Monorepo modular lengkap dengan WebSocket 3-arah dan AI triage. |
| **Khusus APK**| Android Mobile APK | [`.github/workflows/build-apk.yml`](file:///C:/Users/Dell%203490/.gemini/antigravity/scratch/ciheul-helpdesk/.github/workflows/build-apk.yml) | Otomatisasi kompilasi APK release via GitHub Actions CI/CD atau compile lokal. |

---

## Panduan Menjalankan Sistem Secara Lokal

### 1. Jalankan Backend & Web Service (Python FastAPI)

Pastikan dependensi telah terpasang:
```bash
pip install -r backend/requirements.txt
```

Inisialisasi database SQLite dan seed user/FAQ:
```bash
python backend/app/core/init_db.py
```

Jalankan server:
```bash
python backend/main.py
```
> Server akan berjalan di: `http://localhost:8000`  
> Dokumentasi API interaktif Swagger: `http://localhost:8000/docs`

---

### 2. Akses Aplikasi & Simulasi

1. **Web Dashboard CS & Admin**:
   - Buka browser di: `http://localhost:8000/dashboard/index.html`
   - Kredensial Login CS:
     - **Email:** `cs@ciheul.com`
     - **Password:** `cs123`
   - Atau akun Admin: `admin@ciheul.com` / `admin123`.

2. **Simulasi Live Chat Widget (Pelanggan)**:
   - Buka tab baru di browser: `http://localhost:8000/widget/demo.html`
   - Klik tombol chat di kanan bawah.
   - Ketik pertanyaan FAQ (contoh: *"Bagaimana cara reset password?"* atau *"Metode pembayaran apa saja?"*) -> **AI Bot akan membalas otomatis**.
   - Ketik *"Saya mau bicara dengan CS manusia"* atau klik tombol **"Hubungi CS"** -> **Tiket otomatis dieskalasi ke Web Dashboard & Mobile App CS**.

---

### 3. Menjalankan Aplikasi Mobile (Flutter CS App)

Masuk ke folder `mobile-flutter`:
```bash
cd mobile-flutter
flutter run
```

Atau kompilasi file APK rilis:
```bash
flutter build apk --release
```
*File APK akan berada di: `mobile-flutter/build/app/outputs/flutter-apk/app-release.apk`.*

> [!NOTE]
> Jika Anda mengunggah repositori ini ke akun GitHub Anda, GitHub Actions akan secara otomatis meng-compile APK Android pada tab Actions tanpa perlu membebani laptop Anda.

---

## Pengujian Otomatis (TDD & Unit Testing)

Jalankan pengujian unit dan integrasi backend menggunakan Pytest:
```bash
pytest backend/tests/test_api.py -v
```
Hasil pengujian: **13 PASSED (100% Green)** mencakup:
- Keamanan Password Hashing dengan per-user random cryptographic salt (`salt$hash`)
- Autentikasi JWT dan Session Token
- Evaluasi AI Bot deflection & intent detection
- Alur lengkap tiket: pembuatan, claim, resolusi, dan rating kepuasan
- Otorisasi eskalasi tiket dan validasi kepemilikan pelanggan
- Validasi rentang rating (skala 1 s/d 5) pada tiket terselesaikan
- Role-Based Access Control (RBAC) mutasi Knowledge Base khusus Admin
- Pengamanan WebSocket (`/ws/agents` dan `/ws/ticket/{id}`) terhadap akses anonim dan sender spoofing
- Analisis Copilot Assistant AI dan follow-up actions

---

## Keamanan & Kualitas Rekayasa Produksi
- **Kriptografi Password:** Menggunakan algoritma PBKDF2 HMAC SHA-256 dengan 100.000 iterasi dan random cryptographic salt 16-byte (`os.urandom(16)`), disimpan dalam format `salt$hash` dengan verifikasi waktu konstan (`hmac.compare_digest`).
- **Otorisasi WebSocket & Anti-Spoofing:** Kanal `/ws/agents` dan `/ws/ticket/{id}` wajib menyertakan token otentikasi. Identitas pengirim ditetapkan absolut dari sesi server, mengabaikan manipulasi atribut identitas dari payload client.
- **Pencegahan SQL Injection:** Menggunakan SQLAlchemy ORM dengan parameterized queries.
- **Sanitasi XSS:** Input chat disanitasi sebelum dimasukkan ke DOM tree.
- **Always-Connected Resilience:** WebSocket Heartbeat (15s ping/pong) + auto-reconnect backoff (1s, 2s, 5s) + pemulihan pesan tertinggal saat koneksi pulih.
- **Anti-AI Slop:** Desain antarmuka Obsidian/Slate kontras tinggi tanpa titik hijau berkedip (`animate-pulse`).
