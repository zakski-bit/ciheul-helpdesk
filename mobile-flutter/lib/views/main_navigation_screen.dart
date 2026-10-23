import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/constants.dart';
import '../models/ticket.dart';
import '../models/knowledge_base.dart';
import 'chat_detail_screen.dart';
import 'login_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  final String token;
  final String agentName;

  const MainNavigationScreen({
    super.key,
    required this.token,
    required this.agentName,
  });

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentTabIndex = 0;

  // Tickets State
  List<Ticket> _tickets = [];
  bool _isLoadingTickets = true;
  String _inboxFilter = "ALL";
  String _ticketSearchQuery = "";
  String _ticketStatusFilter = "ALL";
  WebSocketChannel? _agentChannel;

  // Knowledge Base State
  List<KnowledgeBaseArticle> _kbArticles = [];
  bool _isLoadingKB = true;
  String _kbCategoryFilter = "ALL";
  String _kbSearchQuery = "";

  @override
  void initState() {
    super.initState();
    _fetchTickets();
    _fetchKnowledgeBase();
    _connectAgentWebSocket();
  }

  @override
  void dispose() {
    _agentChannel?.sink.close();
    super.dispose();
  }

  // 1. WebSocket Channel for Realtime Events
  void _connectAgentWebSocket() {
    try {
      final wsUrl = Uri.parse("${AppConstants.wsBaseUrl}/ws/agents");
      _agentChannel = WebSocketChannel.connect(wsUrl);

      // In-band authentication handshake - zero token in URL query string
      _agentChannel!.sink.add(jsonEncode({
        "event": "auth",
        "token": widget.token,
      }));

      _agentChannel!.stream.listen(
        (message) {
          try {
            final data = jsonDecode(message);
            final event = data['event'];
            if (event == 'ticket_escalated') {
              _fetchTickets();
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    backgroundColor: const Color(0xFF92400E),
                    behavior: SnackBarBehavior.floating,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    content: Row(
                      children: const [
                        Icon(Icons.mark_email_unread_outlined, color: Colors.amberAccent, size: 18),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            "Tiket eskalasi baru dialihkan ke antrean CS",
                            style: TextStyle(color: Colors.white, fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                    duration: const Duration(seconds: 4),
                  ),
                );
              }
            } else if (event == 'ticket_claimed' || event == 'ticket_resolved' || event == 'ticket_message_activity') {
              _fetchTickets();
            }
          } catch (_) {}
        },
        onError: (_) {
          Future.delayed(const Duration(seconds: 4), _connectAgentWebSocket);
        },
        onDone: () {
          Future.delayed(const Duration(seconds: 4), _connectAgentWebSocket);
        },
      );
    } catch (_) {}
  }

  // 2. Fetch Tickets from API
  Future<void> _fetchTickets() async {
    setState(() => _isLoadingTickets = true);
    try {
      final res = await http.get(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/tickets"),
        headers: {"Authorization": "Bearer ${widget.token}"},
      );
      if (res.statusCode == 200) {
        final List data = jsonDecode(res.body);
        if (mounted) {
          setState(() {
            _tickets = data.map((json) => Ticket.fromJson(json)).toList();
            _isLoadingTickets = false;
          });
        }
      } else {
        if (mounted) setState(() => _isLoadingTickets = false);
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingTickets = false);
    }
  }

  // 3. Fetch Knowledge Base from API
  Future<void> _fetchKnowledgeBase() async {
    setState(() => _isLoadingKB = true);
    try {
      final res = await http.get(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/knowledge-base"),
      );
      if (res.statusCode == 200) {
        final List data = jsonDecode(res.body);
        if (mounted) {
          setState(() {
            _kbArticles = data.map((json) => KnowledgeBaseArticle.fromJson(json)).toList();
            _isLoadingKB = false;
          });
        }
      } else {
        if (mounted) setState(() => _isLoadingKB = false);
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingKB = false);
    }
  }

  // Filtered Tickets for Inbox
  List<Ticket> get _filteredInboxTickets {
    if (_inboxFilter == "ALL") return _tickets;
    return _tickets.where((t) => t.status == _inboxFilter).toList();
  }

  // Filtered Tickets for Directory Tab
  List<Ticket> get _filteredDirectoryTickets {
    return _tickets.where((t) {
      final matchesStatus = _ticketStatusFilter == "ALL" || t.status == _ticketStatusFilter;
      final q = _ticketSearchQuery.toLowerCase();
      final matchesSearch = q.isEmpty ||
          t.customerName.toLowerCase().contains(q) ||
          t.subject.toLowerCase().contains(q) ||
          t.id.toLowerCase().contains(q) ||
          t.category.toLowerCase().contains(q);
      return matchesStatus && matchesSearch;
    }).toList();
  }

  // Filtered Articles for Knowledge Base Tab
  List<KnowledgeBaseArticle> get _filteredKBArticles {
    return _kbArticles.where((article) {
      final matchesCat = _kbCategoryFilter == "ALL" || article.category.toUpperCase() == _kbCategoryFilter;
      final q = _kbSearchQuery.toLowerCase();
      final matchesSearch = q.isEmpty ||
          article.question.toLowerCase().contains(q) ||
          article.answer.toLowerCase().contains(q) ||
          article.keywords.toLowerCase().contains(q);
      return matchesCat && matchesSearch;
    }).toList();
  }

  void _openChat(Ticket ticket) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ChatDetailScreen(
          ticketId: ticket.id,
          token: widget.token,
          agentName: widget.agentName,
          customerName: ticket.customerName,
          subject: ticket.subject,
          initialStatus: ticket.status,
        ),
      ),
    );
    _fetchTickets();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.bgDark,
      appBar: _buildAppBar(),
      body: IndexedStack(
        index: _currentTabIndex,
        children: [
          _buildInboxTab(),
          _buildTicketsDirectoryTab(),
          _buildKnowledgeBaseTab(),
          _buildSettingsTab(),
        ],
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  // --- TOP APP BAR ---
  PreferredSizeWidget _buildAppBar() {
    String title = "Inbox Percakapan";
    String subtitle = "Antrean live obrolan pelanggan";
    if (_currentTabIndex == 1) {
      title = "Direktori Tiket";
      subtitle = "Manajemen data seluruh tiket kendala";
    } else if (_currentTabIndex == 2) {
      title = "Basis Pengetahuan";
      subtitle = "15 Panduan dan solusi resmi CIHEUL";
    } else if (_currentTabIndex == 3) {
      title = "Pengaturan & Diagnostik";
      subtitle = "Profil agen & status infrastruktur";
    }

    return AppBar(
      backgroundColor: AppConstants.cardDark,
      elevation: 0,
      leading: Padding(
        padding: const EdgeInsets.only(left: 12.0, top: 10.0, bottom: 10.0, right: 4.0),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.asset(
            'assets/ciheul-logo.png',
            fit: BoxFit.contain,
          ),
        ),
      ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          Text(
            subtitle,
            style: const TextStyle(fontSize: 11, color: AppConstants.textMuted),
          ),
        ],
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh, color: AppConstants.primaryBlue, size: 20),
          tooltip: "Segarkan Data",
          onPressed: () {
            if (_currentTabIndex == 2) {
              _fetchKnowledgeBase();
            } else {
              _fetchTickets();
            }
          },
        ),
      ],
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(color: AppConstants.borderDark, height: 1),
      ),
    );
  }

  // --- BOTTOM NAVIGATION BAR ---
  Widget _buildBottomNav() {
    return Container(
      decoration: const BoxDecoration(
        color: AppConstants.cardDark,
        border: Border(top: BorderSide(color: AppConstants.borderDark)),
      ),
      child: SafeArea(
        child: BottomNavigationBar(
          currentIndex: _currentTabIndex,
          onTap: (idx) => setState(() => _currentTabIndex = idx),
          backgroundColor: AppConstants.cardDark,
          selectedItemColor: AppConstants.primaryBlue,
          unselectedItemColor: AppConstants.textMuted,
          selectedFontSize: 11,
          unselectedFontSize: 11,
          type: BottomNavigationBarType.fixed,
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.forum_outlined, size: 20),
              activeIcon: Icon(Icons.forum, size: 20),
              label: "Inbox",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.view_list_outlined, size: 20),
              activeIcon: Icon(Icons.view_list, size: 20),
              label: "Tiket",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.menu_book_outlined, size: 20),
              activeIcon: Icon(Icons.menu_book, size: 20),
              label: "Solusi KB",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.tune_outlined, size: 20),
              activeIcon: Icon(Icons.tune, size: 20),
              label: "Pengaturan",
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // TAB 1: INBOX CONVERSATIONS
  // ==========================================
  Widget _buildInboxTab() {
    final waitingCount = _tickets.where((t) => t.status == "WAITING_AGENT").length;
    final activeCount = _tickets.where((t) => t.status == "AGENT_ACTIVE").length;

    return Column(
      children: [
        // Counters Banner
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          color: const Color(0xFF0F172A),
          child: Row(
            children: [
              _buildBadgeCount("Menunggu", waitingCount, const Color(0xFFFEF3C7), const Color(0xFF92400E)),
              const SizedBox(width: 8),
              _buildBadgeCount("Ditangani CS", activeCount, const Color(0xFFE0F2FE), const Color(0xFF0369A1)),
              const Spacer(),
              Text(
                "Total ${_tickets.length} Tiket",
                style: const TextStyle(color: AppConstants.textMuted, fontSize: 11),
              ),
            ],
          ),
        ),

        // Filter Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: AppConstants.cardDark,
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterChip("Semua", "ALL", _inboxFilter, (v) => setState(() => _inboxFilter = v)),
                _buildFilterChip("Menunggu CS", "WAITING_AGENT", _inboxFilter, (v) => setState(() => _inboxFilter = v)),
                _buildFilterChip("CS Aktif", "AGENT_ACTIVE", _inboxFilter, (v) => setState(() => _inboxFilter = v)),
                _buildFilterChip("Selesai", "RESOLVED", _inboxFilter, (v) => setState(() => _inboxFilter = v)),
              ],
            ),
          ),
        ),

        Expanded(
          child: _isLoadingTickets
              ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
              : _filteredInboxTickets.isEmpty
                  ? _buildEmptyState("Tidak ada percakapan pada filter ini.")
                  : RefreshIndicator(
                      onRefresh: _fetchTickets,
                      color: AppConstants.primaryBlue,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _filteredInboxTickets.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 10),
                        itemBuilder: (ctx, idx) {
                          final ticket = _filteredInboxTickets[idx];
                          return _buildInboxTicketCard(ticket);
                        },
                      ),
                    ),
        ),
      ],
    );
  }

  Widget _buildBadgeCount(String label, int count, Color bg, Color text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        "$count $label",
        style: TextStyle(color: text, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildInboxTicketCard(Ticket ticket) {
    final statusColor = AppConstants.getStatusColor(ticket.status);
    final statusLabel = AppConstants.getStatusLabel(ticket.status);
    final formattedTime = DateFormat('HH:mm').format(ticket.updatedAt);
    final initials = ticket.customerName.isNotEmpty
        ? ticket.customerName.substring(0, ticket.customerName.length >= 2 ? 2 : 1).toUpperCase()
        : "PL";

    return InkWell(
      onTap: () => _openChat(ticket),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppConstants.cardDark,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppConstants.borderDark),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: const Color(0xFF334155),
              child: Text(
                initials,
                style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          ticket.customerName,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppConstants.textLight),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Text(
                        formattedTime,
                        style: const TextStyle(fontSize: 10.5, color: AppConstants.textMuted),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    ticket.subject,
                    style: const TextStyle(fontSize: 12, color: Color(0xFFCBD5E1), height: 1.3),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: statusColor.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: statusColor.withValues(alpha: 0.3)),
                        ),
                        child: Text(
                          statusLabel,
                          style: TextStyle(color: statusColor, fontSize: 9.5, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        ticket.category,
                        style: const TextStyle(color: AppConstants.textMuted, fontSize: 10, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // TAB 2: TICKETS DIRECTORY (TABLE/CATALOG)
  // ==========================================
  Widget _buildTicketsDirectoryTab() {
    return Column(
      children: [
        // Search & Filter Box
        Container(
          padding: const EdgeInsets.all(16),
          color: AppConstants.cardDark,
          child: Column(
            children: [
              TextField(
                onChanged: (val) => setState(() => _ticketSearchQuery = val),
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: InputDecoration(
                  hintText: "Cari ID tiket, nama pelanggan, subjek...",
                  hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                  prefixIcon: const Icon(Icons.search, size: 18, color: AppConstants.textMuted),
                  filled: true,
                  fillColor: AppConstants.bgDark,
                  contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderDark),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderDark),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip("Semua", "ALL", _ticketStatusFilter, (v) => setState(() => _ticketStatusFilter = v)),
                    _buildFilterChip("Menunggu", "WAITING_AGENT", _ticketStatusFilter, (v) => setState(() => _ticketStatusFilter = v)),
                    _buildFilterChip("Aktif", "AGENT_ACTIVE", _ticketStatusFilter, (v) => setState(() => _ticketStatusFilter = v)),
                    _buildFilterChip("Selesai", "RESOLVED", _ticketStatusFilter, (v) => setState(() => _ticketStatusFilter = v)),
                  ],
                ),
              ),
            ],
          ),
        ),

        Expanded(
          child: _isLoadingTickets
              ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
              : _filteredDirectoryTickets.isEmpty
                  ? _buildEmptyState("Tidak ada tiket yang cocok dengan pencarian.")
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _filteredDirectoryTickets.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (ctx, idx) {
                        final t = _filteredDirectoryTickets[idx];
                        return _buildDirectoryCard(t);
                      },
                    ),
        ),
      ],
    );
  }

  Widget _buildDirectoryCard(Ticket t) {
    final statusColor = AppConstants.getStatusColor(t.status);
    final statusLabel = AppConstants.getStatusLabel(t.status);
    final dateStr = DateFormat('dd MMM yyyy, HH:mm').format(t.updatedAt);

    Color priorityColor = Colors.grey;
    if (t.priority == "HIGH" || t.priority == "URGENT") priorityColor = Colors.redAccent;
    if (t.priority == "MEDIUM") priorityColor = Colors.amber;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppConstants.cardDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppConstants.borderDark),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppConstants.borderDark,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  "#${t.id.substring(0, t.id.length >= 8 ? 8 : t.id.length)}",
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 10, color: Colors.white70),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: priorityColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  t.priority,
                  style: TextStyle(color: priorityColor, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            t.customerName,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppConstants.textLight),
          ),
          const SizedBox(height: 4),
          Text(
            t.subject,
            style: const TextStyle(fontSize: 12.5, color: Color(0xFFCBD5E1)),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: statusColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      statusLabel,
                      style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    t.category,
                    style: const TextStyle(color: AppConstants.textMuted, fontSize: 10.5),
                  ),
                ],
              ),
              Text(
                dateStr,
                style: const TextStyle(color: AppConstants.textMuted, fontSize: 10),
              ),
            ],
          ),
          const Divider(color: AppConstants.borderDark, height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton.icon(
                onPressed: () => _openChat(t),
                icon: const Icon(Icons.chat_bubble_outline, size: 15, color: AppConstants.primaryBlue),
                label: const Text(
                  "Buka di Chat",
                  style: TextStyle(color: AppConstants.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==========================================
  // TAB 3: KNOWLEDGE BASE (15 SOLUSI RESMI)
  // ==========================================
  Widget _buildKnowledgeBaseTab() {
    return Column(
      children: [
        // Search & Filter Box
        Container(
          padding: const EdgeInsets.all(16),
          color: AppConstants.cardDark,
          child: Column(
            children: [
              TextField(
                onChanged: (val) => setState(() => _kbSearchQuery = val),
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: InputDecoration(
                  hintText: "Cari pertanyaan atau solusi KB...",
                  hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                  prefixIcon: const Icon(Icons.search, size: 18, color: AppConstants.textMuted),
                  filled: true,
                  fillColor: AppConstants.bgDark,
                  contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderDark),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderDark),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip("Semua", "ALL", _kbCategoryFilter, (v) => setState(() => _kbCategoryFilter = v)),
                    _buildFilterChip("Akun & Akses", "ACCOUNT", _kbCategoryFilter, (v) => setState(() => _kbCategoryFilter = v)),
                    _buildFilterChip("Tagihan", "BILLING", _kbCategoryFilter, (v) => setState(() => _kbCategoryFilter = v)),
                    _buildFilterChip("Teknis & API", "TECHNICAL", _kbCategoryFilter, (v) => setState(() => _kbCategoryFilter = v)),
                    _buildFilterChip("Umum", "GENERAL", _kbCategoryFilter, (v) => setState(() => _kbCategoryFilter = v)),
                  ],
                ),
              ),
            ],
          ),
        ),

        // Count Banner
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: const Color(0xFF0F172A),
          child: Row(
            children: [
              const Icon(Icons.verified_outlined, size: 14, color: AppConstants.primaryBlue),
              const SizedBox(width: 6),
              Text(
                "Menampilkan ${_filteredKBArticles.length} artikel solusi resmi CIHEUL",
                style: const TextStyle(color: AppConstants.textMuted, fontSize: 11),
              ),
            ],
          ),
        ),

        Expanded(
          child: _isLoadingKB
              ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
              : _filteredKBArticles.isEmpty
                  ? _buildEmptyState("Tidak ada artikel solusi yang cocok.")
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _filteredKBArticles.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (ctx, idx) {
                        final article = _filteredKBArticles[idx];
                        return _buildKBCard(article);
                      },
                    ),
        ),
      ],
    );
  }

  Widget _buildKBCard(KnowledgeBaseArticle article) {
    return Container(
      decoration: BoxDecoration(
        color: AppConstants.cardDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppConstants.borderDark),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppConstants.primaryBlue.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      article.category,
                      style: const TextStyle(color: AppConstants.primaryBlue, fontSize: 9.5, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                article.question,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5, color: AppConstants.textLight),
              ),
            ],
          ),
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppConstants.bgDark,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppConstants.borderDark),
                    ),
                    child: Text(
                      article.answer,
                      style: const TextStyle(fontSize: 12.5, color: Color(0xFFCBD5E1), height: 1.45),
                    ),
                  ),
                  if (article.keywords.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text(
                      "Kata Kunci: ${article.keywords}",
                      style: const TextStyle(fontSize: 10.5, color: AppConstants.textMuted),
                    ),
                  ],
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      ElevatedButton.icon(
                        onPressed: () {
                          Clipboard.setData(ClipboardData(text: article.answer));
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              backgroundColor: const Color(0xFF065F46),
                              content: const Text("Jawaban KB berhasil disalin ke clipboard!"),
                              duration: const Duration(seconds: 2),
                            ),
                          );
                        },
                        icon: const Icon(Icons.copy, size: 14, color: Colors.white),
                        label: const Text(
                          "Salin Solusi",
                          style: TextStyle(fontSize: 11.5, color: Colors.white, fontWeight: FontWeight.bold),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1E293B),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                            side: const BorderSide(color: AppConstants.borderDark),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // TAB 4: SETTINGS & DIAGNOSTICS
  // ==========================================
  Widget _buildSettingsTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Profile Card
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: AppConstants.cardDark,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppConstants.borderDark),
          ),
          child: Row(
            children: [
              CircleAvatar(
                radius: 28,
                backgroundColor: AppConstants.primaryBlue,
                child: Text(
                  widget.agentName.substring(0, widget.agentName.length >= 2 ? 2 : 1).toUpperCase(),
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.agentName,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 2),
                    const Text(
                      "cs@ciheul.com",
                      style: TextStyle(fontSize: 12, color: AppConstants.textMuted),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0284C7).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        "CUSTOMER SUPPORT",
                        style: TextStyle(color: AppConstants.primaryBlue, fontSize: 9.5, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 16),

        // System Diagnostics Card
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: AppConstants.cardDark,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppConstants.borderDark),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Diagnostik Layanan Sistem",
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 14),
              _buildDiagRow("Server API Host", AppConstants.apiBaseUrl, Colors.greenAccent),
              _buildDiagRow("WebSocket Gateway", "${AppConstants.wsBaseUrl}/ws/agents", Colors.greenAccent),
              _buildDiagRow("Backend Framework", "FastAPI 0.115 (Python 3.10)", Colors.greenAccent),
              _buildDiagRow("Database Mesin", "SQLite Relasional", Colors.greenAccent),
              _buildDiagRow("Enkripsi & Masking", "PII Redaction Aktif (NIK/Card/Telp)", Colors.greenAccent),
              _buildDiagRow("SLA Standar", "Maksimal 15 Menit Respon", Colors.amberAccent),
            ],
          ),
        ),

        const SizedBox(height: 16),

        // Host Switcher Action
        Container(
          decoration: BoxDecoration(
            color: AppConstants.cardDark,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppConstants.borderDark),
          ),
          child: ListTile(
            leading: const Icon(Icons.dns_outlined, color: AppConstants.primaryBlue),
            title: const Text("Ubah Server Host & Port", style: TextStyle(color: Colors.white, fontSize: 13.5)),
            subtitle: Text(AppConstants.host, style: const TextStyle(color: AppConstants.textMuted, fontSize: 11)),
            trailing: const Icon(Icons.chevron_right, color: AppConstants.textMuted),
            onTap: _showHostDialog,
          ),
        ),

        const SizedBox(height: 24),

        // Logout Button
        ElevatedButton.icon(
          onPressed: _confirmLogout,
          icon: const Icon(Icons.logout, size: 16, color: Colors.redAccent),
          label: const Text(
            "Keluar dari Workspace",
            style: TextStyle(color: Colors.redAccent, fontSize: 13, fontWeight: FontWeight.bold),
          ),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.red.withValues(alpha: 0.1),
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: BorderSide(color: Colors.red.withValues(alpha: 0.3)),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDiagRow(String label, String value, Color statusColor) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppConstants.textMuted, fontSize: 12)),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              value,
              style: TextStyle(color: statusColor, fontSize: 11.5, fontWeight: FontWeight.w600),
              textAlign: TextAlign.end,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  void _showHostDialog() {
    final ctrl = TextEditingController(text: AppConstants.host);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppConstants.cardDark,
        title: const Text("Ubah Host Server", style: TextStyle(color: Colors.white, fontSize: 15)),
        content: TextField(
          controller: ctrl,
          style: const TextStyle(color: Colors.white, fontSize: 13),
          decoration: const InputDecoration(
            hintText: "Contoh: localhost:8000 atau 192.168.1.10:8000",
            hintStyle: TextStyle(color: AppConstants.textMuted, fontSize: 12),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Batal", style: TextStyle(color: AppConstants.textMuted)),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                AppConstants.host = ctrl.text.trim();
              });
              Navigator.pop(ctx);
              _fetchTickets();
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppConstants.primaryBlue),
            child: const Text("Simpan", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _confirmLogout() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppConstants.cardDark,
        title: const Text("Konfirmasi Keluar", style: TextStyle(color: Colors.white, fontSize: 15)),
        content: const Text(
          "Apakah Anda yakin ingin keluar dari workspace agen CIHEUL?",
          style: TextStyle(color: AppConstants.textMuted, fontSize: 13),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Batal", style: TextStyle(color: AppConstants.textMuted)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const LoginScreen()),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
            child: const Text("Keluar", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // --- HELPER WIDGETS ---
  Widget _buildFilterChip(String label, String value, String currentVal, Function(String) onSelect) {
    final isSelected = currentVal == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: FilterChip(
        label: Text(label),
        labelStyle: TextStyle(
          color: isSelected ? Colors.white : AppConstants.textMuted,
          fontSize: 11.5,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
        selected: isSelected,
        selectedColor: AppConstants.primaryBlue,
        backgroundColor: AppConstants.borderDark,
        onSelected: (_) => onSelect(value),
      ),
    );
  }

  Widget _buildEmptyState(String msg) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.inbox_outlined, size: 40, color: AppConstants.textMuted),
            const SizedBox(height: 12),
            Text(
              msg,
              style: const TextStyle(color: AppConstants.textMuted, fontSize: 12.5),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
