(function () {
    "use strict";

    // 1. Configuration & Session Management
    const API_BASE = window.CIHEUL_API_URL || (window.location.origin.includes(":8000") ? window.location.origin : "http://localhost:8000");
    const WS_BASE = API_BASE.replace(/^http/, "ws");
    const LOGO_URL = `${API_BASE}/widget/dist/ciheul-logo.png`;

    function generateCryptographicSessionToken() {
        try {
            if (typeof window !== "undefined" && window.crypto && window.crypto.getRandomValues) {
                const bytes = new Uint8Array(24);
                window.crypto.getRandomValues(bytes);
                return "cust_" + Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
            }
        } catch (e) {
            // fallback if secure context unavailable
        }
        return "cust_" + Math.random().toString(36).substring(2, 12) + Date.now().toString(36);
    }

    let sessionToken = localStorage.getItem("ciheul_session_token");
    if (!sessionToken) {
        sessionToken = generateCryptographicSessionToken();
        localStorage.setItem("ciheul_session_token", sessionToken);
    }

    let activeTicketId = localStorage.getItem("ciheul_ticket_id");
    let socket = null;
    let heartbeatInterval = null;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;
    let lastMessageId = null;
    let isOpen = false;

    // 2. Load Stylesheet Dynamically if not present
    if (!document.getElementById("ciheul-widget-css")) {
        const link = document.createElement("link");
        link.id = "ciheul-widget-css";
        link.rel = "stylesheet";
        link.href = `${API_BASE}/widget/dist/widget.css`;
        document.head.appendChild(link);
    }

    // 3. Inject Widget DOM
    const root = document.createElement("div");
    root.className = "ch-widget-root";
    root.innerHTML = `
        <div class="ch-window" id="ch-window">
            <div class="ch-header">
                <div class="ch-header-left">
                    <img src="${LOGO_URL}" alt="Logo" class="ch-header-logo" />
                    <div class="ch-header-titles">
                        <h4 class="ch-header-title">Ciheul Support</h4>
                        <span class="ch-header-sub" id="ch-status-sub">Asisten AI Aktif</span>
                    </div>
                </div>
                <button class="ch-close-btn" id="ch-close-btn" title="Tutup">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                </button>
            </div>
            <div class="ch-escalate-bar" id="ch-escalate-bar" style="display: none;">
                <span>Butuh berbicara dengan tim support?</span>
                <button class="ch-escalate-btn" id="ch-escalate-btn">Hubungi CS</button>
            </div>
            <div class="ch-feed" id="ch-feed">
                <div class="ch-msg ch-msg-bot">
                    Halo, saya asisten AI Ciheul. Ada kendala teknis atau pertanyaan yang dapat kami bantu selesaikan?
                </div>
            </div>
            <div class="ch-input-bar">
                <input type="file" id="ch-file-input" accept="image/png,image/jpeg,image/webp,application/pdf" style="display: none;" />
                <button class="ch-attach-btn" id="ch-attach-btn" title="Lampirkan Gambar atau Berkas">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                </button>
                <input type="text" class="ch-input" id="ch-input" placeholder="Tulis pertanyaan Anda..." autocomplete="off" />
                <button class="ch-send-btn" id="ch-send-btn" title="Kirim">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                </button>
            </div>
        </div>
        <button class="ch-launcher-btn" id="ch-launcher-btn" title="Bantuan Support">
            <img src="${LOGO_URL}" alt="Support" />
        </button>
    `;
    document.body.appendChild(root);

    const win = document.getElementById("ch-window");
    const launcher = document.getElementById("ch-launcher-btn");
    const closeBtn = document.getElementById("ch-close-btn");
    const feed = document.getElementById("ch-feed");
    const input = document.getElementById("ch-input");
    const sendBtn = document.getElementById("ch-send-btn");
    const attachBtn = document.getElementById("ch-attach-btn");
    const fileInput = document.getElementById("ch-file-input");
    const escalateBar = document.getElementById("ch-escalate-bar");
    const escalateBtn = document.getElementById("ch-escalate-btn");
    const statusSub = document.getElementById("ch-status-sub");

    // 4. Toggle Window
    launcher.addEventListener("click", () => {
        isOpen = !isOpen;
        win.classList.toggle("ch-open", isOpen);
        if (isOpen) {
            input.focus();
            scrollToBottom();
        }
    });

    closeBtn.addEventListener("click", () => {
        isOpen = false;
        win.classList.remove("ch-open");
    });

    const renderedMessageIds = new Set();

    function parseUTCDate(dateStr) {
        if (!dateStr) return new Date();
        let s = String(dateStr);
        if (!s.endsWith("Z") && !/[+-]\d{2}:\d{2}$/.test(s)) {
            s += "Z";
        }
        return new Date(s);
    }

    function scrollToBottom() {
        feed.scrollTop = feed.scrollHeight;
    }

    function appendMessage(senderType, senderName, content, timeStr, messageId) {
        if (messageId) {
            if (renderedMessageIds.has(messageId)) {
                return; // Deduplicate: already rendered
            }
            renderedMessageIds.add(messageId);
        }

        const msgDiv = document.createElement("div");
        let typeClass = "ch-msg-customer";
        if (senderType === "BOT") typeClass = "ch-msg-bot";
        else if (senderType === "AGENT") typeClass = "ch-msg-agent";
        else if (senderType === "SYSTEM") typeClass = "ch-msg-system";

        msgDiv.className = `ch-msg ${typeClass}`;
        if (messageId) {
            msgDiv.dataset.messageId = messageId;
        }
        
        const time = timeStr ? parseUTCDate(timeStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (senderType === "SYSTEM") {
            msgDiv.innerText = content;
        } else {
            msgDiv.innerHTML = `${formatMessageContent(content)}<div class="ch-msg-time">${time}</div>`;
        }
        
        feed.appendChild(msgDiv);
        scrollToBottom();
    }

    function formatMessageContent(content) {
        if (!content) return "";
        const match = content.match(/\[Lampiran:?\s*(.*?)\]\((.*?)\)/);
        if (match) {
            const filename = match[1];
            let url = match[2];
            if (url.startsWith("/")) {
                url = `${API_BASE}${url}`;
            }
            const isImg = /\.(png|jpe?g|webp|gif)$/i.test(filename) || /\.(png|jpe?g|webp|gif)$/i.test(url);
            if (isImg) {
                return `
                    <div style="margin-bottom: 4px;">
                        <a href="${url}" target="_blank" rel="noopener noreferrer">
                            <img src="${url}" alt="${escapeHTML(filename)}" style="max-width: 100%; max-height: 200px; border-radius: 8px; display: block; border: 1px solid rgba(0,0,0,0.1); cursor: pointer;" />
                        </a>
                        <span style="font-size: 10.5px; opacity: 0.75; display: block; margin-top: 3px;">${escapeHTML(filename)}</span>
                    </div>
                `;
            } else {
                return `
                    <div style="margin-bottom: 4px;">
                        <a href="${url}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: underline; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                            <span>${escapeHTML(filename)}</span>
                        </a>
                    </div>
                `;
            }
        }
        return escapeHTML(content);
    }

    function escapeHTML(str) {
        const div = document.createElement("div");
        div.innerText = str;
        return div.innerHTML.replace(/\n/g, "<br/>");
    }

    // 5. Check Active Ticket on Backend
    async function loadActiveTicket() {
        try {
            const res = await fetch(`${API_BASE}/api/v1/tickets/active`, {
                headers: {
                    "X-Session-Token": sessionToken
                }
            });
            if (res.ok) {
                const ticket = await res.json();
                if (ticket && ticket.id) {
                    activeTicketId = ticket.id;
                    localStorage.setItem("ciheul_ticket_id", activeTicketId);
                    
                    feed.innerHTML = "";
                    if (ticket.messages && ticket.messages.length > 0) {
                        ticket.messages.forEach(m => {
                            appendMessage(m.sender_type, m.sender_name, m.content, m.created_at, m.id);
                            lastMessageId = m.id;
                        });
                    }

                    updateStatusUI(ticket.status);
                    connectWebSocket(activeTicketId);
                } else {
                    activeTicketId = null;
                    localStorage.removeItem("ciheul_ticket_id");
                }
            } else {
                activeTicketId = null;
                localStorage.removeItem("ciheul_ticket_id");
            }
        } catch (err) {
            console.warn("Ciheul Widget: Connection error:", err);
            activeTicketId = null;
            localStorage.removeItem("ciheul_ticket_id");
        }
    }

    function updateStatusUI(status) {
        if (status === "BOT_ACTIVE") {
            statusSub.innerText = "Asisten AI Aktif";
            escalateBar.style.display = "flex";
        } else if (status === "WAITING_AGENT") {
            statusSub.innerText = "Menunggu Customer Support...";
            escalateBar.style.display = "none";
        } else if (status === "AGENT_ACTIVE") {
            statusSub.innerText = "Customer Support Terhubung";
            escalateBar.style.display = "none";
        } else if (status === "RESOLVED" || status === "CLOSED") {
            statusSub.innerText = "Kendala Selesai";
            escalateBar.style.display = "none";
            showResolutionNotice();
        }
    }

    // 6. WebSocket Always-Connected Resilience
    function connectWebSocket(ticketId) {
        if (!ticketId) return;
        if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
            return;
        }

        const wsUrl = `${WS_BASE}/ws/ticket/${ticketId}`;
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            reconnectAttempts = 0;
            
            // In-band authentication handshake - zero token in URL query string
            socket.send(JSON.stringify({
                event: "auth",
                session_token: sessionToken
            }));

            if (heartbeatInterval) clearInterval(heartbeatInterval);
            heartbeatInterval = setInterval(() => {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ event: "ping" }));
                } else {
                    clearInterval(heartbeatInterval);
                }
            }, 15000);

            if (lastMessageId) {
                socket.send(JSON.stringify({
                    event: "sync_missed",
                    last_message_id: lastMessageId
                }));
            }
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.event === "new_message") {
                    appendMessage(data.sender_type, data.sender_name, data.content, data.created_at, data.id);
                    lastMessageId = data.id;
                } else if (data.event === "sync_result" && data.messages) {
                    data.messages.forEach(m => {
                        appendMessage(m.sender_type, m.sender_name, m.content, m.created_at, m.id);
                        lastMessageId = m.id;
                    });
                } else if (data.event === "ticket_escalated") {
                    updateStatusUI("WAITING_AGENT");
                } else if (data.event === "ticket_claimed") {
                    updateStatusUI("AGENT_ACTIVE");
                } else if (data.event === "ticket_resolved") {
                    updateStatusUI("RESOLVED");
                }
            } catch (e) {
                console.error("WS parse error:", e);
            }
        };

        socket.onclose = () => {
            if (heartbeatInterval) clearInterval(heartbeatInterval);
            if (activeTicketId) {
                const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), 10000);
                reconnectAttempts++;
                clearTimeout(reconnectTimeout);
                reconnectTimeout = setTimeout(() => {
                    connectWebSocket(activeTicketId);
                }, delay);
            }
        };
    }

    // 7. Send Message
    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // Client-side length validation: prevent silent truncation or 422 failure
        if (text.length > 3000) {
            appendMessage("SYSTEM", "Sistem", `Pesan melebihi batas maksimum 3.000 karakter (panjang saat ini: ${text.length} karakter). Mohon perpendek pesan Anda.`);
            return;
        }

        if (!activeTicketId) {
            sendBtn.disabled = true;
            input.disabled = true;
            try {
                const res = await fetch(`${API_BASE}/api/v1/tickets`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        session_token: sessionToken,
                        customer_name: "Pelanggan Web",
                        initial_message: text
                    })
                });
                if (res.ok) {
                    const ticket = await res.json();
                    activeTicketId = ticket.id;
                    localStorage.setItem("ciheul_ticket_id", activeTicketId);
                    input.value = "";
                    
                    if (ticket.messages && ticket.messages.length > 0) {
                        const firstMsg = ticket.messages[0];
                        appendMessage(firstMsg.sender_type, firstMsg.sender_name, firstMsg.content, firstMsg.created_at, firstMsg.id);
                        lastMessageId = firstMsg.id;
                    } else {
                        appendMessage("CUSTOMER", "Anda", text);
                    }

                    if (ticket.messages && ticket.messages.length > 1) {
                        const botMsg = ticket.messages[1];
                        appendMessage(botMsg.sender_type, botMsg.sender_name, botMsg.content, botMsg.created_at, botMsg.id);
                        lastMessageId = botMsg.id;
                    }
                    updateStatusUI(ticket.status);
                    connectWebSocket(activeTicketId);
                } else {
                    const errData = await res.json().catch(() => ({}));
                    let errMsg = "Gagal membuat tiket kendala.";
                    if (errData.detail) {
                        if (Array.isArray(errData.detail)) {
                            errMsg = errData.detail.map(d => d.msg || JSON.stringify(d)).join(", ");
                        } else {
                            errMsg = String(errData.detail);
                        }
                    }
                    appendMessage("SYSTEM", "Sistem", errMsg);
                }
            } catch (err) {
                appendMessage("SYSTEM", "Sistem", "Gagal terhubung ke server. Silakan coba lagi.");
            } finally {
                sendBtn.disabled = false;
                input.disabled = false;
                input.focus();
            }
        } else {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    event: "send_message",
                    content: text
                }));
                input.value = "";
            } else {
                appendMessage("SYSTEM", "Sistem", "Menghubungkan kembali ke server...");
            }
        }
    }

    // 8. Escalate
    escalateBtn.addEventListener("click", async () => {
        if (!activeTicketId) return;
        try {
            escalateBtn.disabled = true;
            escalateBtn.innerText = "Menghubungkan...";
            const res = await fetch(`${API_BASE}/api/v1/tickets/${activeTicketId}/escalate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_token: sessionToken })
            });
            if (res.ok) {
                updateStatusUI("WAITING_AGENT");
            }
        } catch (err) {
            console.error("Escalation failed:", err);
        } finally {
            escalateBtn.disabled = false;
        }
    });

    // 9. Resolution Notice & Rating (Minimalist, without emojis)
    function showResolutionNotice() {
        if (document.getElementById("ch-resolution-card")) return;
        const card = document.createElement("div");
        card.id = "ch-resolution-card";
        card.style = "background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px; margin: 10px 0; text-align: center;";
        card.innerHTML = `
            <div style="font-weight: 600; font-size: 13px; color: #111827; margin-bottom: 4px;">Kendala Ditandai Selesai</div>
            <div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">Berikan penilaian kepuasan layanan kami (1 - 5):</div>
            <div id="ch-rating-row" style="display: flex; justify-content: center; gap: 6px; margin-bottom: 12px;">
                <button class="ch-score-btn" data-val="1" style="width: 28px; height: 28px; border-radius: 6px; border: 1px solid #d1d5db; background: white; font-weight: 600; cursor: pointer; font-size: 12px;">1</button>
                <button class="ch-score-btn" data-val="2" style="width: 28px; height: 28px; border-radius: 6px; border: 1px solid #d1d5db; background: white; font-weight: 600; cursor: pointer; font-size: 12px;">2</button>
                <button class="ch-score-btn" data-val="3" style="width: 28px; height: 28px; border-radius: 6px; border: 1px solid #d1d5db; background: white; font-weight: 600; cursor: pointer; font-size: 12px;">3</button>
                <button class="ch-score-btn" data-val="4" style="width: 28px; height: 28px; border-radius: 6px; border: 1px solid #d1d5db; background: white; font-weight: 600; cursor: pointer; font-size: 12px;">4</button>
                <button class="ch-score-btn" data-val="5" style="width: 28px; height: 28px; border-radius: 6px; border: 1px solid #d1d5db; background: white; font-weight: 600; cursor: pointer; font-size: 12px;">5</button>
            </div>
            <div id="ch-rating-status" style="font-size: 11px; color: #0284c7; margin-bottom: 8px; display: none;"></div>
            <button id="ch-start-new" style="background: #111827; color: white; border: none; padding: 6px 14px; border-radius: 16px; font-weight: 600; cursor: pointer; font-size: 11.5px;">Mulai Konsultasi Baru</button>
        `;
        feed.appendChild(card);
        scrollToBottom();

        // Rating button clicks
        card.querySelectorAll(".ch-score-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const score = parseInt(btn.dataset.val);
                try {
                    const res = await fetch(`${API_BASE}/api/v1/tickets/${activeTicketId}/rate`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            session_token: sessionToken,
                            rating: score,
                            feedback: `Penilaian skor ${score} dari widget pelanggan`
                        })
                    });
                    if (res.ok) {
                        const statusBox = document.getElementById("ch-rating-status");
                        statusBox.innerText = `Terima kasih atas penilaian skor ${score}!`;
                        statusBox.style.display = "block";
                        card.querySelectorAll(".ch-score-btn").forEach(b => b.disabled = true);
                    }
                } catch (e) {
                    console.error("Rating error:", e);
                }
            });
        });

        document.getElementById("ch-start-new").addEventListener("click", () => {
            if (socket) {
                socket.close();
                socket = null;
            }
            localStorage.removeItem("ciheul_ticket_id");
            activeTicketId = null;
            lastMessageId = null;
            feed.innerHTML = `
                <div class="ch-msg ch-msg-bot">
                    Halo, saya asisten AI Ciheul. Ada kendala teknis atau pertanyaan yang dapat kami bantu selesaikan?
                </div>
            `;
            updateStatusUI("BOT_ACTIVE");
            input.value = "";
            input.focus();
        });
    }

    // Attachment Button & File Upload Handler
    attachBtn.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        // Validation: 10MB limit
        if (file.size > 10 * 1024 * 1024) {
            appendMessage("SYSTEM", "Sistem", "Ukuran berkas melebihi batas maksimal 10MB.");
            fileInput.value = "";
            return;
        }

        attachBtn.disabled = true;
        attachBtn.style.opacity = "0.5";

        try {
            // If no active ticket exists yet, create ticket first
            if (!activeTicketId) {
                const createRes = await fetch(`${API_BASE}/api/v1/tickets`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        session_token: sessionToken,
                        customer_name: "Pelanggan Web",
                        initial_message: `Mengirim lampiran: ${file.name}`
                    })
                });
                if (createRes.ok) {
                    const ticket = await createRes.json();
                    activeTicketId = ticket.id;
                    localStorage.setItem("ciheul_ticket_id", activeTicketId);
                    if (ticket.messages && ticket.messages.length > 0) {
                        const firstMsg = ticket.messages[0];
                        appendMessage(firstMsg.sender_type, firstMsg.sender_name, firstMsg.content, firstMsg.created_at, firstMsg.id);
                        lastMessageId = firstMsg.id;
                    }
                    if (ticket.messages && ticket.messages.length > 1) {
                        const botMsg = ticket.messages[1];
                        appendMessage(botMsg.sender_type, botMsg.sender_name, botMsg.content, botMsg.created_at, botMsg.id);
                        lastMessageId = botMsg.id;
                    }
                    updateStatusUI(ticket.status);
                    connectWebSocket(activeTicketId);
                } else {
                    throw new Error("Gagal menginisialisasi percakapan untuk mengunggah berkas.");
                }
            }

            // Upload the file to ticket
            const formData = new FormData();
            formData.append("file", file);
            formData.append("session_token", sessionToken);

            const uploadRes = await fetch(`${API_BASE}/api/v1/tickets/${activeTicketId}/upload`, {
                method: "POST",
                body: formData
            });

            if (!uploadRes.ok) {
                const errData = await uploadRes.json().catch(() => ({}));
                appendMessage("SYSTEM", "Sistem", errData.detail || "Gagal mengunggah berkas.");
            }
        } catch (err) {
            console.error("Upload failed:", err);
            appendMessage("SYSTEM", "Sistem", "Terjadi kesalahan saat mengunggah berkas.");
        } finally {
            attachBtn.disabled = false;
            attachBtn.style.opacity = "1";
            fileInput.value = "";
        }
    });

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    loadActiveTicket();
})();
