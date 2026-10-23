import 'package:flutter_test/flutter_test.dart';
import 'package:helpdesk_mobile/main.dart';
import 'package:helpdesk_mobile/core/constants.dart';

void main() {
  testWidgets('Helpdesk app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const CiheulHelpdeskApp());
    expect(find.text('Masuk ke Helpdesk'), findsOneWidget);
  });

  group('Initials and Name Parsing Tests', () {
    String getInitials(String name) {
      final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
      if (parts.length >= 2) {
        return "${parts[0][0]}${parts[1][0]}".toUpperCase();
      } else if (parts.isNotEmpty && parts[0].isNotEmpty) {
        return parts[0].substring(0, parts[0].length >= 2 ? 2 : 1).toUpperCase();
      }
      return "CS";
    }

    test('parses standard two-word name', () {
      expect(getInitials('Dewi Putri'), 'DP');
    });

    test('handles multiple consecutive spaces without index out of range crash', () {
      expect(getInitials('Dewi   Putri'), 'DP');
      expect(getInitials('  Ahmad   Syahid  '), 'AS');
    });

    test('handles single word name', () {
      expect(getInitials('Budi'), 'BU');
      expect(getInitials('A'), 'A');
    });

    test('handles empty or whitespace only input safely', () {
      expect(getInitials(''), 'CS');
      expect(getInitials('   '), 'CS');
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
