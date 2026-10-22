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
    return ChatMessage(
      id: json['id'] ?? '',
      ticketId: json['ticket_id'] ?? '',
      senderType: json['sender_type'] ?? 'CUSTOMER',
      senderName: json['sender_name'] ?? 'Pengguna',
      content: json['content'] ?? '',
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}
