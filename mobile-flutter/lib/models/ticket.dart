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
    DateTime parsed;
    final rawDate = json['updated_at']?.toString();
    if (rawDate != null && rawDate.isNotEmpty) {
      final utcString = (!rawDate.endsWith('Z') && !RegExp(r'[+-]\d{2}:\d{2}$').hasMatch(rawDate))
          ? '${rawDate}Z'
          : rawDate;
      parsed = DateTime.tryParse(utcString)?.toLocal() ?? DateTime.now();
    } else {
      parsed = DateTime.now();
    }

    return Ticket(
      id: json['id'] ?? '',
      customerName: json['customer_name'] ?? 'Tamu',
      customerEmail: json['customer_email'],
      subject: json['subject'] ?? 'Bantuan Kendala',
      category: json['category'] ?? 'GENERAL',
      status: json['status'] ?? 'BOT_ACTIVE',
      priority: json['priority'] ?? 'MEDIUM',
      updatedAt: parsed,
    );
  }
}
