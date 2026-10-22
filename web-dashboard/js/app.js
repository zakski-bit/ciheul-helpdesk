(function () {
    "use strict";

    const API_BASE = window.location.origin.includes(":8000") ? window.location.origin : "http://localhost:8000";
    const WS_BASE = API_BASE.replace(/^http/, "ws");

    let authToken = localStorage.getItem("ciheul_agent_token");
    let currentAgent = null;
    let activeTicket = null;
    let globalSocket = null;
    let roomSocket = null;
    let allTickets = [];
    let currentFilter = "ALL";
    let latestDraftReply = "";

    // DOM Elements
    const loginModal = document.getElementById("login-modal");
    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error-alert");
    const agentAvatarBtn = document.getElementById("agent-avatar-btn");
    const agentPopover = document.getElementById("agent-popover");
    const btnLogout = document.getElementById("btn-logout");
    const btnSwitchAccount = document.getElementById("btn-switch-account");
    const btnFillCs = document.getElementById("btn-fill-cs");
    const btnFillAdmin = document.getElementById("btn-fill-admin");

    const detailsDrawer = document.getElementById("details-drawer");
    const btnDetailsDrawer = document.getElementById("btn-details-drawer");
    const btnCloseDetails = document.getElementById("btn-close-details");
    const detailsBackdrop = document.getElementById("details-backdrop");

    const macroModal = document.getElementById("macro-modal");
    const btnQuickMacro = document.getElementById("btn-quick-macro");
    const btnCloseMacro = document.getElementById("btn-close-macro");
    const macroBackdrop = document.getElementById("macro-backdrop");

    const btnClaimTicket = document.getElementById("btn-claim-ticket");

    // 1. Authentication Lifecycle
    async function checkAuthentication() {
        if (!authToken) {
            showLoginModal();
            return false;
        }

        try {
            const meRes = await fetch(`${API_BASE}/api/v1/auth/me`, {
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (meRes.ok) {
                currentAgent = await meRes.json();
                updateAgentUI();
                hideLoginModal();
                loadTickets();
                connectGlobalAgentWS();
                return true;
            } else {
                // Token invalid or expired
                authToken = null;
                localStorage.removeItem("ciheul_agent_token");
                showLoginModal();
                return false;
            }
        } catch (e) {
            console.error("Auth verification failed:", e);
            showLoginModal();
            return false;
        }
    }

    function showLoginModal() {
        loginModal.classList.remove("hidden");
    }

    function hideLoginModal() {
        loginModal.classList.add("hidden");
        loginError.classList.add("hidden");
        loginError.innerText = "";
    }

    function updateAgentUI() {
        if (!currentAgent) return;
        const initials = currentAgent.full_name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
        agentAvatarBtn.innerText = initials || "CS";
        agentAvatarBtn.title = `${currentAgent.full_name} (${currentAgent.role})`;

        document.getElementById("popover-agent-name").innerText = currentAgent.full_name;
        document.getElementById("popover-agent-email").innerText = currentAgent.email;
        const roleBadge = document.getElementById("popover-agent-role");
        roleBadge.innerText = currentAgent.role;
        if (currentAgent.role === "ADMIN") {
            roleBadge.className = "inline-block mt-2 px-2 py-0.5 bg-[#fef3c7] text-[#92400e] text-[10px] font-bold rounded-full";
        } else {
            roleBadge.className = "inline-block mt-2 px-2 py-0.5 bg-[#e0f2fe] text-[#0369a1] text-[10px] font-bold rounded-full";
        }
    }

    // Login Form Submit
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-password").value;
        const btnSubmit = document.getElementById("btn-submit-login");

        btnSubmit.disabled = true;
        btnSubmit.innerText = "Memproses...";
        loginError.classList.add("hidden");

        try {
            const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            if (res.ok) {
                const data = await res.json();
                authToken = data.access_token;
                localStorage.setItem("ciheul_agent_token", authToken);
                currentAgent = data;
                updateAgentUI();
                hideLoginModal();
                loadTickets();
                connectGlobalAgentWS();
            } else {
                const errData = await res.json().catch(() => ({}));
                loginError.innerText = errData.detail || "Email atau kata sandi tidak cocok.";
                loginError.classList.remove("hidden");
            }
        } catch (err) {
            loginError.innerText = "Gagal menghubungi server. Periksa koneksi backend.";
            loginError.classList.remove("hidden");
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerText = "Masuk";
        }
    });

    // Preset helper buttons
    btnFillCs.addEventListener("click", () => {
        document.getElementById("login-email").value = "cs@ciheul.com";
        document.getElementById("login-password").value = "cs123";
    });

    btnFillAdmin.addEventListener("click", () => {
        document.getElementById("login-email").value = "admin@ciheul.com";
        document.getElementById("login-password").value = "admin123";
    });

    // Avatar Popover Toggle
    agentAvatarBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        agentPopover.classList.toggle("hidden");
    });

    document.addEventListener("click", (e) => {
        if (!agentPopover.contains(e.target) && e.target !== agentAvatarBtn) {
            agentPopover.classList.add("hidden");
        }
    });

    btnLogout.addEventListener("click", () => {
        authToken = null;
        currentAgent = null;
        localStorage.removeItem("ciheul_agent_token");
        if (globalSocket) { globalSocket.close(); globalSocket = null; }
        if (roomSocket) { roomSocket.close(); roomSocket = null; }
        agentPopover.classList.add("hidden");
        showLoginModal();
    });

    btnSwitchAccount.addEventListener("click", () => {
        agentPopover.classList.add("hidden");
        showLoginModal();
    });

    // 2. Global WebSocket Channel (Authenticated with JWT)
    function connectGlobalAgentWS() {
        if (!authToken) return;
        if (globalSocket && globalSocket.readyState === WebSocket.OPEN) return;

        globalSocket = new WebSocket(`${WS_BASE}/ws/agents`);

        globalSocket.onopen = () => {
            // In-band authentication handshake - zero token in URL query string
            globalSocket.send(JSON.stringify({ event: "auth", token: authToken }));
            // Immediate sync of tickets and counters upon connect or reconnect
            loadTickets();

            const hb = setInterval(() => {
                if (globalSocket && globalSocket.readyState === WebSocket.OPEN) {
                    globalSocket.send(JSON.stringify({ event: "ping" }));
                } else {
                    clearInterval(hb);
                }
            }, 15000);
        };

        globalSocket.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.event === "ticket_escalated" || msg.event === "ticket_claimed" || msg.event === "ticket_resolved" || msg.event === "ticket_message_activity") {
                    loadTickets();
                    if (activeTicket && msg.data && msg.data.ticket_id === activeTicket.id) {
                        loadCopilotAnalysis(activeTicket.id);
                    }
                }
            } catch (e) {
                console.error(e);
            }
        };

        globalSocket.onclose = () => {
            if (authToken) {
                setTimeout(connectGlobalAgentWS, 4000);
            }
        };
    }

    // 3. Load Tickets List
    async function loadTickets() {
        if (!authToken) return;
        try {
            const res = await fetch(`${API_BASE}/api/v1/tickets`, {
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                allTickets = await res.json();
                renderConversationList();
            }
        } catch (e) {
            console.error("Failed to load tickets:", e);
        }
    }

    function renderConversationList() {
        const listEl = document.getElementById("conversation-list");
        const openBadge = document.getElementById("open-count-badge");

        const openCount = allTickets.filter(t => t.status !== "RESOLVED" && t.status !== "CLOSED").length;
        openBadge.innerText = `${openCount} Open`;

        let filtered = allTickets.filter(t => {
            if (currentFilter === "ALL") return true;
            return t.status === currentFilter;
        });

        if (filtered.length === 0) {
            listEl.innerHTML = `<div class="p-8 text-center text-xs text-[#9ca3af]">Tidak ada percakapan.</div>`;
            return;
        }

        listEl.innerHTML = "";
        filtered.forEach(t => {
            const item = document.createElement("div");
            const isSelected = activeTicket && activeTicket.id === t.id;
            item.className = `px-4 py-3 cursor-pointer transition flex items-start gap-3 border-l-2 ${
                isSelected ? "bg-[#f3f4f6] border-[#111827]" : "hover:bg-[#f9fafb] border-transparent"
            }`;

            const initials = (t.customer_name || "T").substring(0, 2).toUpperCase();
            const timeDiff = getTimeAgo(t.updated_at);
            const snippet = t.last_message || t.subject || "Memulai percakapan...";

            item.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-[#e5e7eb] text-[#374151] flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5">
                    ${initials}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-0.5">
                        <span class="font-bold text-xs text-[#111827] truncate">${escapeHtml(t.customer_name)}</span>
                        <span class="text-[11px] text-[#9ca3af] flex-shrink-0 ml-1">${timeDiff}</span>
                    </div>
                    <p class="text-xs text-[#6b7280] truncate leading-tight">${escapeHtml(snippet)}</p>
                </div>
            `;

            item.addEventListener("click", () => selectTicket(t.id));
            listEl.appendChild(item);
        });
    }

    function getTimeAgo(dateStr) {
        const diffMs = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diffMs / 60000);
        if (mins < 1) return "now";
        if (mins < 60) return `${mins}m`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h`;
        return `${Math.floor(hrs / 24)}d`;
    }

    // 4. Select Ticket & Open Room
    async function selectTicket(ticketId) {
        if (!authToken) return;
        try {
            const res = await fetch(`${API_BASE}/api/v1/tickets/${ticketId}`, {
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                activeTicket = await res.json();
                renderConversationList();
                renderActiveConversation();
                connectRoomWebSocket(activeTicket.id);
                loadCopilotAnalysis(activeTicket.id);
            }
        } catch (e) {
            console.error(e);
        }
    }

    function renderActiveConversation() {
        const nameEl = document.getElementById("convo-customer-name");
        const statusPill = document.getElementById("convo-status-pill");
        const actionsEl = document.getElementById("convo-actions");
        const composer = document.getElementById("composer-input");
        const sendBtn = document.getElementById("btn-send-reply");
        const closeBtn = document.getElementById("btn-close-ticket");

        nameEl.innerText = activeTicket.customer_name;
        statusPill.classList.remove("hidden");

        if (activeTicket.status === "WAITING_AGENT") {
            statusPill.innerText = "Waiting";
            statusPill.className = "px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#fef3c7] text-[#92400e]";
            btnClaimTicket.classList.remove("hidden");
        } else if (activeTicket.status === "AGENT_ACTIVE") {
            statusPill.innerText = "Assigned";
            statusPill.className = "px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#e0f2fe] text-[#0369a1]";
            btnClaimTicket.classList.add("hidden");
        } else if (activeTicket.status === "RESOLVED" || activeTicket.status === "CLOSED") {
            statusPill.innerText = "Closed";
            statusPill.className = "px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#f3f4f6] text-[#4b5563]";
            btnClaimTicket.classList.add("hidden");
        } else {
            statusPill.innerText = "AI Bot";
            statusPill.className = "px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#f5f3ff] text-[#5b21b6]";
            btnClaimTicket.classList.remove("hidden");
        }

        actionsEl.classList.remove("hidden");
        const isClosed = activeTicket.status === "RESOLVED" || activeTicket.status === "CLOSED";
        closeBtn.style.display = isClosed ? "none" : "flex";

        composer.disabled = isClosed;
        sendBtn.disabled = isClosed;
        if (!isClosed) composer.focus();

        const feed = document.getElementById("convo-feed");
        feed.innerHTML = "";

        activeTicket.messages.forEach(m => {
            appendConvoMessage(m.sender_type, m.sender_name, m.content, m.created_at);
        });

        feed.scrollTop = feed.scrollHeight;
    }

    function appendConvoMessage(senderType, senderName, content, timeStr) {
        const feed = document.getElementById("convo-feed");
        const msgDiv = document.createElement("div");

        if (senderType === "SYSTEM") {
            msgDiv.className = "text-center my-3 text-[11px] text-[#9ca3af]";
            msgDiv.innerText = content.trim();
            feed.appendChild(msgDiv);
            feed.scrollTop = feed.scrollHeight;
            return;
        }

        const isCustomer = senderType === "CUSTOMER";
        const align = isCustomer ? "justify-start" : "justify-end";
        const bubbleStyle = isCustomer 
            ? "bg-[#f3f4f6] text-[#111827] rounded-2xl rounded-bl-sm"
            : "bg-[#0284c7] text-white rounded-2xl rounded-br-sm";

        const time = timeStr ? new Date(timeStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        msgDiv.className = `flex ${align}`;
        msgDiv.innerHTML = `
            <div class="max-w-[75%] px-4 py-2.5 text-xs leading-relaxed ${bubbleStyle}">
                <div class="font-bold text-[10px] mb-1 opacity-70">${escapeHtml(senderName)}</div>
                <div class="whitespace-pre-wrap">${escapeHtml(content)}</div>
                <div class="text-[9px] text-right mt-1 opacity-60">${time}</div>
            </div>
        `;

        feed.appendChild(msgDiv);
        feed.scrollTop = feed.scrollHeight;
    }

    // 5. Connect 1-on-1 Room WebSocket (Authenticated with JWT)
    function connectRoomWebSocket(ticketId) {
        if (!authToken) return;
        if (roomSocket) {
            roomSocket.onclose = null; // Detach old reconnect handler to avoid stale reconnections
            roomSocket.close();
        }
        roomSocket = new WebSocket(`${WS_BASE}/ws/ticket/${ticketId}`);

        roomSocket.onopen = () => {
            // In-band authentication handshake - zero token in URL query string
            roomSocket.send(JSON.stringify({ event: "auth", token: authToken }));

            // Sync any messages missed during disconnection
            let lastId = null;
            if (activeTicket && Array.isArray(activeTicket.messages) && activeTicket.messages.length > 0) {
                const lastMsg = activeTicket.messages[activeTicket.messages.length - 1];
                if (lastMsg && lastMsg.id) lastId = lastMsg.id;
            }
            roomSocket.send(JSON.stringify({
                event: "sync_missed",
                last_message_id: lastId
            }));
        };

        roomSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.event === "new_message") {
                    if (activeTicket) {
                        if (!activeTicket.messages) activeTicket.messages = [];
                        const alreadyExists = activeTicket.messages.some(m => m.id && data.id && m.id === data.id);
                        if (!alreadyExists) {
                            activeTicket.messages.push(data);
                            appendConvoMessage(data.sender_type, data.sender_name, data.content, data.created_at);
                            loadCopilotAnalysis(ticketId);
                        }
                    } else {
                        appendConvoMessage(data.sender_type, data.sender_name, data.content, data.created_at);
                    }
                } else if (data.event === "sync_result" && Array.isArray(data.messages)) {
                    let hasNew = false;
                    if (activeTicket) {
                        if (!activeTicket.messages) activeTicket.messages = [];
                        data.messages.forEach(m => {
                            const alreadyExists = activeTicket.messages.some(existing => existing.id && m.id && existing.id === m.id);
                            if (!alreadyExists) {
                                activeTicket.messages.push(m);
                                appendConvoMessage(m.sender_type, m.sender_name, m.content, m.created_at);
                                hasNew = true;
                            }
                        });
                        if (hasNew) {
                            loadCopilotAnalysis(ticketId);
                        }
                    }
                } else if (data.event === "ticket_claimed" || data.event === "ticket_resolved" || data.event === "ticket_escalated") {
                    selectTicket(ticketId);
                }
            } catch (e) {
                console.error(e);
            }
        };

        roomSocket.onclose = () => {
            // Reconnect room WebSocket if this ticket is still the active open ticket
            if (authToken && activeTicket && activeTicket.id === ticketId) {
                setTimeout(() => {
                    if (authToken && activeTicket && activeTicket.id === ticketId) {
                        connectRoomWebSocket(ticketId);
                    }
                }, 3000);
            }
        };
    }

    // 6. Copilot Assistant Integration
    async function loadCopilotAnalysis(ticketId) {
        if (!authToken) return;
        try {
            const res = await fetch(`${API_BASE}/api/v1/copilot/${ticketId}/analyze`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById("copilot-summary-text").innerText = data.summary;
                document.getElementById("copilot-draft-text").innerText = data.draft_reply;
                latestDraftReply = data.draft_reply;

                const sendBtn = document.getElementById("btn-copilot-send");
                sendBtn.innerText = `Send to ${data.customer_name}`;

                const followUpsEl = document.getElementById("copilot-followups");
                followUpsEl.innerHTML = "";
                data.follow_ups.forEach((act, idx) => {
                    const row = document.createElement("div");
                    row.className = "text-xs text-[#4b5563] bg-white p-2.5 rounded-lg border border-[#e5e7eb]";
                    row.innerText = `${idx + 1}. ${act}`;
                    followUpsEl.appendChild(row);
                });
            }
        } catch (e) {
            console.error("Copilot analysis error:", e);
        }
    }

    // Dispatch Copilot Draft directly to customer
    document.getElementById("btn-copilot-send").addEventListener("click", () => {
        if (!latestDraftReply || !roomSocket) return;
        roomSocket.send(JSON.stringify({
            event: "send_message",
            content: latestDraftReply
        }));
    });

    // Ask Copilot custom question
    async function askCopilot() {
        const input = document.getElementById("copilot-ask-input");
        const q = input.value.trim();
        if (!q || !activeTicket || !authToken) return;
        input.value = "";

        const summaryBox = document.getElementById("copilot-summary-text");
        summaryBox.innerText = "Copilot sedang menganalisis basis pengetahuan...";

        try {
            const res = await fetch(`${API_BASE}/api/v1/copilot/${activeTicket.id}/ask`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify({ question: q })
            });
            if (res.ok) {
                const data = await res.json();
                summaryBox.innerText = data.answer;
            }
        } catch (e) {
            console.error(e);
        }
    }

    document.getElementById("btn-copilot-ask").addEventListener("click", askCopilot);
    document.getElementById("copilot-ask-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter") askCopilot();
    });

    // 7. Manual Send Reply
    function sendManualReply() {
        const composer = document.getElementById("composer-input");
        const text = composer.value.trim();
        if (!text || !activeTicket || !roomSocket) return;
        composer.value = "";

        roomSocket.send(JSON.stringify({
            event: "send_message",
            content: text
        }));
    }

    document.getElementById("btn-send-reply").addEventListener("click", sendManualReply);
    document.getElementById("composer-input").addEventListener("keydown", (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            sendManualReply();
        }
    });

    // 8. Claim Ticket Action
    btnClaimTicket.addEventListener("click", async () => {
        if (!activeTicket || !authToken) return;
        try {
            btnClaimTicket.disabled = true;
            btnClaimTicket.innerText = "Claiming...";
            const res = await fetch(`${API_BASE}/api/v1/tickets/${activeTicket.id}/claim`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                await selectTicket(activeTicket.id);
                loadTickets();
            }
        } catch (e) {
            console.error(e);
        } finally {
            btnClaimTicket.disabled = false;
            btnClaimTicket.innerText = "Claim Ticket";
        }
    });

    // 9. Close / Resolve Ticket
    document.getElementById("btn-close-ticket").addEventListener("click", async () => {
        if (!activeTicket || !authToken) return;
        try {
            const res = await fetch(`${API_BASE}/api/v1/tickets/${activeTicket.id}/resolve`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                selectTicket(activeTicket.id);
                loadTickets();
            }
        } catch (e) {
            console.error(e);
        }
    });

    // 10. Details Drawer Handlers
    btnDetailsDrawer.addEventListener("click", () => {
        if (!activeTicket) return;
        document.getElementById("dt-ticket-id").innerText = activeTicket.id;
        document.getElementById("dt-customer-name").innerText = activeTicket.customer_name || "-";
        document.getElementById("dt-customer-email").innerText = activeTicket.customer_email || "Tidak ada email";
        document.getElementById("dt-subject").innerText = activeTicket.subject || "-";
        document.getElementById("dt-status").innerText = activeTicket.status || "-";
        document.getElementById("dt-category").innerText = activeTicket.category || "-";
        document.getElementById("dt-agent-name").innerText = activeTicket.agent_name || "Belum ditugaskan";
        document.getElementById("dt-created-at").innerText = new Date(activeTicket.created_at).toLocaleString();

        detailsDrawer.classList.remove("hidden");
    });

    btnCloseDetails.addEventListener("click", () => detailsDrawer.classList.add("hidden"));
    detailsBackdrop.addEventListener("click", () => detailsDrawer.classList.add("hidden"));

    // 11. Macro Modal Handlers
    btnQuickMacro.addEventListener("click", () => macroModal.classList.remove("hidden"));
    btnCloseMacro.addEventListener("click", () => macroModal.classList.add("hidden"));
    macroBackdrop.addEventListener("click", () => macroModal.classList.add("hidden"));

    document.querySelectorAll(".macro-item").forEach(item => {
        item.addEventListener("click", () => {
            const text = item.dataset.text;
            const composer = document.getElementById("composer-input");
            composer.value = text;
            composer.focus();
            macroModal.classList.add("hidden");
        });
    });

    // 12. Filter Buttons
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filter-btn").forEach(b => {
                b.className = "filter-btn text-[#6b7280] hover:text-[#111827]";
            });
            btn.className = "filter-btn text-[#111827] font-semibold";
            currentFilter = btn.dataset.status;
            renderConversationList();
        });
    });

    function escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.innerText = str;
        return div.innerHTML;
    }

    // Initialize
    checkAuthentication();
})();
