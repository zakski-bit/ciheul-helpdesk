import 'package:flutter_test/flutter_test.dart';
import 'package:helpdesk_mobile/main.dart';

void main() {
  testWidgets('Helpdesk app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const CiheulHelpdeskApp());
    expect(find.text('CIHEUL Support Mobile'), findsOneWidget);
  });
}
