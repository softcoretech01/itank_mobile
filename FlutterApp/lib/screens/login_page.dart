import 'package:flutter/material.dart';
import 'package:iso_tank/service/secure_storage_service.dart';

import '../models/post.dart';
import '../repository/auth_repository.dart';
import '../service/ApiClient.dart';
import '../service/DioProvider.dart';
import '../utils/app_colors.dart';
import 'tank_inspection/tank_inspection_flow.dart';


class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _isLoading = false;
  List<Post> posts = [];
  AuthRepository? authRepository;

  @override
  void initState() {
    super.initState();
    final dio = DioProvider.createDio();
    authRepository = AuthRepository(ApiClient(dio));
  }

  void _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final response = await authRepository!.login(
        loginName: _usernameController.text.trim(),
        password: _passwordController.text.trim(),
      );

      if (response.success == true) {
        await secureStorage.saveToken(response.data?.token ?? "");

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const TankInspectionFlow()),
        );
      } else {
        _showError(response.message ?? "Invalid login");
      }
    } catch (e) {
      print("e=====");
      print(e);
      _showError("Something went wrong. Please try again.");
    }

    setState(() => _isLoading = false);
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        // Apply gradient background
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
            colors: [
              AppColors.primarySwatch[700]!, // deeper blue
              AppColors.primarySwatch[200]!, // light blue
            ],
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Card(
              elevation: 8,
              shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      ShaderMask(
                        shaderCallback: (bounds) => const LinearGradient(
                          colors: [Color(0xFF0066FF), Color(0xFF00C2A8)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ).createShader(bounds),
                        child: const Text(
                          "iTank",
                          style: TextStyle(
                            fontSize: 48,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.5,
                            color: Colors.white, // required for ShaderMask
                          ),
                        ),
                      ),
                      Image.asset('assets/images/smart_gas.png', height: 100,),
                      SizedBox(height: 20,),
                      const Text(
                        "Welcome Back",
                        style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        "Please sign in to continue",
                        style: TextStyle(color: Colors.black54),
                      ),
                      const SizedBox(height: 32),

                      // Username Field
                      TextFormField(
                        controller: _usernameController,
                        decoration: InputDecoration(
                          labelText: "Username",
                          prefixIcon: const Icon(Icons.person_outline),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        validator: (value) =>
                        value!.isEmpty ? "Enter your username" : null,
                      ),
                      const SizedBox(height: 16),

                      // Password Field
                      TextFormField(
                        controller: _passwordController,
                        obscureText: _obscurePassword,
                        decoration: InputDecoration(
                          labelText: "Password",
                          prefixIcon: const Icon(Icons.lock_outline),
                          suffixIcon: IconButton(
                            icon: Icon(_obscurePassword
                                ? Icons.visibility_off
                                : Icons.visibility),
                            onPressed: () => setState(
                                    () => _obscurePassword = !_obscurePassword),
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        validator: (value) =>
                        value!.isEmpty ? "Enter your password" : null,
                      ),
                      const SizedBox(height: 24),

                      // Login Button
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _login,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12)),
                          ),
                          child: _isLoading
                              ? const CircularProgressIndicator(
                              color: Colors.white)
                              : const Text(
                            "Login",
                            style: TextStyle(
                                fontSize: 18, color: Colors.white),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      /*// Forgot Password
                      TextButton(
                        onPressed: () {},
                        child: const Text("Forgot Password?"),
                      ),

                      const Divider(height: 32),

                      // Sign Up
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text("Don't have an account? "),
                          TextButton(
                            onPressed: () {},
                            child: const Text(
                              "Sign Up",
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                          )
                        ],
                      ),*/
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
