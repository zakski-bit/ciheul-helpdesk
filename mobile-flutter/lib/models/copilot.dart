class CopilotAnalysis {
  final String ticketId;
  final String customerName;
  final String summary;
  final String draftReply;
  final List<String> followUps;

  CopilotAnalysis({
    required this.ticketId,
    required this.customerName,
    required this.summary,
    required this.draftReply,
    required this.followUps,
  });

  factory CopilotAnalysis.fromJson(Map<String, dynamic> json) {
    final list = json['follow_ups'] as List? ?? [];
    return CopilotAnalysis(
      ticketId: json['ticket_id'] ?? '',
      customerName: json['customer_name'] ?? 'Pelanggan',
      summary: json['summary'] ?? '',
      draftReply: json['draft_reply'] ?? '',
      followUps: list.map((e) => e.toString()).toList(),
    );
  }
}
