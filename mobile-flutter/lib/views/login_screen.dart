import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../core/constants.dart';
import 'ticket_list_screen.dart';

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
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final token = data['access_token'];
        final agentName = data['full_name'];

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => TicketListScreen(token: token, agentName: agentName),
          ),
        );
      } else {
        setState(() {
          _errorMsg = "Email atau password salah.";
        });
      }
    } catch (e) {
      setState(() {
        _errorMsg = "Gagal terhubung ke server: $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.bgDark,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Container(
            constraints: const BoxConstraints(maxWidth: 400),
            padding: const EdgeInsets.all(28.0),
            decoration: BoxDecoration(
              color: AppConstants.cardDark,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppConstants.borderDark),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.asset(
                      'assets/ciheul-logo.png',
                      width: 64,
                      height: 64,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                const Center(
                  child: Text(
                    "CIHEUL Support Mobile",
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppConstants.textLight,
                    ),
                  ),
                ),
                const Center(
                  child: Text(
                    "Omnichannel CS Agent Console",
                    style: TextStyle(
                      fontSize: 12,
                      color: AppConstants.textMuted,
                    ),
                  ),
                ),
                const SizedBox(height: 28),
                if (_errorMsg != null)
                  Container(
                    padding: const EdgeInsets.all(10),
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: Colors.red.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
                    ),
                    child: Text(
                      _errorMsg!,
                      style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                    ),
                  ),
                TextField(
                  controller: _hostCtrl,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: const InputDecoration(
                    labelText: "Server Host & Port",
                    labelStyle: TextStyle(color: AppConstants.textMuted, fontSize: 12),
                    prefixIcon: Icon(Icons.dns, size: 18, color: AppConstants.textMuted),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _emailCtrl,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: const InputDecoration(
                    labelText: "Email Akun CS",
                    labelStyle: TextStyle(color: AppConstants.textMuted, fontSize: 12),
                    prefixIcon: Icon(Icons.email_outlined, size: 18, color: AppConstants.textMuted),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passCtrl,
                  obscureText: true,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: const InputDecoration(
                    labelText: "Kata Sandi",
                    labelStyle: TextStyle(color: AppConstants.textMuted, fontSize: 12),
                    prefixIcon: Icon(Icons.lock_outline, size: 18, color: AppConstants.textMuted),
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppConstants.primaryBlue,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Text(
                          "Masuk ke Workspace",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
