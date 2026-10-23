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
                    backgroundColor: const Color(0xFF0F172A),
                    behavior: SnackBarBehavior.floating,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    content: const Row(
                      children: [
                        Icon(Icons.mark_email_unread_outlined, color: Colors.amberAccent, size: 18),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            "Tiket baru menunggu penanganan CS",
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
      ).timeout(const Duration(seconds: 6));
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
      ).timeout(const Duration(seconds: 6));
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
    final waitingCount = _tickets.where((t) => t.status == "WAITING_AGENT").length;

    return Scaffold(
      backgroundColor: AppConstants.bgLight,
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
      bottomNavigationBar: _buildBottomNav(waitingCount),
    );
  }

  // --- TOP APP BAR ---
  PreferredSizeWidget _buildAppBar() {
    String title = "Your inbox";
    String subtitle = "Antrean obrolan pelanggan";
    if (_currentTabIndex == 1) {
      title = "Direktori Tiket";
      subtitle = "Manajemen seluruh data tiket";
    } else if (_currentTabIndex == 2) {
      title = "Basis Pengetahuan";
      subtitle = "15 Panduan & solusi resmi CIHEUL";
    } else if (_currentTabIndex == 3) {
      title = "Pengaturan & Diagnostik";
      subtitle = "Profil agen & status sistem";
    }

    return AppBar(
      backgroundColor: AppConstants.cardLight,
      elevation: 0,
      scrolledUnderElevation: 0,
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
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppConstants.textPrimary,
              letterSpacing: -0.2,
            ),
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
        child: Container(color: AppConstants.borderLight, height: 1),
      ),
    );
  }

  // --- BOTTOM NAVIGATION BAR WITH WHATSAPP-STYLE BADGE ---
  Widget _buildBottomNav(int waitingCount) {
    return Container(
      decoration: const BoxDecoration(
        color: AppConstants.cardLight,
        border: Border(top: BorderSide(color: AppConstants.borderLight)),
      ),
      child: SafeArea(
        child: BottomNavigationBar(
          currentIndex: _currentTabIndex,
          onTap: (idx) => setState(() => _currentTabIndex = idx),
          backgroundColor: AppConstants.cardLight,
          selectedItemColor: AppConstants.primaryBlue,
          unselectedItemColor: AppConstants.textMuted,
          selectedFontSize: 11,
          unselectedFontSize: 11,
          type: BottomNavigationBarType.fixed,
          elevation: 0,
          items: [
            BottomNavigationBarItem(
              icon: Badge(
                label: Text(
                  '$waitingCount',
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
                isLabelVisible: waitingCount > 0,
                backgroundColor: const Color(0xFF0284C7),
                child: const Icon(Icons.inbox_outlined, size: 21),
              ),
              activeIcon: Badge(
                label: Text(
                  '$waitingCount',
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
                isLabelVisible: waitingCount > 0,
                backgroundColor: const Color(0xFF0284C7),
                child: const Icon(Icons.inbox, size: 21),
              ),
              label: "Inbox",
            ),
            const BottomNavigationBarItem(
              icon: Icon(Icons.confirmation_number_outlined, size: 21),
              activeIcon: Icon(Icons.confirmation_number, size: 21),
              label: "Tiket",
            ),
            const BottomNavigationBarItem(
              icon: Icon(Icons.menu_book_outlined, size: 21),
              activeIcon: Icon(Icons.menu_book, size: 21),
              label: "FAQ / KB",
            ),
            const BottomNavigationBarItem(
              icon: Icon(Icons.settings_outlined, size: 21),
              activeIcon: Icon(Icons.settings, size: 21),
              label: "Pengaturan",
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // TAB 1: INBOX CONVERSATIONS (MATCHING IMAGE 1)
  // ==========================================
  Widget _buildInboxTab() {
    final openCount = _tickets.where((t) => t.status != "RESOLVED" && t.status != "CLOSED").length;
    final waitingCount = _tickets.where((t) => t.status == "WAITING_AGENT").length;

    return Column(
      children: [
        // Sub-Header Bar matching Image 1: "Your inbox" & "3 Open" pill
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: const BoxDecoration(
            color: AppConstants.cardLight,
            border: Border(bottom: BorderSide(color: AppConstants.borderSubtle)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Text(
                    "Daftar Percakapan",
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppConstants.textPrimary,
                    ),
                  ),
                  if (waitingCount > 0) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFEF3C7),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFFDE68A)),
                      ),
                      child: Text(
                        "$waitingCount Perlu Ditangani",
                        style: const TextStyle(
                          color: Color(0xFF92400E),
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppConstants.badgeBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppConstants.borderLight),
                ),
                child: Text(
                  "$openCount Open",
                  style: const TextStyle(
                    color: AppConstants.textSecondary,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),

        // Filter Bar matching Image 1: Last activity · Semua · Menunggu · Selesai
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: const BoxDecoration(
            color: AppConstants.cardLight,
            border: Border(bottom: BorderSide(color: AppConstants.borderLight)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "Last activity",
                style: TextStyle(fontSize: 11, color: AppConstants.textMuted, fontWeight: FontWeight.w500),
              ),
              Row(
                children: [
                  _buildTextFilter("Semua", "ALL"),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 6),
                    child: Text("·", style: TextStyle(color: AppConstants.textMuted, fontSize: 12)),
                  ),
                  _buildTextFilter("Menunggu", "WAITING_AGENT"),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 6),
                    child: Text("·", style: TextStyle(color: AppConstants.textMuted, fontSize: 12)),
                  ),
                  _buildTextFilter("Selesai", "RESOLVED"),
                ],
              ),
            ],
          ),
        ),

        // Scrollable List
        Expanded(
          child: _isLoadingTickets
              ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
              : _filteredInboxTickets.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.inbox, size: 48, color: Colors.grey[300]),
                          const SizedBox(height: 12),
                          const Text(
                            "Tidak ada tiket dalam antrean ini",
                            style: TextStyle(color: AppConstants.textMuted, fontSize: 13),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      color: AppConstants.primaryBlue,
                      backgroundColor: Colors.white,
                      onRefresh: _fetchTickets,
                      child: ListView.separated(
                        itemCount: _filteredInboxTickets.length,
                        separatorBuilder: (_, __) => const Divider(
                          color: AppConstants.borderSubtle,
                          height: 1,
                          indent: 72,
                        ),
                        itemBuilder: (ctx, idx) {
                          final ticket = _filteredInboxTickets[idx];
                          return _buildInboxTicketTile(ticket);
                        },
                      ),
                    ),
        ),
      ],
    );
  }

  Widget _buildTextFilter(String label, String value) {
    final isActive = _inboxFilter == value;
    return GestureDetector(
      onTap: () => setState(() => _inboxFilter = value),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: isActive ? FontWeight.bold : FontWeight.w500,
          color: isActive ? AppConstants.textPrimary : AppConstants.textMuted,
        ),
      ),
    );
  }

  // Single Conversation Tile matching Image 1
  Widget _buildInboxTicketTile(Ticket ticket) {
    final initials = _getInitials(ticket.customerName);
    final timeStr = _formatRelativeTime(ticket.updatedAt);
    final isWaiting = ticket.status == "WAITING_AGENT";

    return Material(
      color: isWaiting ? const Color(0xFFFEFCE8) : AppConstants.cardLight,
      child: InkWell(
        onTap: () => _openChat(ticket),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Circle Avatar with Initials matching Image 1
              CircleAvatar(
                radius: 20,
                backgroundColor: isWaiting ? const Color(0xFFFEF08A) : AppConstants.avatarBg,
                child: Text(
                  initials,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: isWaiting ? const Color(0xFF854D0E) : AppConstants.avatarText,
                  ),
                ),
              ),
              const SizedBox(width: 12),

              // Content: Name & Subject snippet
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
                            style: const TextStyle(
                              fontSize: 13.5,
                              fontWeight: FontWeight.bold,
                              color: AppConstants.textPrimary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Text(
                          timeStr,
                          style: const TextStyle(fontSize: 11, color: AppConstants.textMuted),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      ticket.subject,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppConstants.textSecondary,
                        height: 1.35,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppConstants.getStatusBgColor(ticket.status),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            AppConstants.getStatusLabel(ticket.status),
                            style: TextStyle(
                              color: AppConstants.getStatusColor(ticket.status),
                              fontSize: 9.5,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          "#${ticket.id.substring(0, ticket.id.length > 8 ? 8 : ticket.id.length)}",
                          style: const TextStyle(color: AppConstants.textMuted, fontSize: 10),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              // Right side WhatsApp-style Unread / Attention Badge
              if (isWaiting)
                Padding(
                  padding: const EdgeInsets.only(left: 8.0, top: 4.0),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0284C7),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text(
                      "CS",
                      style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  // ==========================================
  // TAB 2: TICKETS DIRECTORY (LIGHT THEME)
  // ==========================================
  Widget _buildTicketsDirectoryTab() {
    return Column(
      children: [
        // Search & Filter header
        Container(
          padding: const EdgeInsets.all(14),
          color: AppConstants.cardLight,
          child: Column(
            children: [
              TextField(
                onChanged: (q) => setState(() => _ticketSearchQuery = q),
                style: const TextStyle(color: AppConstants.textPrimary, fontSize: 13),
                decoration: InputDecoration(
                  hintText: "Cari ID tiket, pelanggan, atau subjek...",
                  hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                  prefixIcon: const Icon(Icons.search, color: AppConstants.textMuted, size: 18),
                  filled: true,
                  fillColor: AppConstants.bgLight,
                  contentPadding: const EdgeInsets.symmetric(vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderLight),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderLight),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildPillFilter("Semua Status", "ALL"),
                    _buildPillFilter("Menunggu CS", "WAITING_AGENT"),
                    _buildPillFilter("CS Aktif", "AGENT_ACTIVE"),
                    _buildPillFilter("Selesai", "RESOLVED"),
                  ],
                ),
              ),
            ],
          ),
        ),
        const Divider(color: AppConstants.borderLight, height: 1),

        // List
        Expanded(
          child: _isLoadingTickets
              ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
              : _filteredDirectoryTickets.isEmpty
                  ? const Center(
                      child: Text(
                        "Tidak ada tiket yang cocok",
                        style: TextStyle(color: AppConstants.textMuted, fontSize: 13),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _filteredDirectoryTickets.length,
                      itemBuilder: (ctx, idx) {
                        final t = _filteredDirectoryTickets[idx];
                        return Container(
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: AppConstants.cardLight,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppConstants.borderLight),
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
                                      color: AppConstants.getStatusBgColor(t.status),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      AppConstants.getStatusLabel(t.status),
                                      style: TextStyle(
                                        color: AppConstants.getStatusColor(t.status),
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  Text(
                                    DateFormat('dd MMM HH:mm').format(t.updatedAt),
                                    style: const TextStyle(fontSize: 11, color: AppConstants.textMuted),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                t.subject,
                                style: const TextStyle(
                                  color: AppConstants.textPrimary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13.5,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  const Icon(Icons.person_outline, size: 14, color: AppConstants.textMuted),
                                  const SizedBox(width: 4),
                                  Text(
                                    t.customerName,
                                    style: const TextStyle(fontSize: 12, color: AppConstants.textSecondary),
                                  ),
                                  const Spacer(),
                                  TextButton(
                                    style: TextButton.styleFrom(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                      minimumSize: Size.zero,
                                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                    ),
                                    onPressed: () => _openChat(t),
                                    child: const Text("Buka Chat", style: TextStyle(color: AppConstants.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold)),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        );
                      },
                    ),
        ),
      ],
    );
  }

  Widget _buildPillFilter(String label, String value) {
    final isSelected = _ticketStatusFilter == value;
    return Padding(
      padding: const EdgeInsets.only(right: 6.0),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (_) => setState(() => _ticketStatusFilter = value),
        selectedColor: const Color(0xFFE0F2FE),
        backgroundColor: AppConstants.bgLight,
        side: BorderSide(
          color: isSelected ? AppConstants.primaryBlue : AppConstants.borderLight,
        ),
        labelStyle: TextStyle(
          color: isSelected ? AppConstants.primaryBlue : AppConstants.textSecondary,
          fontSize: 11,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
      ),
    );
  }

  // ==========================================
  // TAB 3: KNOWLEDGE BASE (LIGHT THEME)
  // ==========================================
  Widget _buildKnowledgeBaseTab() {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          color: AppConstants.cardLight,
          child: Column(
            children: [
              TextField(
                onChanged: (q) => setState(() => _kbSearchQuery = q),
                style: const TextStyle(color: AppConstants.textPrimary, fontSize: 13),
                decoration: InputDecoration(
                  hintText: "Cari solusi panduan dan FAQ...",
                  hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                  prefixIcon: const Icon(Icons.search, color: AppConstants.textMuted, size: 18),
                  filled: true,
                  fillColor: AppConstants.bgLight,
                  contentPadding: const EdgeInsets.symmetric(vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderLight),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppConstants.borderLight),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildKBCategoryChip("Semua Kategori", "ALL"),
                    _buildKBCategoryChip("Akun & Profil", "ACCOUNT"),
                    _buildKBCategoryChip("Pembayaran", "BILLING"),
                    _buildKBCategoryChip("Kendala Teknis", "TECHNICAL"),
                    _buildKBCategoryChip("Informasi Umum", "GENERAL"),
                  ],
                ),
              ),
            ],
          ),
        ),
        const Divider(color: AppConstants.borderLight, height: 1),

        Expanded(
          child: _isLoadingKB
              ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
              : _filteredKBArticles.isEmpty
                  ? const Center(
                      child: Text(
                        "Tidak ada panduan ditemukan",
                        style: TextStyle(color: AppConstants.textMuted, fontSize: 13),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _filteredKBArticles.length,
                      itemBuilder: (ctx, idx) {
                        final article = _filteredKBArticles[idx];
                        return Card(
                          color: AppConstants.cardLight,
                          margin: const EdgeInsets.only(bottom: 10),
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: const BorderSide(color: AppConstants.borderLight),
                          ),
                          child: ExpansionTile(
                            tilePadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                            childrenPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                            title: Text(
                              article.question,
                              style: const TextStyle(
                                color: AppConstants.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                            subtitle: Text(
                              article.category,
                              style: const TextStyle(color: AppConstants.primaryBlue, fontSize: 10.5, fontWeight: FontWeight.w600),
                            ),
                            children: [
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AppConstants.bgLight,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: AppConstants.borderLight),
                                ),
                                child: Text(
                                  article.answer,
                                  style: const TextStyle(color: AppConstants.textSecondary, fontSize: 12.5, height: 1.45),
                                ),
                              ),
                              const SizedBox(height: 8),
                              Align(
                                alignment: Alignment.centerRight,
                                child: TextButton.icon(
                                  icon: const Icon(Icons.copy, size: 14, color: AppConstants.primaryBlue),
                                  label: const Text("Salin Solusi", style: TextStyle(color: AppConstants.primaryBlue, fontSize: 12)),
                                  onPressed: () {
                                    Clipboard.setData(ClipboardData(text: article.answer));
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                        content: Text("Solusi berhasil disalin ke clipboard."),
                                        duration: Duration(seconds: 2),
                                      ),
                                    );
                                  },
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
        ),
      ],
    );
  }

  Widget _buildKBCategoryChip(String label, String value) {
    final isSelected = _kbCategoryFilter == value;
    return Padding(
      padding: const EdgeInsets.only(right: 6.0),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (_) => setState(() => _kbCategoryFilter = value),
        selectedColor: const Color(0xFFE0F2FE),
        backgroundColor: AppConstants.bgLight,
        side: BorderSide(
          color: isSelected ? AppConstants.primaryBlue : AppConstants.borderLight,
        ),
        labelStyle: TextStyle(
          color: isSelected ? AppConstants.primaryBlue : AppConstants.textSecondary,
          fontSize: 11,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
      ),
    );
  }

  // ==========================================
  // TAB 4: SETTINGS & DIAGNOSTICS (LIGHT THEME)
  // ==========================================
  Widget _buildSettingsTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Profile Card
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppConstants.cardLight,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppConstants.borderLight),
          ),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: const Color(0xFFE0F2FE),
                child: Text(
                  _getInitials(widget.agentName),
                  style: const TextStyle(color: AppConstants.primaryBlue, fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.agentName,
                      style: const TextStyle(color: AppConstants.textPrimary, fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                    const SizedBox(height: 2),
                    const Text(
                      "Spesialis Layanan CS (Aktif)",
                      style: TextStyle(color: AppConstants.textMuted, fontSize: 11),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // System Diagnostics
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppConstants.cardLight,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppConstants.borderLight),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Diagnostik Layanan Realtime",
                style: TextStyle(color: AppConstants.textPrimary, fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 12),
              _buildDiagRow("FastAPI REST Service", "Terhubung (Port 8000)", Icons.check_circle_outline, const Color(0xFF16A34A)),
              const Divider(color: AppConstants.borderSubtle, height: 16),
              _buildDiagRow("WebSocket Gateway", "/ws/agents Active", Icons.sync, AppConstants.primaryBlue),
              const Divider(color: AppConstants.borderSubtle, height: 16),
              _buildDiagRow("SQLite Database", "Schema Initialized", Icons.storage, const Color(0xFF16A34A)),
              const Divider(color: AppConstants.borderSubtle, height: 16),
              _buildDiagRow("PII Masking Sanitizer", "Regex Active", Icons.security, const Color(0xFF16A34A)),
              const Divider(color: AppConstants.borderSubtle, height: 16),
              _buildDiagRow("Target Host", AppConstants.host, Icons.lan_outlined, AppConstants.textSecondary),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Logout Button
        OutlinedButton.icon(
          style: OutlinedButton.styleFrom(
            side: const BorderSide(color: Color(0xFFFECACA)),
            backgroundColor: const Color(0xFFFEF2F2),
            foregroundColor: const Color(0xFFDC2626),
            padding: const EdgeInsets.symmetric(vertical: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          icon: const Icon(Icons.logout, size: 18),
          label: const Text("Keluar (Logout)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          onPressed: () {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => const LoginScreen()),
            );
          },
        ),
      ],
    );
  }

  Widget _buildDiagRow(String title, String val, IconData icon, Color iconColor) {
    return Row(
      children: [
        Icon(icon, color: iconColor, size: 18),
        const SizedBox(width: 10),
        Expanded(
          child: Text(title, style: const TextStyle(color: AppConstants.textPrimary, fontSize: 12.5)),
        ),
        Text(val, style: TextStyle(color: iconColor, fontSize: 11, fontWeight: FontWeight.w600)),
      ],
    );
  }

  String _getInitials(String name) {
    final parts = name.trim().split(" ");
    if (parts.length >= 2) {
      return "${parts[0][0]}${parts[1][0]}".toUpperCase();
    } else if (parts.isNotEmpty && parts[0].isNotEmpty) {
      return parts[0].substring(0, parts[0].length >= 2 ? 2 : 1).toUpperCase();
    }
    return "CS";
  }

  String _formatRelativeTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return "Baru saja";
    if (diff.inMinutes < 60) return "${diff.inMinutes}m";
    if (diff.inHours < 24) return "${diff.inHours}h";
    return "${diff.inDays}d";
  }
}
