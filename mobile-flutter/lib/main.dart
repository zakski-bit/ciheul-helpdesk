import 'package:flutter/material.dart';
import 'core/constants.dart';
import 'views/login_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const CiheulHelpdeskApp());
}

class CiheulHelpdeskApp extends StatelessWidget {
  const CiheulHelpdeskApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CIHEUL Helpdesk Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: AppConstants.bgLight,
        primaryColor: AppConstants.primaryBlue,
        colorScheme: const ColorScheme.light(
          primary: AppConstants.primaryBlue,
          secondary: AppConstants.copilotAccent,
          surface: AppConstants.cardLight,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: AppConstants.cardLight,
          foregroundColor: AppConstants.textPrimary,
          elevation: 0,
          scrolledUnderElevation: 0,
        ),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
    );
  }
}
