class ChatMessage {
  final String id;
  final String ticketId;
  final String senderType; // CUSTOMER, BOT, AGENT, SYSTEM
  final String senderName;
  final String content;
  final DateTime createdAt;

  ChatMessage({
    required this.id,
    required this.ticketId,
    required this.senderType,
    required this.senderName,
    required this.content,
    required this.createdAt,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    DateTime parsed;
    final rawDate = json['created_at']?.toString();
    if (rawDate != null && rawDate.isNotEmpty) {
      final utcString = (!rawDate.endsWith('Z') && !RegExp(r'[+-]\d{2}:\d{2}$').hasMatch(rawDate))
          ? '${rawDate}Z'
          : rawDate;
      parsed = DateTime.tryParse(utcString)?.toLocal() ?? DateTime.now();
    } else {
      parsed = DateTime.now();
    }

    return ChatMessage(
      id: json['id'] ?? '',
      ticketId: json['ticket_id'] ?? '',
      senderType: json['sender_type'] ?? 'CUSTOMER',
      senderName: json['sender_name'] ?? 'Pengguna',
      content: json['content'] ?? '',
      createdAt: parsed,
    );
  }
}
