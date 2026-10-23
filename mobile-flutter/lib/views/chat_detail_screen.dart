import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/constants.dart';
import '../models/message.dart';
import '../models/copilot.dart';

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
      final wsUrl = Uri.parse("${AppConstants.wsBaseUrl}/ws/ticket/${widget.ticketId}");
      _roomChannel = WebSocketChannel.connect(wsUrl);

      _roomChannel!.sink.add(jsonEncode({
        "event": "auth",
        "token": widget.token,
      }));

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

  void _sendMessage([String? overrideText]) {
    final text = (overrideText ?? _msgCtrl.text).trim();
    if (text.isEmpty || _roomChannel == null) return;
    if (overrideText == null) {
      _msgCtrl.clear();
    }

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

  Future<void> _uploadAttachment(String filename, List<int> bytes) async {
    try {
      final uri = Uri.parse("${AppConstants.apiBaseUrl}/api/v1/tickets/${widget.ticketId}/attachments");
      final req = http.MultipartRequest("POST", uri);
      req.headers["Authorization"] = "Bearer ${widget.token}";
      req.files.add(http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: filename,
      ));
      final res = await req.send();
      if (res.statusCode == 200) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text("Lampiran $filename berhasil dikirim."),
              backgroundColor: const Color(0xFF0F766E),
            ),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text("Gagal mengunggah berkas."),
              backgroundColor: Colors.redAccent,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Error: $e"),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    }
  }

  void _showAttachmentPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppConstants.cardDark,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Kirim Lampiran Dukungan",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  "Pilih berkas panduan atau log diagnosa untuk dikirim ke pelanggan:",
                  style: TextStyle(color: AppConstants.textMuted, fontSize: 12),
                ),
                const SizedBox(height: 16),
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppConstants.primaryBlue.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.image, color: AppConstants.primaryBlue),
                  ),
                  title: const Text("Tangkapan Layar Panduan (PNG)", style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                  subtitle: const Text("Kirim sampel cuplikan langkah solusi", style: TextStyle(color: AppConstants.textMuted, fontSize: 11)),
                  onTap: () {
                    Navigator.pop(ctx);
                    // Minimal 1x1 transparent PNG bytes
                    final pngBytes = base64Decode(
                      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    );
                    _uploadAttachment("panduan_solusi.png", pngBytes);
                  },
                ),
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.redAccent.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.picture_as_pdf, color: Colors.redAccent),
                  ),
                  title: const Text("Dokumen Diagnostik Sistem (PDF)", style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                  subtitle: const Text("Kirim log pengecekan teknis resmi", style: TextStyle(color: AppConstants.textMuted, fontSize: 11)),
                  onTap: () {
                    Navigator.pop(ctx);
                    // Valid minimal PDF header bytes
                    final pdfBytes = utf8.encode("%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 300 144]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n180\n%%EOF");
                    _uploadAttachment("laporan_diagnosa.pdf", pdfBytes);
                  },
                ),
                const SizedBox(height: 8),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showCopilotSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppConstants.cardDark,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _CopilotSheetContent(
        ticketId: widget.ticketId,
        token: widget.token,
        onUseDraft: (draft) {
          Navigator.pop(ctx);
          setState(() {
            _msgCtrl.text = draft;
          });
        },
        onSendImmediately: (draft) {
          Navigator.pop(ctx);
          _sendMessage(draft);
        },
      ),
    );
  }

  void _showFullscreenImage(String imageUrl, String filename) {
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.black,
        insetPadding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      filename,
                      style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
            ),
            InteractiveViewer(
              child: Image.network(
                imageUrl,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => Container(
                  height: 200,
                  color: AppConstants.bgDark,
                  child: const Center(
                    child: Text("Gagal memuat gambar", style: TextStyle(color: AppConstants.textMuted)),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
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
          IconButton(
            tooltip: "Buka Copilot AI",
            icon: const Icon(Icons.auto_awesome, color: Color(0xFF818CF8)),
            onPressed: _showCopilotSheet,
          ),
          if (_status == "WAITING_AGENT" || _status == "BOT_ACTIVE")
            TextButton(
              onPressed: _claimTicket,
              child: const Text("Klaim", style: TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.bold, fontSize: 12)),
            ),
          if (_status == "AGENT_ACTIVE")
            TextButton(
              onPressed: _resolveTicket,
              child: const Text("Selesai", style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.bold, fontSize: 12)),
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
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              color: AppConstants.cardDark,
              child: SafeArea(
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.attach_file, color: AppConstants.textMuted),
                      tooltip: "Lampirkan Dokumen/Foto",
                      onPressed: _showAttachmentPicker,
                    ),
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
                        onPressed: () => _sendMessage(),
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

    // Attachment pattern detection
    final attachmentRegex = RegExp(r'\[Lampiran:\s*([^\]]+)\]\(([^)]+)\)');
    final match = attachmentRegex.firstMatch(msg.content);

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
                if (match == null)
                  Text(
                    msg.content,
                    style: const TextStyle(fontSize: 13, color: Colors.white, height: 1.35),
                  )
                else
                  _buildAttachmentContent(msg.content, match),
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

  Widget _buildAttachmentContent(String content, RegExpMatch match) {
    final filename = match.group(1) ?? 'Berkas Lampiran';
    final rawUrl = match.group(2) ?? '';
    final fileUrl = rawUrl.startsWith('http') ? rawUrl : '${AppConstants.apiBaseUrl}$rawUrl';

    final prefixText = content.substring(0, match.start).trim();
    final suffixText = content.substring(match.end).trim();

    final isImage = filename.toLowerCase().endsWith('.png') ||
        filename.toLowerCase().endsWith('.jpg') ||
        filename.toLowerCase().endsWith('.jpeg') ||
        filename.toLowerCase().endsWith('.webp');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (prefixText.isNotEmpty) ...[
          Text(prefixText, style: const TextStyle(fontSize: 13, color: Colors.white)),
          const SizedBox(height: 6),
        ],
        if (isImage)
          GestureDetector(
            onTap: () => _showFullscreenImage(fileUrl, filename),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Stack(
                children: [
                  Image.network(
                    fileUrl,
                    height: 160,
                    width: double.infinity,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                      height: 120,
                      color: AppConstants.bgDark,
                      child: Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.broken_image, color: AppConstants.textMuted),
                            const SizedBox(height: 4),
                            Text(filename, style: const TextStyle(fontSize: 11, color: AppConstants.textMuted)),
                          ],
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 6,
                    right: 6,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.7),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.zoom_in, color: Colors.white, size: 12),
                          SizedBox(width: 4),
                          Text("Perbesar", style: TextStyle(color: Colors.white, fontSize: 10)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          )
        else
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppConstants.bgDark,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppConstants.borderDark),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Icon(Icons.picture_as_pdf, color: Colors.redAccent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        filename,
                        style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        "Dokumen Lampiran Terverifikasi",
                        style: TextStyle(color: AppConstants.textMuted, fontSize: 10),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        if (suffixText.isNotEmpty) ...[
          const SizedBox(height: 6),
          Text(suffixText, style: const TextStyle(fontSize: 13, color: Colors.white)),
        ],
      ],
    );
  }
}

