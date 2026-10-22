import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AppConstants {
  // Configurable API & WebSocket URLs
  // In release/production mode, enforce secure https and wss protocols
  static const bool isProduction = kReleaseMode;
  
  // For Android emulator: 10.0.2.2:8000; For Windows desktop: localhost:8000; For Production: api.ciheul.com
  static String devHost = const String.fromEnvironment('API_HOST', defaultValue: '10.0.2.2:8000');
  static String prodHost = const String.fromEnvironment('PROD_API_HOST', defaultValue: 'api.ciheul.com');

  static String get host => isProduction ? prodHost : devHost;
  static set host(String value) {
    if (!isProduction) {
      devHost = value;
    }
  }
  static String get protocol => isProduction ? 'https' : 'http';
  static String get wsProtocol => isProduction ? 'wss' : 'ws';

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
}
