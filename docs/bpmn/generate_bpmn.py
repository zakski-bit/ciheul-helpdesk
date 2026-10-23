import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import subprocess

def create_clean_drawio_bpmn():
    """
    Generates a clean, crisp, professional white-theme BPMN Swimlane diagram
    formatted specifically for Draw.io (diagrams.net).
    """
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2026-10-23T03:00:00.000Z',
        'agent': 'Antigravity AI (Clean Corporate Architecture)',
        'version': '24.0.0',
        'type': 'device'
    })
    
    diagram = ET.SubElement(mxfile, 'diagram', {
        'id': 'ciheul-bpmn-helpdesk',
        'name': 'BPMN Swimlane - Omnichannel Helpdesk'
    })
    
    model = ET.SubElement(diagram, 'mxGraphModel', {
        'dx': '1600',
        'dy': '1000',
        'grid': '1',
        'gridSize': '10',
        'guides': '1',
        'tooltips': '1',
        'connect': '1',
        'arrows': '1',
        'fold': '1',
        'page': '1',
        'pageScale': '1',
        'pageWidth': '1850',
        'pageHeight': '1050',
        'background': '#ffffff',
        'math': '0',
        'shadow': '0'
    })
    
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', {'id': '0'})
    ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})
    
    # 1. Main Pool (Clean Corporate Header & Crisp Border)
    pool_style = (
        "swimlane;html=1;childLayout=stackLayout;resizeParent=1;resizeParentMax=0;"
        "startSize=40;horizontal=0;horizontalFlip=0;fillColor=#1e293b;strokeColor=#475569;"
        "strokeWidth=1.5;fontColor=#ffffff;fontStyle=1;fontSize=13;fontFamily=Segoe UI,Helvetica;"
    )
    pool = ET.SubElement(root, 'mxCell', {
        'id': 'pool_1',
        'value': 'PROSES BISNIS SISTEM HELPDESK & OMNICHANNEL LIVE SUPPORT (CIHEUL TECHNOLOGIES)',
        'style': pool_style,
        'vertex': '1',
        'parent': '1'
    })
    ET.SubElement(pool, 'mxGeometry', {
        'x': '40', 'y': '40', 'width': '1760', 'height': '920', 'as': 'geometry'
    })
    
    # 2. Swimlanes (4 Roles - Clean White / Slate Alternating Fills)
    lanes = [
        ('lane_customer', 'Pelanggan (Customer / End-User)', '#ffffff', '#0284c7', 210),
        ('lane_ai_bot', 'Sistem AI Helpdesk (Bot Assistant)', '#f8fafc', '#4f46e5', 210),
        ('lane_cs_agent', 'Customer Support (CS Agent - Web & Mobile)', '#ffffff', '#0284c7', 270),
        ('lane_supervisor', 'Supervisor / Technical Lead (L2 Escalation)', '#f8fafc', '#7c3aed', 190)
    ]
    
    lane_y = 0
    for lane_id, lane_name, lane_bg, accent_color, lane_h in lanes:
        lane_style = (
            f"swimlane;html=1;startSize=32;horizontal=0;fillColor={lane_bg};"
            f"strokeColor=#cbd5e1;strokeWidth=1;fontColor={accent_color};fontStyle=1;fontSize=11.5;"
            f"fontFamily=Segoe UI,Helvetica;"
        )
        lane = ET.SubElement(root, 'mxCell', {
            'id': lane_id,
            'value': lane_name,
            'style': lane_style,
            'vertex': '1',
            'parent': 'pool_1'
        })
        ET.SubElement(lane, 'mxGeometry', {
            'x': '40', 'y': str(lane_y), 'width': '1720', 'height': str(lane_h), 'as': 'geometry'
        })
        lane_y += lane_h

    def add_node(node_id, label, style, x, y, w, h, parent='1'):
        cell = ET.SubElement(root, 'mxCell', {
            'id': node_id,
            'value': label,
            'style': style,
            'vertex': '1',
            'parent': parent
        })
        ET.SubElement(cell, 'mxGeometry', {
            'x': str(x), 'y': str(y), 'width': str(w), 'height': str(h), 'as': 'geometry'
        })
        return cell

    def add_edge(edge_id, source_id, target_id, label='', waypoints=None):
        edge_style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
            "html=1;strokeColor=#475569;strokeWidth=1.8;fontColor=#0f172a;fontSize=10;"
            "labelBackgroundColor=#ffffff;labelBorderColor=#cbd5e1;fontFamily=Segoe UI,Helvetica;"
        )
        cell = ET.SubElement(root, 'mxCell', {
            'id': edge_id,
            'value': label,
            'style': edge_style,
            'edge': '1',
            'source': source_id,
            'target': target_id,
            'parent': '1'
        })
        geo = ET.SubElement(cell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
        if waypoints:
            pts = ET.SubElement(geo, 'Array', {'as': 'points'})
            for wx, wy in waypoints:
                ET.SubElement(pts, 'mxPoint', {'x': str(wx), 'y': str(wy)})
        return cell

    # Clean White BPMN Styles
    start_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#dcfce7;strokeColor=#16a34a;strokeWidth=2;fontColor=#14532d;fontStyle=1;fontSize=11;fontFamily=Segoe UI,Helvetica;"
    end_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#fee2e2;strokeColor=#dc2626;strokeWidth=2.5;fontColor=#7f1d1d;fontStyle=1;fontSize=11;fontFamily=Segoe UI,Helvetica;"
    
    task_cust_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#0284c7;strokeWidth=1.5;fontColor=#0c4a6e;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=0;"
    task_bot_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#eef2ff;strokeColor=#6366f1;strokeWidth=1.5;fontColor=#1e1b4b;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=0;"
    task_cs_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=1.5;fontColor=#14532d;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=0;"
    task_sup_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#faf5ff;strokeColor=#9333ea;strokeWidth=1.5;fontColor=#3b0764;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=0;"
    gw_style = "rhombus;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#d97706;strokeWidth=2;fontColor=#78350f;fontStyle=1;fontSize=10;fontFamily=Segoe UI,Helvetica;"

    # --- LANE 1: Pelanggan (Customer / End-User) ---
    add_node('n_start', 'Mulai:\nKendala Terjadi', start_style, 120, 115, 52, 52)
    add_node('n_cust_open', 'Buka Live Chat Widget\ndi Web & Input Pesan', task_cust_style, 215, 106, 145, 70)
    add_node('n_cust_eval', 'Terima Jawaban AI &\nCoba Langkah Solusi', task_cust_style, 650, 106, 145, 70)
    add_node('n_gw_cust_solved', 'Masalah\nSelesai?', gw_style, 840, 111, 60, 60)
    add_node('n_cust_rate_bot', 'Beri Rating Kepuasan\n(1-5 Bintang)', task_cust_style, 945, 106, 145, 70)
    add_node('n_end_bot', 'Selesai:\nTiket Selesai (AI)', end_style, 1135, 115, 52, 52)
    
    add_node('n_cust_escalate', 'Klik "Hubungi CS"\n/ Respon Tidak Membantu', task_cust_style, 895, 190, 155, 50)
    add_node('n_cust_chat_cs', 'Komunikasi Interaktif 1-on-1\ndengan CS Manusia', task_cust_style, 1270, 106, 155, 70)
    add_node('n_cust_final_review', 'Konfirmasi Penyelesaian &\nBeri Rating Layanan', task_cust_style, 1545, 106, 145, 70)
    add_node('n_end_human', 'Selesai:\nTiket Selesai (CS)', end_style, 1730, 115, 52, 52)

    # --- LANE 2: AI Bot Assistant ---
    add_node('n_bot_nlp', 'Inisialisasi Sesi Tiket &\nEvaluasi Pesan (KB Match)', task_bot_style, 390, 315, 155, 70)
    add_node('n_gw_bot_conf', 'Confidence\nScore >= 75%?', gw_style, 580, 320, 60, 60)
    add_node('n_bot_reply', 'Kirim Solusi Otomatis &\nOpsi "Bicara CS"', task_bot_style, 665, 315, 145, 70)
    add_node('n_bot_escalate', 'Update Status: WAITING_AGENT\nBroadcast Sinyal WebSocket', task_bot_style, 895, 315, 155, 70)

    # --- LANE 3: Customer Support (Web & Mobile) ---
    add_node('n_cs_notif', 'Terima Notifikasi Tiket Baru\ndi Web & Flutter App', task_cs_style, 1090, 535, 155, 70)
    add_node('n_cs_claim', 'Klaim Tiket (Claim Session)\n& Nonaktifkan AI Bot', task_cs_style, 1270, 535, 155, 70)
    add_node('n_cs_investigate', 'Analisis Chat Log AI &\nLakukan Troubleshooting', task_cs_style, 1270, 630, 155, 70)
    add_node('n_gw_cs_l2', 'Perlu Eskalasi\nTeknis L2?', gw_style, 1460, 635, 60, 60)
    add_node('n_cs_resolve', 'Terapkan Solusi &\nUpdate Status RESOLVED', task_cs_style, 1545, 535, 145, 70)

    # --- LANE 4: Supervisor / Technical Lead ---
    add_node('n_sup_review', 'Review Log Server / Bug Code\n& Berikan Panduan Resolusi', task_sup_style, 1400, 800, 175, 70)

    # CONNECTORS
    add_edge('e1', 'n_start', 'n_cust_open')
    add_edge('e2', 'n_cust_open', 'n_bot_nlp', '', [(287, 350)])
    add_edge('e3', 'n_bot_nlp', 'n_gw_bot_conf')
    add_edge('e4', 'n_gw_bot_conf', 'n_bot_reply', 'Ya (Tinggi)')
    add_edge('e5', 'n_gw_bot_conf', 'n_bot_escalate', 'Tidak / Ambigu', [(610, 420), (972, 420)])
    add_edge('e6', 'n_bot_reply', 'n_cust_eval')
    add_edge('e7', 'n_cust_eval', 'n_gw_cust_solved')
    add_edge('e8', 'n_gw_cust_solved', 'n_cust_rate_bot', 'Ya')
    add_edge('e9', 'n_cust_rate_bot', 'n_end_bot')
    add_edge('e10', 'n_gw_cust_solved', 'n_cust_escalate', 'Tidak', [(870, 215)])
    add_edge('e11', 'n_cust_escalate', 'n_bot_escalate')
    add_edge('e12', 'n_bot_escalate', 'n_cs_notif', '', [(1050, 350), (1050, 570)])
    add_edge('e13', 'n_cs_notif', 'n_cs_claim')
    add_edge('e14', 'n_cs_claim', 'n_cs_investigate')
    add_edge('e15', 'n_cs_investigate', 'n_cust_chat_cs', 'Real-time WebSocket Sync', [(1347, 200)])
    add_edge('e16', 'n_cs_investigate', 'n_gw_cs_l2')
    add_edge('e17', 'n_gw_cs_l2', 'n_sup_review', 'Ya (Kompleks)', [(1490, 835)])
    add_edge('e18', 'n_sup_review', 'n_cs_resolve', 'Solusi Disetujui', [(1617, 835)])
    add_edge('e19', 'n_gw_cs_l2', 'n_cs_resolve', 'Tidak (Teratasi)', [(1490, 570)])
    add_edge('e20', 'n_cs_resolve', 'n_cust_final_review')
    add_edge('e21', 'n_cust_final_review', 'n_end_human')

    # Format XML
    rough_string = ET.tostring(mxfile, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    output_path = r'C:\Users\Dell 3490\.gemini\antigravity\scratch\ciheul-helpdesk\docs\bpmn\helpdesk_process_swimlane.drawio'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print(f"Clean white Draw.io BPMN generated at: {output_path}")

def generate_svg_and_pdf():
    """
    Renders the exact BPMN Swimlane diagram into a pristine vector SVG and HTML,
    then uses Microsoft Edge headless to compile it to helpdesk_process_swimlane.pdf.
    """
    html_content = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>BPMN Swimlane - Omnichannel Helpdesk (Ciheul Technologies)</title>
<style>
  @page {
    size: 420mm 297mm; /* A3 Landscape */
    margin: 0;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    padding: 0;
    width: 420mm;
    height: 297mm;
    background-color: #ffffff;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #0f172a;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    overflow: hidden;
  }
  .svg-container {
    width: 420mm;
    height: 297mm;
    padding: 10mm 12mm;
    margin: 0 auto;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #ffffff;
  }
  svg {
    width: 100%;
    height: 100%;
    max-height: 275mm;
  }
</style>
</head>
<body>
<div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1820 980" width="1820" height="980" style="background:#ffffff; font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
  <defs>
    <!-- Arrow Marker -->
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#475569"/>
    </marker>
    <!-- Filter for subtle crisp card shadow -->
    <filter id="subtle-shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
  </defs>

  <!-- 1. POOL CONTAINER -->
  <rect x="20" y="20" width="1780" height="940" rx="6" fill="#ffffff" stroke="#475569" stroke-width="2"/>
  
  <!-- Pool Main Header Bar (Left vertical) -->
  <path d="M 20 26 Q 20 20 26 20 L 65 20 L 65 960 L 26 960 Q 20 960 20 954 Z" fill="#1e293b"/>
  <text x="-490" y="47" transform="rotate(-90)" fill="#ffffff" font-size="12.5" font-weight="700" letter-spacing="1.5" text-anchor="middle">
    PROSES BISNIS SISTEM HELPDESK &amp; OMNICHANNEL LIVE SUPPORT (CIHEUL TECHNOLOGIES)
  </text>

  <!-- 2. SWIMLANES -->
  <!-- Lane 1: Pelanggan (Y: 20 to 235, H: 215) -->
  <rect x="65" y="20" width="1735" height="215" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.2"/>
  <rect x="65" y="20" width="40" height="215" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
  <text x="-127" y="90" transform="rotate(-90)" fill="#0369a1" font-size="11.5" font-weight="700" text-anchor="middle">
    Pelanggan (Customer / End-User)
  </text>

  <!-- Lane 2: AI Bot Engine (Y: 235 to 450, H: 215) -->
  <rect x="65" y="235" width="1735" height="215" fill="#fcfdff" stroke="#cbd5e1" stroke-width="1.2"/>
  <rect x="65" y="235" width="40" height="215" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1.2"/>
  <text x="-342" y="90" transform="rotate(-90)" fill="#4338ca" font-size="11.5" font-weight="700" text-anchor="middle">
    Sistem AI Helpdesk (Bot Assistant)
  </text>

  <!-- Lane 3: CS Agent (Y: 450 to 730, H: 280) -->
  <rect x="65" y="450" width="1735" height="280" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.2"/>
  <rect x="65" y="450" width="40" height="280" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
  <text x="-590" y="90" transform="rotate(-90)" fill="#0284c7" font-size="11.5" font-weight="700" text-anchor="middle">
    Customer Support (CS Agent - Web &amp; Mobile)
  </text>

  <!-- Lane 4: Supervisor L2 (Y: 730 to 960, H: 230) -->
  <rect x="65" y="730" width="1735" height="230" fill="#fcfdff" stroke="#cbd5e1" stroke-width="1.2"/>
  <rect x="65" y="730" width="40" height="230" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1.2"/>
  <text x="-845" y="90" transform="rotate(-90)" fill="#6b21a8" font-size="11.5" font-weight="700" text-anchor="middle">
    Supervisor / Technical Lead (L2)
  </text>

  <!-- 3. CONNECTING FLOWS (Orthogonal Lines & Arrows) -->
  <!-- e1: start -> cust_open -->
  <path d="M 171 125 L 215 125" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>
  
  <!-- e2: cust_open -> bot_nlp -->
  <path d="M 287 160 L 287 342 L 380 342" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e3: bot_nlp -> gw_bot_conf -->
  <path d="M 535 342 L 575 342" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e4: gw_bot_conf -> bot_reply (Ya) -->
  <path d="M 635 342 L 670 342" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e5: gw_bot_conf -> bot_escalate (Tidak / Ambigu) -->
  <path d="M 605 372 L 605 415 L 972 415 L 972 377" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e6: bot_reply -> cust_eval -->
  <path d="M 742 307 L 742 160" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e7: cust_eval -> gw_cust_solved -->
  <path d="M 815 125 L 850 125" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e8: gw_cust_solved -> cust_rate_bot (Ya) -->
  <path d="M 910 125 L 950 125" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e9: cust_rate_bot -> end_bot -->
  <path d="M 1100 125 L 1149 125" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e10: gw_cust_solved -> cust_escalate (Tidak) -->
  <path d="M 880 155 L 880 200 L 905 200" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e11: cust_escalate -> bot_escalate -->
  <path d="M 977 225 L 977 307" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e12: bot_escalate -> cs_notif -->
  <path d="M 1050 342 L 1065 342 L 1065 560 L 1085 560" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e13: cs_notif -> cs_claim -->
  <path d="M 1240 560 L 1275 560" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e14: cs_claim -> cs_investigate -->
  <path d="M 1352 595 L 1352 625" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e15: cs_investigate -> cust_chat_cs (Realtime WS) -->
  <path d="M 1345 625 L 1345 160" fill="none" stroke="#0284c7" stroke-width="2.2" stroke-dasharray="5 3" marker-end="url(#arrow)"/>

  <!-- e16: cs_investigate -> gw_cs_l2 -->
  <path d="M 1430 660 L 1465 660" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e17: gw_cs_l2 -> sup_review (Ya Kompleks) -->
  <path d="M 1495 690 L 1495 805" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e18: sup_review -> cs_resolve (Solusi Disetujui) -->
  <path d="M 1580 840 L 1625 840 L 1625 595" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e19: gw_cs_l2 -> cs_resolve (Tidak Teratasi) -->
  <path d="M 1525 660 L 1585 660 L 1585 595" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e20: cs_resolve -> cust_final_review -->
  <path d="M 1625 525 L 1625 160" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- e21: cust_final_review -> end_human -->
  <path d="M 1695 125 L 1724 125" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- 4. FLOW ANNOTATION BADGES / LABELS -->
  <!-- Label e4: Ya -->
  <rect x="635" y="327" width="32" height="16" rx="3" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>
  <text x="651" y="339" fill="#15803d" font-size="9" font-weight="700" text-anchor="middle">Ya</text>

  <!-- Label e5: Tidak / Ambigu -->
  <rect x="740" y="405" width="85" height="18" rx="3" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>
  <text x="782" y="418" fill="#b91c1c" font-size="9.5" font-weight="700" text-anchor="middle">Tidak / Ambigu</text>

  <!-- Label e8: Ya -->
  <rect x="912" y="115" width="28" height="16" rx="3" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>
  <text x="926" y="127" fill="#15803d" font-size="9" font-weight="700" text-anchor="middle">Ya</text>

  <!-- Label e10: Tidak -->
  <rect x="862" y="170" width="36" height="16" rx="3" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>
  <text x="880" y="182" fill="#b91c1c" font-size="9" font-weight="700" text-anchor="middle">Tidak</text>

  <!-- Label e15: Real-time WebSocket Sync -->
  <rect x="1275" y="380" width="140" height="20" rx="4" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.2"/>
  <text x="1345" y="394" fill="#0369a1" font-size="9.5" font-weight="700" text-anchor="middle">WebSocket Sync (Live)</text>

  <!-- Label e17: Ya (Kompleks) -->
  <rect x="1455" y="740" width="80" height="18" rx="3" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>
  <text x="1495" y="753" fill="#7e22ce" font-size="9" font-weight="700" text-anchor="middle">Ya (Kompleks)</text>

  <!-- Label e18: Solusi Disetujui -->
  <rect x="1575" y="710" width="95" height="18" rx="3" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>
  <text x="1622" y="723" fill="#15803d" font-size="9" font-weight="700" text-anchor="middle">Solusi Disetujui</text>

  <!-- 5. BPMN NODES (Clean Cards with Elegant Typography) -->

  <!-- LANE 1: Pelanggan Nodes -->
  <!-- Start Event -->
  <circle cx="145" cy="125" r="26" fill="#dcfce7" stroke="#16a34a" stroke-width="2.5" filter="url(#subtle-shadow)"/>
  <text x="145" y="122" fill="#14532d" font-size="10" font-weight="700" text-anchor="middle">Mulai</text>
  <text x="145" y="134" fill="#14532d" font-size="8.5" text-anchor="middle">Kendala</text>

  <!-- Task: Buka Live Chat -->
  <rect x="215" y="90" width="145" height="70" rx="8" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="287" y="120" fill="#0c4a6e" font-size="10.5" font-weight="700" text-anchor="middle">Buka Live Chat Widget</text>
  <text x="287" y="136" fill="#0369a1" font-size="9.5" text-anchor="middle">di Web &amp; Input Pesan</text>

  <!-- Task: Coba Solusi AI -->
  <rect x="670" y="90" width="145" height="70" rx="8" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="742" y="120" fill="#0c4a6e" font-size="10.5" font-weight="700" text-anchor="middle">Terima Jawaban AI &amp;</text>
  <text x="742" y="136" fill="#0369a1" font-size="9.5" text-anchor="middle">Coba Langkah Solusi</text>

  <!-- Gateway: Masalah Selesai? -->
  <polygon points="880,95 910,125 880,155 850,125" fill="#fef3c7" stroke="#d97706" stroke-width="2" filter="url(#subtle-shadow)"/>
  <text x="880" y="122" fill="#78350f" font-size="9.5" font-weight="700" text-anchor="middle">Masalah</text>
  <text x="880" y="133" fill="#78350f" font-size="9" text-anchor="middle">Selesai?</text>

  <!-- Task: Rating Bot -->
  <rect x="950" y="90" width="150" height="70" rx="8" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1025" y="120" fill="#0c4a6e" font-size="10.5" font-weight="700" text-anchor="middle">Beri Rating Kepuasan</text>
  <text x="1025" y="136" fill="#0369a1" font-size="9.5" text-anchor="middle">(1-5 Bintang)</text>

  <!-- End Event Bot -->
  <circle cx="1175" cy="125" r="26" fill="#fee2e2" stroke="#dc2626" stroke-width="3" filter="url(#subtle-shadow)"/>
  <text x="1175" y="121" fill="#7f1d1d" font-size="9.5" font-weight="700" text-anchor="middle">Selesai</text>
  <text x="1175" y="133" fill="#991b1b" font-size="8" text-anchor="middle">Tiket (AI)</text>

  <!-- Task: Eskalasi CS -->
  <rect x="905" y="175" width="145" height="50" rx="8" fill="#fff7ed" stroke="#ea580c" stroke-width="1.5" filter="url(#subtle-shadow)"/>
  <text x="977" y="197" fill="#9a3412" font-size="10" font-weight="700" text-anchor="middle">Klik "Hubungi CS"</text>
  <text x="977" y="211" fill="#c2410c" font-size="8.5" text-anchor="middle">Respon AI Belum Cukup</text>

  <!-- Task: Live Chat CS -->
  <rect x="1270" y="90" width="150" height="70" rx="8" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1345" y="120" fill="#0c4a6e" font-size="10.5" font-weight="700" text-anchor="middle">Komunikasi 1-on-1</text>
  <text x="1345" y="136" fill="#0369a1" font-size="9.5" text-anchor="middle">dengan CS Manusia</text>

  <!-- Task: Review CS -->
  <rect x="1550" y="90" width="145" height="70" rx="8" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1622" y="120" fill="#0c4a6e" font-size="10" font-weight="700" text-anchor="middle">Konfirmasi Selesai &amp;</text>
  <text x="1622" y="136" fill="#0369a1" font-size="9" text-anchor="middle">Beri Rating CS</text>

  <!-- End Event Human -->
  <circle cx="1750" cy="125" r="26" fill="#fee2e2" stroke="#dc2626" stroke-width="3" filter="url(#subtle-shadow)"/>
  <text x="1750" y="121" fill="#7f1d1d" font-size="9.5" font-weight="700" text-anchor="middle">Selesai</text>
  <text x="1750" y="133" fill="#991b1b" font-size="8" text-anchor="middle">Tiket (CS)</text>

  <!-- LANE 2: AI Bot Assistant Nodes -->
  <!-- Task: Bot NLP Match -->
  <rect x="380" y="307" width="155" height="70" rx="8" fill="#eef2ff" stroke="#6366f1" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="457" y="337" fill="#1e1b4b" font-size="10" font-weight="700" text-anchor="middle">Inisialisasi Sesi Tiket &amp;</text>
  <text x="457" y="353" fill="#4338ca" font-size="9" text-anchor="middle">Evaluasi FAQ (KB Match)</text>

  <!-- Gateway: Confidence >= 75%? -->
  <polygon points="605,312 635,342 605,372 575,342" fill="#fef3c7" stroke="#d97706" stroke-width="2" filter="url(#subtle-shadow)"/>
  <text x="605" y="339" fill="#78350f" font-size="9" font-weight="700" text-anchor="middle">Score &gt;=</text>
  <text x="605" y="350" fill="#78350f" font-size="8.5" text-anchor="middle">75%?</text>

  <!-- Task: Bot Reply -->
  <rect x="670" y="307" width="145" height="70" rx="8" fill="#eef2ff" stroke="#6366f1" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="742" y="337" fill="#1e1b4b" font-size="10.5" font-weight="700" text-anchor="middle">Kirim Solusi Otomatis</text>
  <text x="742" y="353" fill="#4338ca" font-size="9.5" text-anchor="middle">&amp; Opsi "Bicara CS"</text>

  <!-- Task: Bot Escalate -->
  <rect x="895" y="307" width="155" height="70" rx="8" fill="#eef2ff" stroke="#6366f1" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="972" y="337" fill="#1e1b4b" font-size="10" font-weight="700" text-anchor="middle">Status: WAITING_AGENT</text>
  <text x="972" y="353" fill="#4338ca" font-size="9" text-anchor="middle">Broadcast WebSocket</text>

  <!-- LANE 3: CS Agent Nodes -->
  <!-- Task: CS Notif -->
  <rect x="1085" y="525" width="155" height="70" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1162" y="555" fill="#14532d" font-size="10" font-weight="700" text-anchor="middle">Terima Notifikasi Tiket</text>
  <text x="1162" y="571" fill="#15803d" font-size="9" text-anchor="middle">di Web &amp; Flutter App</text>

  <!-- Task: CS Claim -->
  <rect x="1275" y="525" width="155" height="70" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1352" y="555" fill="#14532d" font-size="10" font-weight="700" text-anchor="middle">Klaim Tiket (Claim)</text>
  <text x="1352" y="571" fill="#15803d" font-size="9" text-anchor="middle">&amp; Nonaktifkan AI Bot</text>

  <!-- Task: CS Troubleshoot -->
  <rect x="1275" y="625" width="155" height="70" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1352" y="655" fill="#14532d" font-size="10" font-weight="700" text-anchor="middle">Analisis Chat Log AI &amp;</text>
  <text x="1352" y="671" fill="#15803d" font-size="9" text-anchor="middle">Lakukan Troubleshooting</text>

  <!-- Gateway: Perlu L2? -->
  <polygon points="1495,630 1525,660 1495,690 1465,660" fill="#fef3c7" stroke="#d97706" stroke-width="2" filter="url(#subtle-shadow)"/>
  <text x="1495" y="657" fill="#78350f" font-size="9" font-weight="700" text-anchor="middle">Perlu</text>
  <text x="1495" y="668" fill="#78350f" font-size="8.5" text-anchor="middle">L2?</text>

  <!-- Task: CS Resolve -->
  <rect x="1550" y="525" width="150" height="70" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1625" y="555" fill="#14532d" font-size="10.5" font-weight="700" text-anchor="middle">Terapkan Solusi &amp;</text>
  <text x="1625" y="571" fill="#15803d" font-size="9.5" text-anchor="middle">Status: RESOLVED</text>

  <!-- LANE 4: Supervisor Nodes -->
  <!-- Task: Sup Review -->
  <rect x="1405" y="805" width="175" height="70" rx="8" fill="#faf5ff" stroke="#9333ea" stroke-width="1.6" filter="url(#subtle-shadow)"/>
  <text x="1492" y="835" fill="#3b0764" font-size="10" font-weight="700" text-anchor="middle">Review Log / Bug Teknis</text>
  <text x="1492" y="851" fill="#6b21a8" font-size="9" text-anchor="middle">&amp; Panduan Resolusi L2</text>
</svg>
</div>
</body>
</html>"""

    base_dir = r"C:\Users\Dell 3490\.gemini\antigravity\scratch\ciheul-helpdesk\docs\bpmn"
    print_html_path = os.path.join(base_dir, "print_bpmn.html")
    preview_html_path = os.path.join(base_dir, "PREVIEW_BPMN.html")
    pdf_path = os.path.join(base_dir, "helpdesk_process_swimlane.pdf")

    with open(print_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    preview_html = html_content.replace(
        "<body>",
        """<body style="background:#f1f5f9; padding:20px;">
<div style="max-width:1820px; margin:0 auto 15px auto; display:flex; justify-content:space-between; align-items:center; background:#ffffff; padding:14px 20px; border-radius:8px; border:1px solid #cbd5e1; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
  <div>
    <h2 style="margin:0; font-size:17px; color:#0f172a;">BPMN Swimlane Diagram: Omnichannel Helpdesk System</h2>
    <span style="font-size:12px; color:#64748b;">Format Draw.io Clean White Flowchart | Ekspor PDF Resmi Soal 1a</span>
  </div>
  <div>
    <button onclick="window.print()" style="background:#0284c7; color:#ffffff; border:none; padding:8px 16px; border-radius:6px; font-weight:600; font-size:12.5px; cursor:pointer;">Cetak / Simpan PDF</button>
  </div>
</div>"""
    )
    with open(preview_html_path, "w", encoding="utf-8") as f:
        f.write(preview_html)

    print("HTML & SVG preview files generated.")

    # Convert to PDF via Microsoft Edge headless
    edge_cmd = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        print_html_path
    ]
    try:
        subprocess.run(edge_cmd, check=True)
        print(f"Pristine vector PDF created at: {pdf_path}")
    except Exception as e:
        print(f"Error compiling PDF via Edge: {e}")

if __name__ == '__main__':
    create_clean_drawio_bpmn()
    generate_svg_and_pdf()
