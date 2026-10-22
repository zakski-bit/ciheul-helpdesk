import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/constants.dart';
import '../models/message.dart';

class ChatDetailScreen extends StatefulWidget {
  final String ticketId;
  final String token;
  final String agentName;
  final String customerName;
  final String subject;
  final String initialStatus;

  const ChatDetailScreen({
    super.key,
    required this.ticketId,
    required this.token,
    required this.agentName,
    required this.customerName,
    required this.subject,
    required this.initialStatus,
  });

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final List<ChatMessage> _messages = [];
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  WebSocketChannel? _roomChannel;
  late String _status;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _status = widget.initialStatus;
    _fetchDetailAndHistory();
    _connectRoomWebSocket();
  }

  @override
  void dispose() {
    _roomChannel?.sink.close();
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _fetchDetailAndHistory() async {
    try {
      final res = await http.get(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/tickets/${widget.ticketId}"),
        headers: {"Authorization": "Bearer ${widget.token}"},
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final List msgList = data['messages'] ?? [];
        setState(() {
          _status = data['status'] ?? _status;
          _messages.clear();
          _messages.addAll(msgList.map((j) => ChatMessage.fromJson(j)));
          _isLoading = false;
        });
        _scrollToBottom();
      }
    } catch (_) {
      setState(() => _isLoading = false);
    }
  }

  void _connectRoomWebSocket() {
    if (!mounted) return;
    try {
      final wsUrl = Uri.parse("${AppConstants.wsBaseUrl}/ws/ticket/${widget.ticketId}?token=${Uri.encodeComponent(widget.token)}");
      _roomChannel = WebSocketChannel.connect(wsUrl);

      if (_messages.isNotEmpty) {
        _roomChannel!.sink.add(jsonEncode({
          "event": "sync_missed",
          "last_message_id": _messages.last.id,
        }));
      }

      _roomChannel!.stream.listen(
        (message) {
          try {
            final data = jsonDecode(message);
            final event = data['event'];
            if (event == 'new_message') {
              final newMsg = ChatMessage.fromJson(data);
              if (!_messages.any((m) => m.id == newMsg.id)) {
                setState(() {
                  _messages.add(newMsg);
                });
                _scrollToBottom();
              }
            } else if (event == 'sync_result' && data['messages'] != null) {
              final List msgList = data['messages'];
              if (msgList.isNotEmpty) {
                setState(() {
                  for (var m in msgList) {
                    final msgObj = ChatMessage.fromJson(m);
                    if (!_messages.any((existing) => existing.id == msgObj.id)) {
                      _messages.add(msgObj);
                    }
                  }
                });
                _scrollToBottom();
              }
            } else if (event == 'ticket_claimed') {
              setState(() => _status = "AGENT_ACTIVE");
            } else if (event == 'ticket_resolved') {
              setState(() => _status = "RESOLVED");
            }
          } catch (_) {}
        },
        onError: (_) {
          if (mounted) {
            Future.delayed(const Duration(seconds: 3), _connectRoomWebSocket);
          }
        },
        onDone: () {
          if (mounted) {
            Future.delayed(const Duration(seconds: 3), _connectRoomWebSocket);
          }
        },
      );
    } catch (_) {
      if (mounted) {
        Future.delayed(const Duration(seconds: 3), _connectRoomWebSocket);
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage() {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty || _roomChannel == null) return;
    _msgCtrl.clear();

    _roomChannel!.sink.add(jsonEncode({
      "event": "send_message",
      "content": text,
      "sender_type": "AGENT",
      "sender_name": widget.agentName,
    }));
  }

  Future<void> _claimTicket() async {
    try {
      final res = await http.post(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/tickets/${widget.ticketId}/claim"),
        headers: {"Authorization": "Bearer ${widget.token}"},
      );
      if (res.statusCode == 200) {
        setState(() => _status = "AGENT_ACTIVE");
      }
    } catch (_) {}
  }

  Future<void> _resolveTicket() async {
    try {
      final res = await http.post(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/tickets/${widget.ticketId}/resolve"),
        headers: {"Authorization": "Bearer ${widget.token}"},
      );
      if (res.statusCode == 200) {
        setState(() => _status = "RESOLVED");
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final isClosed = _status == "RESOLVED" || _status == "CLOSED";

    return Scaffold(
      backgroundColor: AppConstants.bgDark,
      appBar: AppBar(
        backgroundColor: AppConstants.cardDark,
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.customerName,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            Text(
              widget.subject,
              style: const TextStyle(fontSize: 11, color: AppConstants.textMuted),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        actions: [
          if (_status == "WAITING_AGENT" || _status == "BOT_ACTIVE")
            TextButton(
              onPressed: _claimTicket,
              child: const Text("Klaim Tiket", style: TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.bold)),
            ),
          if (_status == "AGENT_ACTIVE")
            TextButton(
              onPressed: _resolveTicket,
              child: const Text("Selesai", style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.bold)),
            ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppConstants.primaryBlue))
                : ListView.builder(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (ctx, idx) {
                      final msg = _messages[idx];
                      return _buildMessageBubble(msg);
                    },
                  ),
          ),
          if (!isClosed)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              color: AppConstants.cardDark,
              child: SafeArea(
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _msgCtrl,
                        style: const TextStyle(color: Colors.white, fontSize: 13),
                        decoration: InputDecoration(
                          hintText: "Ketik balasan CS...",
                          hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                          filled: true,
                          fillColor: AppConstants.bgDark,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(20),
                            borderSide: const BorderSide(color: AppConstants.borderDark),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(20),
                            borderSide: const BorderSide(color: AppConstants.borderDark),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    CircleAvatar(
                      backgroundColor: AppConstants.primaryBlue,
                      child: IconButton(
                        icon: const Icon(Icons.send, color: Colors.white, size: 18),
                        onPressed: _sendMessage,
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            Container(
              padding: const EdgeInsets.all(12),
              color: Colors.green.withValues(alpha: 0.12),
              child: const Center(
                child: Text(
                  "Kendala telah ditandai selesai (Resolved)",
                  style: TextStyle(color: Colors.greenAccent, fontSize: 12, fontWeight: FontWeight.w600),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    final isAgent = msg.senderType == "AGENT";
    final isBot = msg.senderType == "BOT";
    final isSystem = msg.senderType == "SYSTEM";

    if (isSystem) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 8.0),
        child: Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            decoration: BoxDecoration(
              color: AppConstants.borderDark.withValues(alpha: 0.6),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              msg.content,
              style: const TextStyle(color: AppConstants.textMuted, fontSize: 11),
              textAlign: TextAlign.center,
            ),
          ),
        ),
      );
    }

    final align = isAgent ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    Color bubbleColor = AppConstants.cardDark;
    if (isAgent) bubbleColor = AppConstants.primaryBlue;
    if (isBot) bubbleColor = const Color(0xFF1E1B4B);

    final time = DateFormat('HH:mm').format(msg.createdAt);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Column(
        crossAxisAlignment: align,
        children: [
          Container(
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: bubbleColor,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isBot ? const Color(0xFF4338CA) : AppConstants.borderDark,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  msg.senderName,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: isAgent ? Colors.white70 : (isBot ? const Color(0xFF818CF8) : AppConstants.primaryBlue),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  msg.content,
                  style: const TextStyle(fontSize: 13, color: Colors.white, height: 1.35),
                ),
                const SizedBox(height: 4),
                Align(
                  alignment: Alignment.bottomRight,
                  child: Text(
                    time,
                    style: const TextStyle(fontSize: 9, color: Colors.white54),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
