import 'package:flutter/material.dart';

class AppConstants {
  // Configurable API & WebSocket URLs
  // For Android emulator: 10.0.2.2; For Windows desktop or web: localhost; For Physical device: your LAN IP (e.g. 192.168.1.X)
  static String host = "10.0.2.2:8000"; 
  
  static String get apiBaseUrl => "http://$host";
  static String get wsBaseUrl => "ws://$host";

  // Corporate Slate Dark Theme Colors
  static const Color bgDark = Color(0xFF060A12);
  static const Color cardDark = Color(0xFF0F172A);
  static const Color borderDark = Color(0xFF1E293B);
  static const Color primaryBlue = Color(0xFF0284C7);
  static const Color accentIndigo = Color(0xFF4F46E5);
  static const Color textLight = Color(0xFFF8FAFC);
  static const Color textMuted = Color(0xFF94A3B8);
}
