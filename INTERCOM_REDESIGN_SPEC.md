# Spesifikasi Desain & Rekayasa Ulang: Intercom Helpdesk & Copilot 2

Dokumen ini memetakan restrukturisasi antarmuka dan fitur sistem helpdesk agar mengikuti standar visual dan fungsional **Intercom Helpdesk & Fin AI**, dengan prinsip:
1. **Ultra Clean & Minimalist:** Menghilangkan seluruh ornamen berlebih, gradien norak, dan elemen dekoratif tidak perlu.
2. **ZERO Emoji:** Dilarang menggunakan emoji sama sekali (tidak ada robot, bintang, jempol, atau avatar kartun). Seluruh penanda menggunakan tipografi presisi, micro-copy berkelas, dan ikon SVG monokrom.
3. **Arsitektur 3-Kolom Modern (Inbox + Conversation + Copilot 2):**
   - Kolom 1: Navigasi & Daftar Percakapan (`Your inbox`)
   - Kolom 2: Ruang Obrolan Interaktif (`Conversation`) dengan tombol aksi minimalis (`Close`, `Details`, `⌘K`)
   - Kolom 3: **Copilot Panel** (AI Assistant untuk agen: `What happened`, `Draft reply`, `Send to Customer`, `Ask Copilot`)
4. **Widget Fin AI (Sisi Pelanggan):**
   - Header minimalis dengan ikon 9-dot grid khas Intercom Fin.
   - Bubble chat pelanggan: Solid Black (`#000000` / `#111827`) dengan teks putih tajam.
   - Bubble chat bot / agen: Neutral Gray (`#f3f4f6`) dengan teks gelap presisi.
   - Notifikasi sistem inline: `Fin assigned this conversation to [Agent Name] · 2m`.

---

## 1. Analisis Visual Berdasarkan Referensi Intercom

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ INTERCOM WORKSPACE (3-COLUMN LAYOUT)                                                        │
├────────────┬─────────────────────────────┬─────────────────────────────┬────────────────────┤
│ Icon Nav   │ Column 1: Your Inbox        │ Column 2: Active Chat       │ Column 3: Copilot  │
├────────────┼─────────────────────────────┼─────────────────────────────┼────────────────────┤
│ [Inbox]    │ 12 Open · Last activity     │ Customer Name   [Close]     │ Copilot            │
│ [Tickets]  │                             │                             │                    │
│ [Contacts] │ • Ravi Shankar              │ [Customer Message]          │ What happened      │
│ [Settings] │   "This is blocking..." 3m  │                             │ Summary of issue   │
│            │                             │ [Fin AI Response]           │                    │
│            │ • Sarah Garcia              │                             │ Draft reply        │
│            │   "Hola, me gustaria..." 7m │ Fin assigned to CS · 2m     │ [AI Draft Text]    │
│            │                             │                             │                    │
│            │                             ├─────────────────────────────┤ [Send to Customer] │
│            │                             │ Reply v                     │                    │
│            │                             │ [Use ⌘K for shortcuts...]   │ Ask Copilot...     │
└────────────┴─────────────────────────────┴─────────────────────────────┴────────────────────┘
```

---

## 2. Rincian Desain Per Komponen

### A. Live Chat Widget (Fin AI Messenger)
* **Warna & Geometri:**
  - Background window: `#ffffff` (Light) / `#0f172a` (Dark mode pilihan).
  - Header: Tinggi 56px, border bawah halus 1px `#e5e7eb`. Ikon 9-titik grid khas Fin + teks "Fin" font weight 600 (14px). Tombol `X` close minimalis di kanan.
  - Bubble Pelanggan: `background: #000000; color: #ffffff; border-radius: 18px 18px 4px 18px;` (Solid black bubble kontras tinggi).
  - Bubble Fin / Agen: `background: #f3f4f6; color: #111827; border-radius: 18px 18px 18px 4px;` (Soft neutral gray).
  - Status Inline: Teks abu-abu muted 11px di tengah: `Fin assigned this conversation to Juan Lorenz · 3m`.
  - Input Box: Placeholder `"Ask your question..."`, border halus 1px `#e5e7eb`, tanpa tombol warna-warni yang mencolok.

