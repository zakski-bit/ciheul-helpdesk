class Ticket {
  final String id;
  final String customerName;
  final String? customerEmail;
  final String subject;
  final String category;
  final String status;
  final String priority;
  final DateTime updatedAt;

  Ticket({
    required this.id,
    required this.customerName,
    this.customerEmail,
    required this.subject,
    required this.category,
    required this.status,
    required this.priority,
    required this.updatedAt,
  });

  factory Ticket.fromJson(Map<String, dynamic> json) {
    return Ticket(
      id: json['id'] ?? '',
      customerName: json['customer_name'] ?? 'Tamu',
      customerEmail: json['customer_email'],
      subject: json['subject'] ?? 'Bantuan Kendala',
      category: json['category'] ?? 'GENERAL',
      status: json['status'] ?? 'BOT_ACTIVE',
      priority: json['priority'] ?? 'MEDIUM',
      updatedAt: DateTime.tryParse(json['updated_at'] ?? '') ?? DateTime.now(),
    );
  }
}
