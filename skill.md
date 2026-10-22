# skill.md - Project Skills Matrix & Competency Profile

Dokumen ini mendefinisikan katalog keterampilan (*agent skills & engineering capabilities*) yang aktif dan diterapkan dalam siklus pengembangan **Aplikasi Helpdesk Multi-Platform (CIHEUL TECHNOLOGIES)**.

---

## 🎯 1. Pemetaan 12 Skill Utama dalam Arsitektur Kerja

| Skill | Sumber Terkemuka | Implementasi Konkret pada Proyek Helpdesk |
| :--- | :--- | :--- |
| **1. caveman** | `JuliusBrussee/caveman` | Menjaga efisiensi token dan komunikasi ringkas padat; memprioritaskan kode dan instruksi teknis yang 100% presisi tanpa basa-basi dekoratif. |
| **2. TDD (Test-Driven)** | `obra/superpowers` | Menjamin stabilitas backend: membuat tes endpoint API, model tiket, dan perutean WebSocket sebelum menulis implementasi akhir. |
| **3. ui ux pro max** | `nextlevelbuilder/ui-ux-pro-max-skill` | Menentukan sistem desain korporat: palet warna Slate/Obsidian, rasio kontras WCAG AA, font pairing modern, dan struktur layout kanban yang ergonomis. |
| **4. impeccable** | `pbakaus/impeccable` | Mengeliminasi *AI slop*: tidak ada padding acak, margin tidak konsisten, atau hierarki font yang kacau. Memberikan detail visual yang tajam. |
| **5. grill with docs** | `mattpocock/skills` | Memvalidasi seluruh asumsi arsitektur di awal; mendokumentasikan spesifikasi di `prd.md`, `Architecture.md`, dan BPMN sebelum implementasi. |
| **6. superpowers** | `obra/superpowers` | Menjalankan protokol rekayasa software tingkat lanjut: *Brainstorming* $\rightarrow$ *TDD* $\rightarrow$ *Systematic Debugging* saat menemukan anomali. |
| **7. gstack** | `garrytan/gstack` | Siklus kerja bertahap ala tim startup elit: Office-Hours (analisis bisnis), Plan, Build, Code Review, QA Playwright, dan Shipping. |
| **8. ponytail** | `DietrichGebert/ponytail` | Prinsip minimalis senior developer: hindari library JavaScript yang berlebihan untuk widget chat. Gunakan Vanilla JS murni yang ringan dan handal. |
| **9. i-have-adhd** | `ayghri/i-have-adhd` | Panduan eksekusi yang *action-oriented*: setiap respons diawali dengan langkah berikutnya yang konkret dan nomor urut terstruktur. |
| **10. taste skill** | `Leonxlnx/taste-skill` | Menghadirkan sentuhan visual berkelas pada dashboard CS dan widget chat: border halus 1px, transisi CSS lembut, dan micro-interaction natural. |
| **11. agent-browser** | `vercel-labs/agent-browser` | Validasi browser otomatis: inspeksi DOM widget dan dashboard web untuk memastikan tidak ada error JavaScript di console. |
| **12. find-skills** | `vercel-labs/skills` / `skills.sh` | Kemampuan meta untuk mendeteksi kebutuhan dependensi baru secara modular dan terukur. |

---

## 🛠️ 2. Standar Kompetensi Teknis Per Komponen

### A. Real-Time Distributed Communication Skill
- **Keahlian:** Merancang WebSocket Hub dengan Python FastAPI.
- **Standar:**
  - Koneksi aman (*authenticated connection via ticket session*).
  - Mekanisme Heartbeat ping/pong untuk deteksi koneksi putus (*zombie connection prevention*).
  - Sinkronisasi antrean pesan tertinggal saat client kembali terhubung (*offline-to-online catchup*).

### B. Anti-Slop Frontend & Widget Engineering Skill
- **Keahlian:** Pembuatan widget embed mandiri (*Zero-Dependency Embed Script*).
- **Standar:**
  - Total ukuran script di bawah 40 KB.
  - Isolasi CSS ketat agar tidak bentrok dengan CSS halaman web penampung (*host website*).
  - Menghilangkan elemen klise seperti titik hijau berkedip (`animate-pulse`); menggantinya dengan badge status profesional.

### C. AI Bot Triage & State Machine Skill
- **Keahlian:** Merancang alur transisi bot ke manusia (*Escalation Pattern*).
- **Standar:**
  - Klasifikasi intent pertanyaan pelanggan secara deterministik berbasis FAQ Knowledge Base.
  - Perhitungan skor relevansi jawaban.
  - *Graceful fallback* ke antrean agen manusia ketika skor rendah atau pelanggan meminta bantuan agen secara eksplisit.

### D. Mobile Cross-Platform (Flutter) Skill
- **Keahlian:** Aplikasi agen CS portabel dengan arsitektur bersih.
- **Standar:**
  - Manajemen state reaktif untuk daftar tiket dan ruang obrolan.
  - Audio/Visual alert saat tiket eskalasi baru diterima.
  - Integrasi CI/CD GitHub Actions untuk otomatisasi kompilasi APK release.
