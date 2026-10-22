import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def generate_wbs_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "WBS Helpdesk System"
    ws.views.sheetView[0].showGridLines = True

    # Palette
    NAVY_DARK = "0F172A"       # Primary Title Fill
    BLUE_HEADER = "1E293B"     # Table Header Fill
    SLATE_SECTION = "E2E8F0"   # Module Section Header
    ZEBRA_LIGHT = "F8FAFC"     # Alternating Row Fill
    WHITE = "FFFFFF"
    BORDER_COLOR = "CBD5E1"

    # Fonts
    font_main_title = Font(name="Segoe UI", size=15, bold=True, color=WHITE)
    font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="CBD5E1")
    font_header = Font(name="Segoe UI", size=10, bold=True, color=WHITE)
    font_section = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
    font_body = Font(name="Segoe UI", size=9.5, color="1E293B")
    font_bold_body = Font(name="Segoe UI", size=9.5, bold=True, color="1E293B")

    # Fills
    fill_main_title = PatternFill(start_color=NAVY_DARK, end_color=NAVY_DARK, fill_type="solid")
    fill_header = PatternFill(start_color=BLUE_HEADER, end_color=BLUE_HEADER, fill_type="solid")
    fill_section = PatternFill(start_color=SLATE_SECTION, end_color=SLATE_SECTION, fill_type="solid")
    fill_zebra = PatternFill(start_color=ZEBRA_LIGHT, end_color=ZEBRA_LIGHT, fill_type="solid")

    # Borders
    thin_border = Border(
        left=Side(style="thin", color=BORDER_COLOR),
        right=Side(style="thin", color=BORDER_COLOR),
        top=Side(style="thin", color=BORDER_COLOR),
        bottom=Side(style="thin", color=BORDER_COLOR)
    )
    thick_bottom = Border(
        left=Side(style="thin", color=BORDER_COLOR),
        right=Side(style="thin", color=BORDER_COLOR),
        top=Side(style="thin", color=BORDER_COLOR),
        bottom=Side(style="medium", color=NAVY_DARK)
    )

    # Alignments
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center")

    # 1. Title Block
    ws.merge_cells("A1:J1")
    ws["A1"] = "CIHEUL TECHNOLOGIES - TAKE HOME PROGRAMMING TEST (SOFTWARE ENGINEER)"
    ws["A1"].font = font_main_title
    ws["A1"].fill = fill_main_title
    ws["A1"].alignment = align_center

    ws.merge_cells("A2:J2")
    ws["A2"] = "WORK BREAKDOWN STRUCTURE (WBS) - OMNICHANNEL HELPDESK & REALTIME SUPPORT SYSTEM"
    ws["A2"].font = Font(name="Segoe UI", size=11, bold=True, color="38BDF8")
    ws["A2"].fill = fill_main_title
    ws["A2"].alignment = align_center

    ws.merge_cells("A3:J3")
    ws["A3"] = "Arsitektur: Monorepo | Backend: Python FastAPI | Frontend: Vanilla JS Widget & Tailwind Web Dashboard | Mobile: Flutter"
    ws["A3"].font = font_subtitle
    ws["A3"].fill = fill_main_title
    ws["A3"].alignment = align_center

    ws.row_dimensions[1].height = 28
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[3].height = 18
    ws.row_dimensions[4].height = 10  # blank space

    # 2. Table Headers
    headers = [
        ("WBS ID", 10),
        ("Modul / Komponen", 22),
        ("Fitur / Work Package", 28),
        ("Rincian Task & Deliverables Teknis", 38),
        ("User Role", 16),
        ("Tech Stack", 20),
        ("Durasi (Hari)", 12),
        ("Bobot (%)", 10),
        ("Prioritas", 12),
        ("Kriteria Verifikasi (Definition of Done)", 34)
    ]

    header_row = 5
    ws.row_dimensions[header_row].height = 26
    for col_idx, (header_text, width) in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=header_text)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = thin_border
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = width

    # 3. WBS Data Items
    # Tuple: (is_section, wbs_id, modul, fitur, task, role, tech, durasi, bobot, prioritas, dod)
    items = [
        # 1.0 Analisis & Desain Sistem
        (True, "1.0", "Analisis & Desain", "Spesifikasi & Blueprint Sistem", "Analisis kebutuhan teknis dan proses bisnis helpdesk omnichannel", "Semua Role", "Markdown, Draw.io", 2.0, 8.0, "Critical", "Dokumen terverifikasi"),
        (False, "1.1", "Analisis & Desain", "BPMN Swimlane Diagram", "Pemodelan proses bisnis 4 swimlanes (Customer, AI Bot, CS Agent, Supervisor)", "Lead Architect", "Draw.io / XML", 1.0, 4.0, "Critical", "File .drawio dan export PDF siap pakai"),
        (False, "1.2", "Analisis & Desain", "WBS & System Design", "Penyusunan rincian WBS modular dan dokumen arsitektur database (ERD) & API contract", "Tech Lead", "Excel / Markdown", 1.0, 4.0, "Critical", "File .xlsx terformat rapi dan Architecture.md"),

        # 2.0 Backend Core & Database Engine
        (True, "2.0", "Backend Service", "Core API & Database Engine", "Fondasi RESTful API, database schema, otentikasi JWT dan manajemen tiket", "CS, Admin", "Python FastAPI", 3.0, 15.0, "Critical", "Backend running, API docs /docs aktif"),
        (False, "2.1", "Backend Service", "Database Schema & ORM", "Modeling tabel Users, Customers, Tickets, Messages, KnowledgeBase dengan relasi ForeignKey", "Backend Eng", "SQLite / SQLAlchemy", 1.0, 5.0, "Critical", "Migrasi schema sukses, relasi cascade teruji"),
        (False, "2.2", "Backend Service", "Auth & RBAC Service", "Autentikasi agen CS dan Admin berbasis JWT Token, password hash bcrypt", "Admin, CS Agent", "FastAPI Security, JWT", 1.0, 5.0, "High", "Endpoint login, refresh token, validasi role"),
        (False, "2.3", "Backend Service", "Ticket Management CRUD", "API pembuatan tiket baru, update status (OPEN, IN_PROGRESS, RESOLVED), filter kategori", "CS Agent, Customer", "FastAPI, Pydantic", 1.0, 5.0, "Critical", "CRUD tiket berfungsi dengan response DTO tervalidasi"),

        # 3.0 Real-time WebSocket Hub (Always-Connected)
        (True, "3.0", "Real-time Hub", "WebSocket Infrastructure", "Jalur komunikasi real-time 3-arah: Live Chat Widget <-> Web Dashboard <-> Mobile Flutter", "Customer, CS", "FastAPI WebSockets", 3.0, 16.0, "Critical", "Pesan tersinkronisasi instan <100ms"),
        (False, "3.1", "Real-time Hub", "Connection Manager & Rooms", "Manajemen pool koneksi aktif, perutean broadcast pesan berdasarkan ticket_id session", "Backend Eng", "Python asyncio", 1.0, 6.0, "Critical", "Multi-client join room tanpa memory leak"),
        (False, "3.2", "Real-time Hub", "Always-Connected & Heartbeat", "Mekanisme ping-pong 15s deteksi zombie socket, exponential backoff reconnect", "Backend & Frontend", "WebSocket Protocol", 1.0, 5.0, "Critical", "Koneksi otomatis pulih saat jaringan putus-nyambung"),
        (False, "3.3", "Real-time Hub", "Offline Message Catch-up", "Sinkronisasi pesan tertinggal dengan parameter last_received_message_id saat reconnect", "Backend Eng", "SQLAlchemy + WS", 1.0, 5.0, "High", "Tidak ada pesan yang hilang saat client offline"),

        # 4.0 AI Bot Assistant & Escalation Engine
        (True, "4.0", "AI Bot Engine", "Auto-Reply & Handoff Triage", "Penanganan otomatis keluhan awal pelanggan dan eskalasi mulus ke CS manusia", "Customer, AI Bot", "Python, NLP / LLM API", 2.5, 13.0, "High", "Bot menjawab akurat dan eskalasi otomatis"),
        (False, "4.1", "AI Bot Engine", "Knowledge Base Matching", "Pencocokan pertanyaan keluhan dengan FAQ Knowledge Base menggunakan similarity scoring", "AI Bot", "Python, TF-IDF / Gemini", 1.0, 5.0, "High", "Rekomendasi jawaban bot relevan (score >= 0.75)"),
        (False, "4.2", "AI Bot Engine", "Confidence Triage & Fallback", "Deteksi jawaban tidak meyakinkan atau sentimen komplain untuk memicu eskalasi", "AI Bot", "State Machine Logic", 0.5, 3.0, "High", "Status tiket berganti WAITING_AGENT secara otomatis"),
        (False, "4.3", "AI Bot Engine", "Human Handoff Workflow", "Broadcast event ticket_escalated ke Web/Mobile CS dan nonaktifkan bot saat di-claim", "CS Agent, Bot", "WebSocket Hub", 1.0, 5.0, "Critical", "Transisi dari bot ke CS mulus tanpa duplikasi chat"),

        # 5.0 Live Chat Widget (JavaScript)
        (True, "5.0", "Live Chat Widget", "Embeddable Client Script", "Widget chat melayang di kanan bawah website (ala Intercom) dengan Vanilla JS murni", "Customer", "Vanilla JS, Scoped CSS", 2.5, 12.0, "Critical", "Widget tampil responsif, bundle < 40 KB"),
        (False, "5.1", "Live Chat Widget", "Floating Launcher & Modal", "Tombol trigger mengambang (FAB) dan popup window chat responsif tanpa merusak CSS host", "Frontend Eng", "HTML5, Scoped CSS", 1.0, 4.0, "Critical", "UI responsif di mobile & desktop, bebas conflict"),
        (False, "5.2", "Live Chat Widget", "WebSocket Client & UI Feed", "Koneksi WebSocket client, auto-reconnect, pengiriman pesan, bubbles chat, typing indicator", "Frontend Eng", "Native WebSocket API", 1.0, 5.0, "Critical", "Pesan masuk real-time, status terkirim jelas"),
        (False, "5.3", "Live Chat Widget", "Interactive Action Buttons", "Tombol eskalasi 'Hubungi CS Manusia', feedback rating kepuasan setelah masalah selesai", "Frontend Eng", "Vanilla JS Events", 0.5, 3.0, "High", "User dapat memicu eskalasi langsung lewat klik"),

        # 6.0 Web App CS & Admin Dashboard
        (True, "6.0", "Web Dashboard", "CS Workspace & Admin Panel", "Aplikasi web internal untuk agen CS melayani chat dan admin memantau metrik performa", "CS Agent, Admin", "HTML5, Tailwind CSS, JS", 3.0, 14.0, "Critical", "Dashboard dark mode elegan, realtime feed"),
        (False, "6.1", "Web Dashboard", "Dark Mode UI (Anti-Slop)", "Desain bertema Obsidian/Slate berkelas, kontras WCAG AA, bebas indikator klise", "UI/UX & Frontend", "Tailwind CSS", 1.0, 4.0, "High", "Tampilan modern, tanpa green pulse klise"),
        (False, "6.2", "Web Dashboard", "Real-time Ticket Kanban", "Board tiket aktif dengan badge status (BOT, WAITING, ACTIVE, RESOLVED), claim button", "Frontend Eng", "Modular JS, WS", 1.0, 5.0, "Critical", "Tiket baru muncul seketika tanpa refresh browser"),
        (False, "6.3", "Web Dashboard", "Interactive 1-on-1 Chat Room", "Panel percakapan langsung dengan customer, informasi identitas user, ganti status tiket", "Frontend Eng", "WebSocket Client", 1.0, 5.0, "Critical", "CS dapat membalas chat real-time dan resolve tiket"),

        # 7.0 Mobile App CS (Flutter)
        (True, "7.0", "Mobile App (CS)", "Flutter Android Client", "Aplikasi mobile resmi agen CS untuk melayani tiket kendala di mana saja", "CS Agent", "Flutter (Dart)", 3.0, 12.0, "Critical", "Aplikasi Flutter jalan lancar, siap build APK"),
        (False, "7.1", "Mobile App (CS)", "Architecture & State Setup", "Scaffolding project Flutter, routing, state management untuk list tiket dan chat room", "Mobile Eng", "Flutter, Provider/Riverpod", 1.0, 4.0, "Critical", "Clean architecture, reactive state management"),
        (False, "7.2", "Mobile App (CS)", "Real-time WebSocket Client", "Implementasi client WebSocket di Flutter dengan background awareness & auto-reconnect", "Mobile Eng", "web_socket_channel", 1.0, 4.0, "Critical", "Pesan sync real-time antara Mobile dan Web"),
        (False, "7.3", "Mobile App (CS)", "In-App Notifications & Resolution", "Pemberitahuan tiket eskalasi baru dengan audio/banner alert dan tombol quick reply", "Mobile Eng", "Flutter Widgets", 1.0, 4.0, "High", "Alert visual & sound berbunyi saat tiket masuk"),

        # 8.0 QA, Security Audit & Automated Release (CI/CD)
        (True, "8.0", "QA & Release", "Verification & Delivery", "Pengujian menyeluruh, audit keamanan kode, dan otomasi build APK via GitHub Actions", "QA, DevOps", "Pytest, GitHub Actions", 2.0, 10.0, "Critical", "Test lulus 100%, APK ter-compile otomatis"),
        (False, "8.1", "QA & Release", "Unit & Security Testing", "Test suite pytest (API, WebSocket, AI deflection), sanitasi XSS pada input chat widget", "QA Eng", "Pytest, TestClient", 1.0, 4.0, "Critical", "Zero vulnerabilities, seluruh unit test hijau"),
        (False, "8.2", "QA & Release", "GitHub Actions CI (Build APK)", "Workflow CI/CD untuk otomatis compile Flutter release APK pada commit/tag repository", "DevOps Eng", "GitHub Actions YAML", 0.5, 3.0, "Critical", "APK file artifact terbuat otomatis di GitHub"),
        (False, "8.3", "QA & Release", "Documentation & Verification", "Penyusunan README lengkap, panduan run lokal 1-command, verifikasi link submission", "Tech Lead", "Markdown, Git", 0.5, 3.0, "Critical", "Seluruh deliverable take-home test siap kirim")
    ]

    current_row = header_row + 1
    for item in items:
        is_section, wbs_id, modul, fitur, task, role, tech, durasi, bobot, prioritas, dod = item
        ws.row_dimensions[current_row].height = 22 if is_section else 20

        vals = [wbs_id, modul, fitur, task, role, tech, durasi, bobot, prioritas, dod]
        for col_idx, val in enumerate(vals, start=1):
            cell = ws.cell(row=current_row, column=col_idx, value=val)
            cell.border = thin_border

            if is_section:
                cell.fill = fill_section
                cell.font = font_section
            else:
                cell.font = font_body
                if (current_row % 2 == 0):
                    cell.fill = fill_zebra

            # Alignments & formatting
            if col_idx in [1, 5, 6, 9]:
                cell.alignment = align_center
            elif col_idx == 7:  # Durasi
                cell.alignment = align_right
                cell.number_format = "0.0"
            elif col_idx == 8:  # Bobot
                cell.alignment = align_right
                cell.number_format = '0.0"%"'
            else:
                cell.alignment = align_left

        current_row += 1

    # 4. Total Summary Row
    summary_row = current_row
    ws.row_dimensions[summary_row].height = 24
    ws.merge_cells(f"A{summary_row}:F{summary_row}")
    summary_label = ws.cell(row=summary_row, column=1, value="TOTAL ESTIMASI PROYEK (HARI KERJA & BOBOT)")
    summary_label.font = font_bold_body
    summary_label.fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")
    summary_label.alignment = align_right

    for c in range(1, 7):
        ws.cell(row=summary_row, column=c).border = thick_bottom

    # Duration formula (summing sub-tasks only: IDs with dot like 1.1, 1.2)
    # Total work days calculation: 21 days
    cell_dur = ws.cell(row=summary_row, column=7, value="=SUM(G6:G34)/2")
    cell_dur.font = font_bold_body
    cell_dur.fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")
    cell_dur.alignment = align_right
    cell_dur.number_format = "0.0"
    cell_dur.border = thick_bottom

    # Weight formula (equals 100%)
    cell_bobot = ws.cell(row=summary_row, column=8, value="100.0%")
    cell_bobot.font = font_bold_body
    cell_bobot.fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")
    cell_bobot.alignment = align_right
    cell_bobot.border = thick_bottom

    ws.merge_cells(f"I{summary_row}:J{summary_row}")
    sum_stat = ws.cell(row=summary_row, column=9, value="Status: Siap Eksekusi (Ready)")
    sum_stat.font = font_bold_body
    sum_stat.fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")
    sum_stat.alignment = align_center
    ws.cell(row=summary_row, column=10).border = thick_bottom
    sum_stat.border = thick_bottom

    output_path = r"C:\Users\Dell 3490\.gemini\antigravity\scratch\ciheul-helpdesk\docs\wbs\wbs_helpdesk_system.xlsx"
    wb.save(output_path)
    print(f"WBS spreadsheet successfully generated at: {output_path}")

if __name__ == "__main__":
    generate_wbs_excel()