class _CopilotSheetContent extends StatefulWidget {
  final String ticketId;
  final String token;
  final ValueChanged<String> onUseDraft;
  final ValueChanged<String> onSendImmediately;

  const _CopilotSheetContent({
    required this.ticketId,
    required this.token,
    required this.onUseDraft,
    required this.onSendImmediately,
  });

  @override
  State<_CopilotSheetContent> createState() => _CopilotSheetContentState();
}

class _CopilotSheetContentState extends State<_CopilotSheetContent> {
  CopilotAnalysis? _analysis;
  bool _isLoading = true;
  String? _errorMessage;

  final _askCtrl = TextEditingController();
  bool _isAsking = false;
  String? _askAnswer;

  @override
  void initState() {
    super.initState();
    _fetchAnalysis();
  }

  @override
  void dispose() {
    _askCtrl.dispose();
    super.dispose();
  }

  Future<void> _fetchAnalysis() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final res = await http.post(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/copilot/${widget.ticketId}/analyze"),
        headers: {
          "Authorization": "Bearer ${widget.token}",
          "Content-Type": "application/json",
        },
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        setState(() {
          _analysis = CopilotAnalysis.fromJson(data);
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = "Gagal memuat rekomendasi Copilot (Status ${res.statusCode})";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Koneksi ke Copilot gagal: $e";
        _isLoading = false;
      });
    }
  }

  Future<void> _handleAsk() async {
    final q = _askCtrl.text.trim();
    if (q.isEmpty) return;

    setState(() {
      _isAsking = true;
      _askAnswer = null;
    });

    try {
      final res = await http.post(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/copilot/${widget.ticketId}/ask"),
        headers: {
          "Authorization": "Bearer ${widget.token}",
          "Content-Type": "application/json",
        },
        body: jsonEncode({"question": q}),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        setState(() {
          _askAnswer = data['answer'] ?? 'Tidak ada jawaban';
        });
      } else {
        setState(() {
          _askAnswer = "Copilot tidak dapat menjawab pertanyaan ini.";
        });
      }
    } catch (e) {
      setState(() {
        _askAnswer = "Gagal menghubungi Copilot: $e";
      });
    } finally {
      setState(() {
        _isAsking = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.8,
      minChildSize: 0.45,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: AppConstants.cardDark,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          child: Column(
            children: [
              // Pull bar
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppConstants.borderDark,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              // Header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF6366F1).withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.auto_awesome, color: Color(0xFF818CF8), size: 18),
                  ),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Copilot AI Assistant",
                          style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          "Analisis konteks tiket & saran resolusi otomatis",
                          style: TextStyle(color: AppConstants.textMuted, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: AppConstants.textMuted, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const Divider(color: AppConstants.borderDark, height: 24),
              // Body
              Expanded(
                child: _isLoading
                    ? const Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            CircularProgressIndicator(color: Color(0xFF818CF8)),
                            SizedBox(height: 12),
                            Text("Copilot sedang menganalisis obrolan...", style: TextStyle(color: AppConstants.textMuted, fontSize: 12)),
                          ],
                        ),
                      )
                    : _errorMessage != null
                        ? Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(_errorMessage!, style: const TextStyle(color: Colors.redAccent, fontSize: 12), textAlign: TextAlign.center),
                                const SizedBox(height: 10),
                                OutlinedButton(
                                  onPressed: _fetchAnalysis,
                                  child: const Text("Coba Lagi", style: TextStyle(color: Colors.white)),
                                ),
                              ],
                            ),
                          )
                        : _buildCopilotBody(scrollController),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildCopilotBody(ScrollController scrollController) {
    final analysis = _analysis!;

    return ListView(
      controller: scrollController,
      children: [
        // Summary
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppConstants.bgDark,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppConstants.borderDark),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.article_outlined, color: AppConstants.primaryBlue, size: 16),
                  SizedBox(width: 8),
                  Text("Ringkasan Kasus", style: TextStyle(color: AppConstants.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                analysis.summary,
                style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // Draft Reply Card
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1B4B).withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFF4338CA)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.mark_chat_read_outlined, color: Color(0xFF818CF8), size: 16),
                  SizedBox(width: 8),
                  Text("Rekomendasi Respons Agen", style: TextStyle(color: Color(0xFF818CF8), fontSize: 12, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                analysis.draftReply,
                style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF818CF8),
                        side: const BorderSide(color: Color(0xFF6366F1)),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      icon: const Icon(Icons.edit_note, size: 18),
                      label: const Text("Gunakan Draf", style: TextStyle(fontSize: 12)),
                      onPressed: () => widget.onUseDraft(analysis.draftReply),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF4F46E5),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      icon: const Icon(Icons.send, size: 16),
                      label: const Text("Kirim Langsung", style: TextStyle(fontSize: 12)),
                      onPressed: () => widget.onSendImmediately(analysis.draftReply),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // Follow ups
        if (analysis.followUps.isNotEmpty) ...[
          const Text(
            "Aksi / Saran Tindak Lanjut:",
            style: TextStyle(color: AppConstants.textMuted, fontSize: 12, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: analysis.followUps.map((action) {
              return ActionChip(
                backgroundColor: AppConstants.bgDark,
                side: const BorderSide(color: AppConstants.borderDark),
                label: Text(action, style: const TextStyle(color: Colors.white, fontSize: 11)),
                avatar: const Icon(Icons.arrow_forward_ios, size: 10, color: AppConstants.primaryBlue),
                onPressed: () => widget.onUseDraft(action),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
        ],

        // Ask Copilot Box
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppConstants.bgDark,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppConstants.borderDark),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.help_outline, color: Colors.amberAccent, size: 16),
                  SizedBox(width: 8),
                  Text("Tanya Copilot", style: TextStyle(color: Colors.amberAccent, fontSize: 12, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _askCtrl,
                      style: const TextStyle(color: Colors.white, fontSize: 12),
                      decoration: InputDecoration(
                        hintText: "Contoh: Bagaimana aturan refund?",
                        hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 11),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: AppConstants.borderDark),
                        ),
                      ),
                      onSubmitted: (_) => _handleAsk(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.amber[700],
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    ),
                    onPressed: _isAsking ? null : _handleAsk,
                    child: _isAsking
                        ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                        : const Text("Tanya", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
              if (_askAnswer != null) ...[
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.amber.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
                  ),
                  child: Text(
                    _askAnswer!,
                    style: const TextStyle(color: Colors.white, fontSize: 12, height: 1.35),
                  ),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 20),
      ],
    );
  }
}
