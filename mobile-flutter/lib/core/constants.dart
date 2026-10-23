import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AppConstants {
  // Configurable API & WebSocket URLs
  // In release/production mode, enforce secure https and wss protocols
  static const bool isProduction = kReleaseMode;
  
  // Default to localhost:8000 (suitable for adb reverse or local testing)
  static String _activeHost = const String.fromEnvironment('API_HOST', defaultValue: 'localhost:8000');

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

  // Corporate Slate Dark Theme Colors
  static const Color bgDark = Color(0xFF060A12);
  static const Color cardDark = Color(0xFF0F172A);
  static const Color borderDark = Color(0xFF1E293B);
  static const Color primaryBlue = Color(0xFF0284C7);
  static const Color accentIndigo = Color(0xFF4F46E5);
  static const Color textLight = Color(0xFFF8FAFC);
  static const Color textMuted = Color(0xFF94A3B8);

  static Color getStatusColor(String status) {
    switch (status) {
      case "WAITING_AGENT":
        return const Color(0xFFF59E0B);
      case "AGENT_ACTIVE":
        return const Color(0xFF0284C7);
      case "RESOLVED":
      case "CLOSED":
        return const Color(0xFF10B981);
      case "BOT_ACTIVE":
      default:
        return const Color(0xFF6366F1);
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
