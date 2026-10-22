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
| **Soal 1a** | Swimlane BPMN | [`docs/bpmn/helpdesk_process_swimlane.pdf`](./docs/bpmn/helpdesk_process_swimlane.pdf)<br/>[`docs/bpmn/helpdesk_process_swimlane.drawio`](./docs/bpmn/helpdesk_process_swimlane.drawio)<br/>[`docs/bpmn/PREVIEW_BPMN.html`](./docs/bpmn/PREVIEW_BPMN.html) | Dokumen PDF resmi vektor siap tinjau, file source draw.io, dan preview HTML interaktif 4 role (Pelanggan, AI Bot, CS Agent, Supervisor). |
| **Soal 1b** | WBS Spreadsheet | [`docs/wbs/wbs_helpdesk_system.xlsx`](./docs/wbs/wbs_helpdesk_system.xlsx) | File Excel resmi berisi 8 modul, 24 fitur, durasi, bobot (100%), dan DoD. |
| **Soal 2** | Source Code Monorepo | `backend/`, `web-dashboard/`, `widget-js/`, `mobile-flutter/` | Monorepo modular lengkap dengan WebSocket 3-arah dan AI triage. |
| **Khusus APK**| Android Mobile APK | [`.github/workflows/build-apk.yml`](./.github/workflows/build-apk.yml) | Otomatisasi kompilasi APK release via GitHub Actions CI/CD atau compile lokal. |

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

### 3. Menjalankan Aplikasi Mobile (Flutter CS App) & Distribusi APK

Masuk ke folder `mobile-flutter`:
```bash
cd mobile-flutter
flutter run
```

Atau kompilasi file APK rilis secara lokal:
```bash
flutter build apk --release
```
*File APK akan berada di: `mobile-flutter/build/app/outputs/flutter-apk/app-release.apk`.*

---

### 4. Panduan Submission Git Remote & Unduhan APK Release

1. **Menghubungkan ke Remote Git Penguji / Evaluator**:
   Repositori lokal ini telah terinisialisasi secara bersih dengan riwayat commit rapi. Untuk mengunggah ke GitHub atau GitLab Anda:
   ```bash
   git remote add origin https://github.com/<username>/ciheul-helpdesk.git
   git branch -M master
   git push -u origin master
   ```

2. **Otomasi Build & Rilis APK Permanen (GitHub Actions)**:
   - File workflow [`.github/workflows/build-apk.yml`](./.github/workflows/build-apk.yml) secara otomatis menjalankan kompilasi Java 17 + Flutter SDK di runner Linux cloud tanpa membebani laptop penguji.
   - APK hasil build disimpan sebagai build artifact (durasi retensi 90 hari) dan otomatis diunggah ke **GitHub Releases** permanen:  
     `https://github.com/<username>/ciheul-helpdesk/releases/latest/download/app-release.apk`
   - **Keamanan Keystore Signing:** Untuk rilis produksi sesungguhnya, konfigurasikan GitHub Secrets (`RELEASE_KEYSTORE_BASE64`, `KEY_ALIAS`, `KEY_PASSWORD`, `STORE_PASSWORD`). Fallback signing key di workflow hanya diperuntukkan sebagai validator verifikasi build di sandbox CI agar proses verifikasi otomatis tetap berjalan mulus.

---

## Pengujian Otomatis (TDD & Unit Testing)

Jalankan pengujian unit dan integrasi backend menggunakan Pytest:
```bash
pytest backend/tests/test_api.py -v
```
Hasil pengujian: **22 PASSED (100% Green)** mencakup:
- Keamanan Password Hashing dengan per-user random cryptographic salt (`salt$hash`)
- Autentikasi JWT dan Session Token
- Evaluasi AI Bot deflection & intent detection
- Alur lengkap tiket: pembuatan, claim, resolusi, dan rating kepuasan
- Otorisasi eskalasi tiket dan validasi kepemilikan pelanggan
- Validasi rentang rating (skala 1 s/d 5) pada tiket terselesaikan
- Role-Based Access Control (RBAC) mutasi Knowledge Base khusus Admin
- Pengamanan WebSocket (`/ws/agents` dan `/ws/ticket/{id}`) terhadap akses anonim dan sender spoofing
- Analisis Copilot Assistant AI dan follow-up actions
- In-band first-message authentication handshake pada WebSocket (zero credential token di query URL log)
- Batas ketat frame payload 64 KB UTF-8 dan pembatasan frekuensi event koneksi (rate limiting)
- Validasi batas panjang input pembuatan tiket (maksimal 3000 karakter)
- Penyamaran ID agen CS pada endpoint publik pelanggan
- Safeguard keamanan lingkungan production dan staging (larangan penggunaan default secret/password)
- Sanitasi PII (NIK, nomor rekening, kartu kredit, telepon, email, nama) sebelum evaluasi AI
- Draft fallback pembayaran yang akurat dan jujur (tanpa klaim palsu verifikasi gateway)

---

## Keamanan & Kualitas Rekayasa Produksi
- **Kriptografi Password:** Menggunakan algoritma PBKDF2 HMAC SHA-256 dengan 100.000 iterasi dan random cryptographic salt 16-byte (`os.urandom(16)`), disimpan dalam format `salt$hash` dengan verifikasi waktu konstan (`hmac.compare_digest`).
- **Otorisasi WebSocket & Anti-Spoofing:** Kanal `/ws/agents` dan `/ws/ticket/{id}` wajib menyertakan token otentikasi. Identitas pengirim ditetapkan absolut dari sesi server, mengabaikan manipulasi atribut identitas dari payload client.
- **Pencegahan SQL Injection:** Menggunakan SQLAlchemy ORM dengan parameterized queries.
- **Sanitasi XSS:** Input chat disanitasi sebelum dimasukkan ke DOM tree.
- **Always-Connected Resilience:** WebSocket Heartbeat (15s ping/pong) + auto-reconnect backoff (1s, 2s, 5s) + pemulihan pesan tertinggal saat koneksi pulih.
- **Anti-AI Slop:** Desain antarmuka Obsidian/Slate kontras tinggi tanpa titik hijau berkedip (`animate-pulse`).
