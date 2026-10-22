import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

def create_drawio_bpmn():
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2026-10-22T08:00:00.000Z',
        'agent': 'Antigravity AI',
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
        'pageWidth': '1800',
        'pageHeight': '1100',
        'math': '0',
        'shadow': '0'
    })
    
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', {'id': '0'})
    ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})
    
    # 1. Main Pool
    pool_style = (
        "swimlane;html=1;childLayout=stackLayout;resizeParent=1;resizeParentMax=0;"
        "startSize=40;horizontal=0;horizontalFlip=0;fillColor=#0f172a;strokeColor=#334155;"
        "fontColor=#f8fafc;fontStyle=1;fontSize=14;fontFamily=Segoe UI,Helvetica;"
    )
    pool = ET.SubElement(root, 'mxCell', {
        'id': 'pool_1',
        'value': 'PROSES BISNIS SISTEM HELPDESK & OMNICHANNEL LIVE SUPPORT (CIHEUL TECHNOLOGIES)',
        'style': pool_style,
        'vertex': '1',
        'parent': '1'
    })
    ET.SubElement(pool, 'mxGeometry', {
        'x': '40', 'y': '40', 'width': '1700', 'height': '920', 'as': 'geometry'
    })
    
    # 2. Swimlanes (4 Roles)
    lanes = [
        ('lane_customer', 'Pelanggan (Customer / End-User)', '#1e293b', 210),
        ('lane_ai_bot', 'Sistem AI Helpdesk (Bot Assistant)', '#0f172a', 210),
        ('lane_cs_agent', 'Customer Support (CS Agent - Web & Mobile)', '#1e293b', 270),
        ('lane_supervisor', 'Supervisor / Technical Lead (L2 Escalation)', '#0f172a', 190)
    ]
    
    lane_y = 0
    for lane_id, lane_name, lane_bg, lane_h in lanes:
        lane_style = (
            f"swimlane;html=1;startSize=30;horizontal=0;fillColor={lane_bg};"
            f"strokeColor=#334155;fontColor=#38bdf8;fontStyle=1;fontSize=12;"
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
            'x': '40', 'y': str(lane_y), 'width': '1660', 'height': str(lane_h), 'as': 'geometry'
        })
        lane_y += lane_h

    # Helper function for adding nodes
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

    # Helper function for connectors
    def add_edge(edge_id, source_id, target_id, label='', waypoints=None):
        edge_style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
            "html=1;strokeColor=#94a3b8;strokeWidth=2;fontColor=#e2e8f0;fontSize=10;"
            "labelBackgroundColor=#0f172a;fontFamily=Segoe UI,Helvetica;"
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

    # Styles
    start_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#10b981;strokeColor=#059669;fontColor=#ffffff;fontStyle=1;fontSize=11;"
    end_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#ef4444;strokeColor=#b91c1c;strokeWidth=3;fontColor=#ffffff;fontStyle=1;fontSize=11;"
    task_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#475569;strokeWidth=1.5;fontColor=#f8fafc;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=1;"
    task_bot_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#1e1b4b;strokeColor=#6366f1;strokeWidth=1.5;fontColor=#e0e7ff;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=1;"
    task_cs_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#082f49;strokeColor=#0284c7;strokeWidth=1.5;fontColor=#e0f2fe;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=1;"
    task_sup_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#31104b;strokeColor=#a855f7;strokeWidth=1.5;fontColor=#f3e8ff;fontSize=11;fontFamily=Segoe UI,Helvetica;shadow=1;"
    gw_style = "rhombus;whiteSpace=wrap;html=1;fillColor=#f59e0b;strokeColor=#d97706;strokeWidth=2;fontColor=#1e293b;fontStyle=1;fontSize=10;fontFamily=Segoe UI,Helvetica;"

    # NODES (Coordinates absolute in pool)
    # --- LANE 1: Pelanggan (Y: 40 to 250) ---
    add_node('n_start', 'Mulai: Kendala Terjadi', start_style, 120, 115, 50, 50)
    add_node('n_cust_open', 'Buka Live Chat Widget\ndi Web & Input Pesan', task_style, 210, 105, 140, 70)
    add_node('n_cust_eval', 'Terima Jawaban AI &\nCoba Langkah Solusi', task_style, 640, 105, 140, 70)
    add_node('n_gw_cust_solved', 'Masalah\nSelesai?', gw_style, 830, 110, 60, 60)
    add_node('n_cust_rate_bot', 'Beri Rating Kepuasan\n(1-5 Bintang)', task_style, 940, 105, 140, 70)
    add_node('n_end_bot', 'Selesai:\nTiket Selesai (AI)', end_style, 1130, 115, 50, 50)
    
    add_node('n_cust_escalate', 'Klik "Hubungi CS"\n/ Respon Tidak Membantu', task_style, 890, 190, 150, 50)
    add_node('n_cust_chat_cs', 'Komunikasi Interaktif 1-on-1\ndengan CS Manusia', task_style, 1260, 105, 150, 70)
    add_node('n_cust_final_review', 'Konfirmasi Penyelesaian &\nBeri Rating CS', task_style, 1530, 105, 140, 70)
    add_node('n_end_human', 'Selesai:\nTiket Selesai (CS)', end_style, 1690, 115, 50, 50)

    # --- LANE 2: AI Bot Assistant (Y: 250 to 460) ---
    add_node('n_bot_nlp', 'Inisialisasi Sesi Tiket &\nEvaluasi Pesan (KB Match)', task_bot_style, 380, 315, 150, 70)
    add_node('n_gw_bot_conf', 'Confidence\nScore >= 75%?', gw_style, 560, 320, 60, 60)
    add_node('n_bot_reply', 'Kirim Solusi Otomatis &\nOpsi "Bicara CS"', task_bot_style, 640, 315, 140, 70)
    add_node('n_bot_escalate', 'Update Status: WAITING_AGENT\nBroadcast Sinyal WebSocket', task_bot_style, 890, 315, 150, 70)

    # --- LANE 3: CS Agent (Web & Mobile) (Y: 460 to 730) ---
    add_node('n_cs_notif', 'Terima Notifikasi Tiket Baru\ndi Web & Flutter App', task_cs_style, 1080, 535, 150, 70)
    add_node('n_cs_claim', 'Klaim Tiket (Claim Session)\n& Nonaktifkan AI Bot', task_cs_style, 1260, 535, 150, 70)
    add_node('n_cs_investigate', 'Analisis Chat Log AI &\nLakukan Troubleshooting', task_cs_style, 1260, 630, 150, 70)
    add_node('n_gw_cs_l2', 'Perlu Eskalasi\nTeknis L2?', gw_style, 1445, 635, 60, 60)
    add_node('n_cs_resolve', 'Terapkan Solusi &\nUpdate Status RESOLVED', task_cs_style, 1530, 535, 140, 70)

    # --- LANE 4: Supervisor / Tech Lead (Y: 730 to 920) ---
    add_node('n_sup_review', 'Review Log Server / Bug Code\n& Berikan Panduan Resolusi', task_sup_style, 1390, 800, 170, 70)

    # CONNECTORS (EDGES)
    add_edge('e1', 'n_start', 'n_cust_open')
    add_edge('e2', 'n_cust_open', 'n_bot_nlp', '', [(280, 350)])
    add_edge('e3', 'n_bot_nlp', 'n_gw_bot_conf')
    add_edge('e4', 'n_gw_bot_conf', 'n_bot_reply', 'Ya (Tinggi)')
    add_edge('e5', 'n_gw_bot_conf', 'n_bot_escalate', 'Tidak / Ambigu', [(590, 420), (965, 420)])
    add_edge('e6', 'n_bot_reply', 'n_cust_eval')
    add_edge('e7', 'n_cust_eval', 'n_gw_cust_solved')
    add_edge('e8', 'n_gw_cust_solved', 'n_cust_rate_bot', 'Ya')
    add_edge('e9', 'n_cust_rate_bot', 'n_end_bot')
    add_edge('e10', 'n_gw_cust_solved', 'n_cust_escalate', 'Tidak', [(860, 215)])
    add_edge('e11', 'n_cust_escalate', 'n_bot_escalate')
    add_edge('e12', 'n_bot_escalate', 'n_cs_notif', '', [(1040, 350), (1040, 570)])
    add_edge('e13', 'n_cs_notif', 'n_cs_claim')
    add_edge('e14', 'n_cs_claim', 'n_cs_investigate')
    add_edge('e15', 'n_cs_investigate', 'n_cust_chat_cs', 'Real-time WebSocket Sync', [(1335, 200)])
    add_edge('e16', 'n_cs_investigate', 'n_gw_cs_l2')
    add_edge('e17', 'n_gw_cs_l2', 'n_sup_review', 'Ya (Kompleks)', [(1475, 835)])
    add_edge('e18', 'n_sup_review', 'n_cs_resolve', 'Solusi Disetujui', [(1600, 835)])
    add_edge('e19', 'n_gw_cs_l2', 'n_cs_resolve', 'Tidak (Teratasi)', [(1475, 570)])
    add_edge('e20', 'n_cs_resolve', 'n_cust_final_review')
    add_edge('e21', 'n_cust_final_review', 'n_end_human')

    # Format nicely as XML string
    rough_string = ET.tostring(mxfile, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    output_path = r'C:\Users\Dell 3490\.gemini\antigravity\scratch\ciheul-helpdesk\docs\bpmn\helpdesk_process_swimlane.drawio'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print(f"BPMN file generated successfully at {output_path}")

if __name__ == '__main__':
    create_drawio_bpmn()
