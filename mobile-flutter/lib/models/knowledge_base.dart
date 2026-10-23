class KnowledgeBaseArticle {
  final String id;
  final String question;
  final String answer;
  final String category;
  final String keywords;
  final bool isActive;

  KnowledgeBaseArticle({
    required this.id,
    required this.question,
    required this.answer,
    required this.category,
    required this.keywords,
    required this.isActive,
  });

  factory KnowledgeBaseArticle.fromJson(Map<String, dynamic> json) {
    return KnowledgeBaseArticle(
      id: json['id']?.toString() ?? '',
      question: json['question'] ?? '',
      answer: json['answer'] ?? '',
      category: json['category'] ?? 'GENERAL',
      keywords: json['keywords'] ?? '',
      isActive: json['is_active'] ?? true,
    );
  }
}
