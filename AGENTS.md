# AGENTS.md - Engineering & Vibe Coding Guidelines

Dokumen ini memuat standar teknis, aturan arsitektur, dan sintesis skill agen untuk pengembangan proyek **Multi-Platform Helpdesk System (CIHEUL TECHNOLOGIES Test)**.

---

## 🧭 1. Intisari 12 Skill Utama dalam Pengerjaan Proyek

Proyek ini mengadopsi filosofi terbaik dari ekosistem skill agen modern:

1. **`obra/superpowers` (Disiplin Rekayasa Perangkat Lunak):**
   - Wajib melalui fase *Brainstorming*, *TDD*, dan *Systematic Debugging*.
   - Tidak ada kode produksi tanpa rencana arsitektur dan skenario pengujian yang jelas.
2. **`garrytan/gstack` (Multi-Role Thinking):**
   - Berpikir bertahap: `/office-hours` (bedah masalah) $\rightarrow$ `/plan` (arsitektur) $\rightarrow$ `/build` (koding bersih) $\rightarrow$ `/review` (audit keamanan & kualitas) $\rightarrow$ `/qa` (uji coba) $\rightarrow$ `/ship`.
3. **`DietrichGebert/ponytail` (Minimalist Senior Developer - YAGNI):**
   - *"The best code is the code you never wrote."* Hindari over-engineering. Solusi paling sederhana, teruji, dan modular adalah yang terbaik.
4. **`nextlevelbuilder/ui-ux-pro-max-skill` (Design Intelligence):**
   - Gunakan palet warna yang terkurasi untuk software enterprise (Obsidian, Slate, Deep Charcoal dengan aksen Trust Blue/Indigo yang presisi).
5. **`pbakaus/impeccable` & `Leonxlnx/taste-skill` (Anti-Frontend-Slop):**
   - Dilarang membuat antarmuka generic yang terlihat seperti template murahan. Tipografi jelas, hirarki visual tegas, micro-interaction halus.
6. **`JuliusBrussee/caveman` & `ayghri/i-have-adhd` (Kepadatan Komunikasi & Fokus Aksi):**
   - Komunikasi to-the-point, utamakan langkah aksi berikutnya, minimalkan basa-basi token, dan pastikan kode yang dihasilkan 100% presisi.
7. **`mattpocock/skills` (Grill With Docs):**
   - Setiap keputusan arsitektur krusial dicatat dalam `Architecture.md` dan `workflow.md`.
8. **`vercel-labs/agent-browser` & Playwright (Automated Verification):**
   - Lakukan verifikasi end-to-end secara otomatis dan mandiri sebelum menyatakan task selesai.

---

## 🛑 2. Aturan Keras Desain UI & Anti-AI Slop

1. **DILARANG Titik Hijau Nyala-Mati (`animate-pulse`):**
   - JANGAN PERNAH menyematkan titik/lingkaran hijau berkedip (`bg-emerald-500 animate-pulse`) untuk status agen online/offline. Gunakan badge teks tipografi berkelas (`ONLINE` / `AWAY`), border aksen halus, atau ikon status profesional.
2. **Dukungan Dark Mode Berkualitas Tinggi:**
   - Gunakan palet Obsidian / Slate (`bg-slate-900`, `bg-slate-950`, border `border-slate-800`, text `text-slate-100`).
   - Kontras teks harus memenuhi standar aksesibilitas WCAG AA (rasio kontras $\ge 4.5:1$).
3. **Widget Chat Ringan & Terisolasi:**
   - Live Chat Widget wajib ditulis dengan Vanilla JavaScript murni tanpa runtime framework besar. CSS di-namespace ketat agar tidak bocor atau merusak CSS website induk.

---

## 🧪 3. Test-Driven Development (TDD) Protocol

1. **Hukum Siklus Red-Green-Refactor:**
   - **RED:** Tulis unit test atau integration test terlebih dahulu yang mendefinisikan ekspektasi perilaku sistem.
   - **GREEN:** Tulis kode implementasi minimal yang dibutuhkan agar pengujian lulus.
   - **REFACTOR:** Rapikan struktur kode, hilangkan duplikasi, dan optimalkan performa tanpa merusak pengujian yang sudah ada.
2. **Cakupan Pengujian:**
   - Backend API endpoints (HTTP 200/201/400/401/404).
   - WebSocket broadcast & direct messaging.
   - AI bot auto-escalation trigger logic.

---

## 🛡️ 4. Standar Keamanan & Coding Best Practices

1. **Database & Query:**
   - Wajib menggunakan SQLAlchemy ORM dengan parameterized queries. Larangan keras terhadap f-string raw SQL interpolation.
2. **Input Sanitization & XSS Defense:**
   - Setiap payload teks dari chat widget disanitasi menggunakan `DOMPurify` / text escaping sebelum disisipkan ke DOM chat history.
3. **Autentikasi & Otorisasi:**
   - CS/Admin wajib melalui otentikasi JWT Bearer token dengan algoritma `HS256`. Password di-hash menggunakan algoritma yang aman.
4. **Error Handling & Systematic Debugging:**
   - Dilarang membuat *silent fail* (`except: pass`). Log error secara eksplisit dan kembalikan response JSON yang terstruktur (`{"detail": "...", "code": "..."}`).

---

## 📦 5. Standar Commit Git (Conventional Commits)

Format commit harus deskriptif dan konsisten:
- `feat(backend): add websocket connection manager with auto-reconnect support`
- `feat(widget): implement floating launcher and chat modal in vanilla js`
- `feat(mobile): scaffold flutter app with live ticket feed and websocket client`
- `test(api): add unit tests for ticket escalation and ai auto-reply`
- `docs(bpmn): add swimlane process diagram and wbs spreadsheet`
