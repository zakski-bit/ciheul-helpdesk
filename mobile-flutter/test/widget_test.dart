import 'package:flutter_test/flutter_test.dart';
import 'package:helpdesk_mobile/main.dart';
import 'package:helpdesk_mobile/core/constants.dart';

void main() {
  testWidgets('Helpdesk app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const CiheulHelpdeskApp());
    expect(find.text('Masuk ke Helpdesk'), findsOneWidget);
  });

  group('Initials and Name Parsing Production Tests', () {
    test('parses standard two-word name', () {
      expect(AppConstants.getInitials('Dewi Putri'), 'DP');
    });

    test('handles multiple consecutive spaces without index out of range crash', () {
      expect(AppConstants.getInitials('Dewi   Putri'), 'DP');
      expect(AppConstants.getInitials('  Ahmad   Syahid  '), 'AS');
    });

    test('handles single word name', () {
      expect(AppConstants.getInitials('Budi'), 'BU');
      expect(AppConstants.getInitials('A'), 'A');
    });

    test('handles empty or whitespace only input safely', () {
      expect(AppConstants.getInitials(''), 'CS');
      expect(AppConstants.getInitials('   '), 'CS');
    });
  });

  group('Network Protocol & Security Host Resolution Tests', () {
    test('local development hosts resolve to http / ws', () {
      AppConstants.host = '127.0.0.1:8000';
      expect(AppConstants.protocol, 'http');
      expect(AppConstants.wsProtocol, 'ws');

      AppConstants.host = '10.250.219.238:8000';
      expect(AppConstants.protocol, 'http');
      expect(AppConstants.wsProtocol, 'ws');
    });

    test('production domain resolves to https / wss', () {
      AppConstants.host = 'api.ciheul.com';
      expect(AppConstants.protocol, 'https');
      expect(AppConstants.wsProtocol, 'wss');

      // Reset back to default local dev host
      AppConstants.host = AppConstants.defaultUsbHost;
    });
  });
}
