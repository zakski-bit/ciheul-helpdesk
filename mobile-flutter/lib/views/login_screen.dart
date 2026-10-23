import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../core/constants.dart';
import 'main_navigation_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController(text: "cs@ciheul.com");
  final _passCtrl = TextEditingController(text: "cs123");
  final _hostCtrl = TextEditingController(text: AppConstants.host);
  bool _isLoading = false;
  String? _errorMsg;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    _hostCtrl.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    setState(() {
      _isLoading = true;
      _errorMsg = null;
      AppConstants.host = _hostCtrl.text.trim();
    });

    try {
      final res = await http.post(
        Uri.parse("${AppConstants.apiBaseUrl}/api/v1/auth/login"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "email": _emailCtrl.text.trim(),
          "password": _passCtrl.text.trim(),
        }),
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final token = data['access_token'];
        final agentName = data['full_name'];

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => MainNavigationScreen(token: token, agentName: agentName),
          ),
        );
      } else {
        setState(() {
          _errorMsg = "Email atau kata sandi tidak cocok.";
        });
      }
    } on TimeoutException {
      setState(() {
        _errorMsg = "Koneksi ke server timeout (melebihi 6 detik). Pastikan server backend aktif dan periksa opsi Host (USB atau Wi-Fi).";
      });
    } catch (e) {
      setState(() {
        _errorMsg = "Gagal terhubung ke ${_hostCtrl.text.trim()}: $e";
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _fillAccount(String email, String pass) {
    setState(() {
      _emailCtrl.text = email;
      _passCtrl.text = pass;
      _errorMsg = null;
    });
  }

  void _setHost(String newHost) {
    setState(() {
      _hostCtrl.text = newHost;
      AppConstants.host = newHost;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.bgLight,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 32.0),
          child: Container(
            constraints: const BoxConstraints(maxWidth: 420),
            padding: const EdgeInsets.all(28.0),
            decoration: BoxDecoration(
              color: AppConstants.cardLight,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppConstants.borderLight),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.04),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header Logo & Title matching Web Dashboard Modal
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Image.asset(
                        'assets/ciheul-logo.png',
                        width: 42,
                        height: 42,
                        fit: BoxFit.contain,
                      ),
                    ),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Masuk ke Helpdesk",
                            style: TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.bold,
                              color: AppConstants.textPrimary,
                              letterSpacing: -0.2,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            "CIHEUL Technologies Omnichannel Support",
                            style: TextStyle(
                              fontSize: 11,
                              color: AppConstants.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 22),

                // Error alert box
                if (_errorMsg != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.only(bottom: 18),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEF2F2),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFFECACA)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.error_outline, color: Color(0xFFDC2626), size: 18),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _errorMsg!,
                            style: const TextStyle(color: Color(0xFFB91C1C), fontSize: 11.5, height: 1.35),
                          ),
                        ),
                      ],
                    ),
                  ),

                // Host Selector
                const Text(
                  "Koneksi Server",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF374151),
                  ),
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          side: BorderSide(
                            color: _hostCtrl.text == AppConstants.defaultUsbHost
                                ? AppConstants.primaryBlue
                                : AppConstants.borderLight,
                            width: _hostCtrl.text == AppConstants.defaultUsbHost ? 1.5 : 1,
                          ),
                          backgroundColor: _hostCtrl.text == AppConstants.defaultUsbHost
                              ? const Color(0xFFE0F2FE)
                              : AppConstants.bgLight,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        onPressed: () => _setHost(AppConstants.defaultUsbHost),
                        child: Text(
                          "USB ADB (127.0.0.1)",
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: _hostCtrl.text == AppConstants.defaultUsbHost
                                ? AppConstants.primaryBlue
                                : AppConstants.textSecondary,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          side: BorderSide(
                            color: _hostCtrl.text == AppConstants.defaultWifiHost
                                ? AppConstants.primaryBlue
                                : AppConstants.borderLight,
                            width: _hostCtrl.text == AppConstants.defaultWifiHost ? 1.5 : 1,
                          ),
                          backgroundColor: _hostCtrl.text == AppConstants.defaultWifiHost
                              ? const Color(0xFFE0F2FE)
                              : AppConstants.bgLight,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        onPressed: () => _setHost(AppConstants.defaultWifiHost),
                        child: Text(
                          "Wi-Fi LAN (PC IP)",
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: _hostCtrl.text == AppConstants.defaultWifiHost
                                ? AppConstants.primaryBlue
                                : AppConstants.textSecondary,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _hostCtrl,
                  style: const TextStyle(color: AppConstants.textPrimary, fontSize: 12.5),
                  decoration: InputDecoration(
                    hintText: "Contoh: 127.0.0.1:8000",
                    hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                    filled: true,
                    fillColor: AppConstants.bgLight,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.borderLight),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.borderLight),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.primaryBlue, width: 1.5),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // Email Field
                const Text(
                  "Email Staf",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF374151),
                  ),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: _emailCtrl,
                  style: const TextStyle(color: AppConstants.textPrimary, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: "cs@ciheul.com",
                    hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                    filled: true,
                    fillColor: AppConstants.bgLight,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.borderLight),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.borderLight),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.primaryBlue, width: 1.5),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // Password Field
                const Text(
                  "Kata Sandi",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF374151),
                  ),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: _passCtrl,
                  obscureText: true,
                  style: const TextStyle(color: AppConstants.textPrimary, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: "Masukkan kata sandi",
                    hintStyle: const TextStyle(color: AppConstants.textMuted, fontSize: 12),
                    filled: true,
                    fillColor: AppConstants.bgLight,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.borderLight),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.borderLight),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: AppConstants.primaryBlue, width: 1.5),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Submit Button
                SizedBox(
                  height: 44,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleLogin,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppConstants.primaryBlue,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            "Masuk",
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                  ),
                ),

                // Quick Demo Account Buttons matching Web Dashboard
                const SizedBox(height: 22),
                const Divider(color: AppConstants.borderSubtle),
                const SizedBox(height: 10),
                const Center(
                  child: Text(
                    "Akun Demo Pengujian Cepat",
                    style: TextStyle(fontSize: 11, color: Color(0xFF9CA3AF), fontWeight: FontWeight.w500),
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        style: TextButton.styleFrom(
                          backgroundColor: AppConstants.borderSubtle,
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        onPressed: () => _fillAccount("cs@ciheul.com", "cs123"),
                        child: const Text(
                          "Isi CS Support",
                          style: TextStyle(color: Color(0xFF374151), fontSize: 11.5, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextButton(
                        style: TextButton.styleFrom(
                          backgroundColor: AppConstants.borderSubtle,
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        onPressed: () => _fillAccount("admin@ciheul.com", "admin123"),
                        child: const Text(
                          "Isi Administrator",
                          style: TextStyle(color: Color(0xFF374151), fontSize: 11.5, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
