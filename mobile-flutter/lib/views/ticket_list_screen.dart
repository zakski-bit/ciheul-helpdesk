import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/constants.dart';
import '../models/ticket.dart';
import 'chat_detail_screen.dart';

class TicketListScreen extends StatefulWidget {
  final String token;
  final String agentName;

  const TicketListScreen({super.key, required this.token, required this.agentName});

  @override
  State<TicketListScreen> createState() => _TicketListScreenState();
}

class _TicketListScreenState extends State<TicketListScreen> {
  List<Ticket> _tickets = [];
  bool _isLoading = true;
  String _currentFilter = "ALL";
  WebSocketChannel? _agentChannel;

  @override
  void initState() {
    super.initState();
    _fetchTickets();
    _connectAgentWebSocket();
  }

  @override
  void dispose() {
    _agentChannel?.sink.close();
    super.dispose();
  }

  Future<void> _fetchTickets() async {
    setState(() => _isLoading = true);
    try {
      final res = await http.get(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/tickets"),
        headers: {"Authorization": "Bearer ${widget.token}"},
      );
      if (res.statusCode == 200) {
        final List data = jsonDecode(res.body);
        setState(() {
          _tickets = data.map((json) => Ticket.fromJson(json)).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

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
                    backgroundColor: Colors.amber[900],
                    content: Row(
                      children: const [
                        Icon(Icons.mark_email_unread_outlined, color: Colors.amberAccent, size: 18),
                        SizedBox(width: 8),
                        Expanded(child: Text("Tiket eskalasi baru dialihkan ke CS")),
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

  List<Ticket> get _filteredTickets {
    if (_currentFilter == "ALL") return _tickets;
    return _tickets.where((t) => t.status == _currentFilter).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.bgDark,
      appBar: AppBar(
        backgroundColor: AppConstants.cardDark,
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Antrean Tiket Helpdesk",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            Text(
              "Agen: ${widget.agentName}",
              style: const TextStyle(fontSize: 11, color: AppConstants.textMuted),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppConstants.primaryBlue),
            onPressed: _fetchTickets,
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Tabs Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: AppConstants.cardDark,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildFilterChip("Semua", "ALL"),
                  _buildFilterChip("Menunggu CS", "WAITING_AGENT"),
                  _buildFilterChip("CS Aktif", "AGENT_ACTIVE"),
                  _buildFilterChip("Selesai", "RESOLVED"),
                ],
              ),
            ),
          ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
                : _filteredTickets.isEmpty
                    ? const Center(
                        child: Text(
                          "Tidak ada tiket pada kategori ini.",
                          style: TextStyle(color: AppConstants.textMuted, fontSize: 13),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _fetchTickets,
                        color: AppConstants.primaryBlue,
                        child: ListView.separated(
                          padding: const EdgeInsets.all(16),
                          itemCount: _filteredTickets.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 12),
                          itemBuilder: (ctx, idx) {
                            final ticket = _filteredTickets[idx];
                            return _buildTicketCard(ticket);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, String value) {
    final isSelected = _currentFilter == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: FilterChip(
        label: Text(label),
        labelStyle: TextStyle(
          color: isSelected ? Colors.white : AppConstants.textMuted,
          fontSize: 12,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
        selected: isSelected,
        selectedColor: AppConstants.primaryBlue,
        backgroundColor: AppConstants.borderDark,
        onSelected: (_) {
          setState(() => _currentFilter = value);
        },
      ),
    );
  }

  Widget _buildTicketCard(Ticket ticket) {
    Color statusColor = Colors.grey;
    String statusLabel = ticket.status;

    if (ticket.status == "WAITING_AGENT") {
      statusColor = Colors.amber;
      statusLabel = "MENUNGGU CS";
    } else if (ticket.status == "AGENT_ACTIVE") {
      statusColor = AppConstants.primaryBlue;
      statusLabel = "CS AKTIF";
    } else if (ticket.status == "RESOLVED" || ticket.status == "CLOSED") {
      statusColor = Colors.green;
      statusLabel = "SELESAI";
    } else if (ticket.status == "BOT_ACTIVE") {
      statusColor = Colors.indigo;
      statusLabel = "BOT AI";
    }

    final formattedTime = DateFormat('HH:mm').format(ticket.updatedAt);

    return InkWell(
      onTap: () async {
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
      },
      borderRadius: BorderRadius.circular(12),
      child: Container(
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
                Text(
                  ticket.customerName,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppConstants.textLight),
                ),
                Text(
                  formattedTime,
                  style: const TextStyle(fontSize: 11, color: AppConstants.textMuted),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              ticket.subject,
              style: const TextStyle(fontSize: 13, color: Color(0xFFCBD5E1)),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
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
                    style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
                Text(
                  ticket.category,
                  style: const TextStyle(color: AppConstants.textMuted, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
