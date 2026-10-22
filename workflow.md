# workflow.md - 10 Langkah Pengembangan Aplikasi

Dokumen ini memetakan implementasi konkret dari **10 Langkah Pengembangan Aplikasi** untuk menyelesaikan Take Home Test Software Engineer CIHEUL TECHNOLOGIES secara sistematis dan terverifikasi.

---

## 📋 Matriks 10 Langkah Eksekusi

```text
[1. PRD Lengkap] ──────────► [2. UI/UX Design Brief] ────► [3. Audit Keamanan]
       │                                                          │
       ▼                                                          ▼
[4. TDD & Systematic Debug] ◄── [5. E2E Test Playwright] ◄───────┘
       │
       ▼
[6. Clean & Refactor Dead Code] ──► [7. Git Commit Rapi] ─► [8. Task to Skill]
       │                                                          │
       ▼                                                          ▼
[9. Optimasi Performa] ──────────────────────────────────────────► [10. Docs & Deploy]
```

---

### Langkah 1: Tulis PRD Lengkap
- **Status:** **SELESAI (DONE)**
- **Dokumen:** [`prd.md`](file:///C:/Users/Dell%203490/.gemini/antigravity/scratch/ciheul-helpdesk/prd.md)
- **Cakupan:** Tujuan proyek, peran aktor (Pelanggan, CS, Admin, AI Bot), kebutuhan fungsional (Widget, Web Dashboard, Mobile Flutter, Realtime Hub, AI Handoff), user flow, dan kriteria keberhasilan.

### Langkah 2: Full UI & UX Design Brief
- **Status:** **SELESAI (TERINTEGRASI DI ARCHITECTURE & AGENTS.MD)**
- **Sistem Desain:**
  - **Palet Warna:** Obsidian & Slate 900 (`#0f172a`, `#020617`), border halus `#1e293b`, aksen aksi `#3b82f6` (Indigo/Blue).
  - **Prinsip Anti-Slop:** Tidak menggunakan titik hijau berkedip (`animate-pulse`); menggunakan badge tipografi presisi (`ONLINE`, `WAITING`, `ACTIVE`).
  - **Aksesibilitas:** Rasio kontras teks minimum 4.5:1 (WCAG AA).
  - **Responsivitas:** Tata letak kanban tiket untuk layar desktop/tablet; layout satu kolom yang nyaman untuk mobile Flutter.

### Langkah 3: Temukan Celah Keamanan (Security Audit)
- **Proteksi SQL Injection:** Wajib menggunakan query berparameter lewat SQLAlchemy ORM. Dilarang konkatenasi string SQL mentah.
- **Proteksi Cross-Site Scripting (XSS):** Semua pesan yang diketik pengguna di Live Chat Widget disanitasi sebelum dimasukkan ke DOM tree.
- **Proteksi WebSocket Hijacking:** Koneksi WebSocket divalidasi dengan `session_token` untuk customer atau JWT token untuk CS Agent.
- **CORS Policy:** Dibatasi secara eksplisit pada domain yang diizinkan untuk API backend.

### Langkah 4: TDD & Debug Error dengan Cepat (Systematic Debugging)
- **Protokol:** Menulis test suite sebelum kode implementasi selesai (*Red-Green-Refactor*).
- **Penanganan Error:** Analisis pesan error secara runtut berbasis akar masalah (*root cause*), dilarang melakukan spekulasi perbaikan acak (*no speculative fixes*).

### Langkah 5: E2E Test Aplikasimu (Playwright / Integration Test)
- **Skenario Otomatis:**
  1. Pelanggan membuka website demo yang memuat Chat Widget.
  2. Pelanggan mengirimkan pesan keluhan teknis.
  3. AI Bot membalas otomatis dengan artikel FAQ.
  4. Pelanggan menekan tombol "Hubungi CS Manusia".
  5. Status tiket berubah menjadi `WAITING_AGENT`.
  6. CS di Web Dashboard menerima notifikasi real-time dan mengklaim tiket.
  7. Komunikasi dua arah CS $\leftrightarrow$ Pelanggan berjalan lancar.

### Langkah 6: Bersihkan & Refactor Dead Code
- Melakukan pengecekan kode yang tidak digunakan (*unused imports, dead variables, deprecated functions*).
- Menjaga modul tetap ramping sesuai filosofi `DietrichGebert/ponytail` (*minimalist senior developer*).

### Langkah 7: Tulis Git Commit yang Rapi
- Menggunakan standar **Conventional Commits**:
  - `feat`: Penambahan fitur baru (Widget, Backend API, WebSocket, Mobile UI).
  - `fix`: Perbaikan bug atau logic error.
  - `test`: Penambahan skenario unit test atau E2E test.
  - `docs`: Pembuatan dokumen analisis (BPMN, WBS, PRD, README).
  - `refactor`: Perapian struktur kode tanpa mengubah fungsi.

### Langkah 8: Ubah Task Jadi Skill
- Setiap modul yang dibuat dirangkum sebagai pola yang dapat digunakan kembali (*reusable skills*), didokumentasikan dalam [`skill.md`](file:///C:/Users/Dell%203490/.gemini/antigravity/scratch/ciheul-helpdesk/skill.md).

### Langkah 9: Optimalkan Performa Aplikasi
- **Frontend Widget:** Bundling murni Vanilla JavaScript dengan ukuran $< 40$ KB.
- **Backend WebSocket:** Penggunaan koneksi asinkronus (FastAPI ASGI) dengan latensi sub-100ms.
- **Database Indexing:** Indexing pada kolom pencarian utama (`ticket.status`, `ticket.customer_id`, `message.ticket_id`).

### Langkah 10: Buat Dokumentasi & Deploy
- **Dokumen Analisis:**
  - Soal 1a: Swimlane BPMN dalam format `.drawio` dan file konversi `.pdf`.
  - Soal 1b: Work Breakdown Structure (WBS) dalam spreadsheet `.xlsx` profesional.
- **Deployment & Delivery:**
  - File panduan `README.md` monorepo lengkap dengan petunjuk instalasi lokal dalam 1 baris perintah.
  - Skrip GitHub Actions `.github/workflows/build-apk.yml` untuk otomatisasi kompilasi APK Android release.
