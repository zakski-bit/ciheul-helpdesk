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
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppConstants.bgDark,
        primaryColor: AppConstants.primaryBlue,
        colorScheme: const ColorScheme.dark(
          primary: AppConstants.primaryBlue,
          secondary: AppConstants.accentIndigo,
          surface: AppConstants.cardDark,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: AppConstants.cardDark,
          elevation: 0,
        ),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
    );
  }
}