### B. Web Dashboard CS (Intercom Inbox)
* **Kolom Kiri (Navigasi Ikon Vertikal):**
  - Lebar 56px, background `#ffffff` border kanan `#e5e7eb`.
  - Ikon monokrom: Inbox, Tickets, Knowledge Base, Settings, Profil Avatar.
* **Kolom 1 (`Your inbox`):**
  - Header: Judul `"Your inbox"`, filter count `"12 Open"`, sort dropdown `"Last activity"`.
  - Item Percakapan: Avatar inisial minimalis dengan status dot abu-abu/hijau subtle, Nama Pelanggan (Font weight 600), Cuplikan pesan terakhir (1 baris truncate), waktu relatif (`3m`, `15m`, `1h`).
* **Kolom 2 (`Conversation View`):**
  - Header: Nama Pelanggan, tombol aksi elipsis `...`, tombol `Close` (black pill button khas Intercom), tombol `Details`.
  - Thread: Ruang percakapan yang bersih dengan padding lega, bubble obrolan bersudut rounded modern, delivery receipt `"Seen · 5m"`.
  - Composer Box:
    - Kontainer rounded-xl dengan border halus.
    - Header composer: Dropdown `"Reply"` / `"Note"` (internal team note).
    - Textarea: Placeholder `"Use ⌘K for shortcuts..."`.
    - Toolbar bawah: Ikon Lightning (Saved replies / macro), tombol `Send` di kanan bawah.
* **Kolom 3 (`Copilot 2 Assistant Panel`):**
  - Header: `"Copilot"` + tombol expand/collapse panel.
  - Sub-link: `"Read conversation, searched Knowledge Base >"`.
  - Card 1 — **What happened:**
    - AI merangkum inti masalah pelanggan secara otomatis tanpa agen perlu membaca seluruh chat panjang.
  - Card 2 — **Draft reply:**
    - AI otomatis menyusun draf balasan profesional untuk pelanggan berdasarkan FAQ dan riwayat kendala.
    - Tombol aksi utama: Blue pill button **`Send to [Customer Name]`**. Agen cukup klik 1 tombol untuk langsung membalas pelanggan!
  - Card 3 — **Follow ups / Suggested Actions:**
    - Rekomendasi aksi cepat (misal: "Tandai kategori Akun", "Eskalasi ke Level 2").
  - Footer input: `"Ask Copilot about this conversation..."` + arrow button untuk agen meminta saran tambahan ke Copilot.

### C. Mobile App CS (Flutter)
* Menyesuaikan dengan estetika Intercom Inbox mobile:
  - Header ringkas dengan tab filter Inbox.
  - Thread chat dengan bubble hitam (pelanggan) dan abu-abu (agen/bot).
  - Bottom sheet modal untuk **Copilot AI Summary & One-Tap Draft Reply**.
  - Bebas dari seluruh emoji.

---

## 3. Rencana Eksekusi Teknis

1. **Update API Backend (`/api/v1/copilot`):**
   - Menambahkan endpoint `POST /api/v1/copilot/summarize-and-draft` yang menganalisis percakapan aktif dan menghasilkan:
     - `summary`: Ringkasan 2 kalimat tentang apa yang dialami pelanggan.
     - `draft_reply`: Draf jawaban siap kirim untuk agen.
     - `suggested_actions`: Daftar 2 aksi lanjutan yang disarankan.
2. **Redesign Live Chat Widget (`widget-js/`):**
   - Menulis ulang CSS & markup widget dengan styling Fin Intercom (black/gray bubbles, 9-dot grid icon, input minimalis).
   - Menghapus seluruh emoji dan animasi norak.
3. **Redesign Web Dashboard (`web-dashboard/`):**
   - Membangun layout 3-kolom persis screenshot Intercom.
   - Mengimplementasikan panel **Copilot 2** di kolom kanan dengan fitur auto-summary dan tombol `Send to [Customer]`.
4. **Refactor Flutter Mobile App (`mobile-flutter/`):**
   - Mengubah palette ke Intercom style (Clean white/light mode atau sleek dark mode), typography sharp, tanpa emoji.
