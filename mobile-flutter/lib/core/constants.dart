import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AppConstants {
  // Configurable API & WebSocket URLs
  static const bool isProduction = kReleaseMode;
  
  // Default to 127.0.0.1:8000 (direct IPv4 for adb reverse)
  static String _activeHost = const String.fromEnvironment('API_HOST', defaultValue: '127.0.0.1:8000');
  static const String defaultWifiHost = '10.250.219.238:8000';
  static const String defaultUsbHost = '127.0.0.1:8000';

  static String get host => _activeHost;
  static set host(String value) {
    if (value.trim().isNotEmpty) {
      _activeHost = value.trim();
    }
  }

  static bool get _isLocalOrInsecure =>
      _activeHost.contains('localhost') ||
      _activeHost.contains('10.0.2.2') ||
      _activeHost.contains('127.0.0.1') ||
      _activeHost.contains(':8000') ||
      _activeHost.startsWith('192.168.') ||
      _activeHost.startsWith('10.');

  static String get protocol => _isLocalOrInsecure ? 'http' : (isProduction ? 'https' : 'http');
  static String get wsProtocol => _isLocalOrInsecure ? 'ws' : (isProduction ? 'wss' : 'ws');

  static String get apiBaseUrl => "$protocol://$host";
  static String get wsBaseUrl => "$wsProtocol://$host";

  // Web Dashboard Light Theme Colors (Clean White & Slate)
  static const Color bgLight = Color(0xFFF9FAFB);
  static const Color cardLight = Color(0xFFFFFFFF);
  static const Color borderLight = Color(0xFFE5E7EB);
  static const Color borderSubtle = Color(0xFFF3F4F6);
  static const Color primaryBlue = Color(0xFF0284C7);
  static const Color primaryHover = Color(0xFF0369A1);
  static const Color textPrimary = Color(0xFF111827);
  static const Color textSecondary = Color(0xFF4B5563);
  static const Color textMuted = Color(0xFF6B7280);
  static const Color badgeBg = Color(0xFFF3F4F6);
  static const Color avatarBg = Color(0xFFE2E8F0);
  static const Color avatarText = Color(0xFF334155);

  // Legacy aliases
  static const Color bgDark = bgLight;
  static const Color cardDark = cardLight;
  static const Color borderDark = borderLight;
  static const Color textLight = textPrimary;
  static const Color accentIndigo = Color(0xFF4F46E5);

  // Bot & Copilot Accents
  static const Color botBg = Color(0xFFF5F3FF);
  static const Color botBorder = Color(0xFFDDD6FE);
  static const Color botText = Color(0xFF4C1D95);
  static const Color copilotAccent = Color(0xFF4F46E5);

  // Status Colors
  static Color getStatusColor(String status) {
    switch (status) {
      case "WAITING_AGENT":
        return const Color(0xFFD97706);
      case "AGENT_ACTIVE":
        return const Color(0xFF0284C7);
      case "RESOLVED":
      case "CLOSED":
        return const Color(0xFF16A34A);
      case "BOT_ACTIVE":
      default:
        return const Color(0xFF6366F1);
    }
  }

  static Color getStatusBgColor(String status) {
    switch (status) {
      case "WAITING_AGENT":
        return const Color(0xFFFEF3C7);
      case "AGENT_ACTIVE":
        return const Color(0xFFE0F2FE);
      case "RESOLVED":
      case "CLOSED":
        return const Color(0xFFDCFCE7);
      case "BOT_ACTIVE":
      default:
        return const Color(0xFFEEF2FF);
    }
  }

  static String getStatusLabel(String status) {
    switch (status) {
      case "WAITING_AGENT":
        return "MENUNGGU CS";
      case "AGENT_ACTIVE":
        return "CS AKTIF";
      case "RESOLVED":
        return "SELESAI";
      case "CLOSED":
        return "DITUTUP";
      case "BOT_ACTIVE":
      default:
        return "AI BOT";
    }
  }
}
