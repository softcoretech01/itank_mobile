import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/login_response.dart';

class SecureStorageService {
  static const String _keyToken = "auth_token";
  static const String _keyIsLoggedIn = "is_logged_in";
  static const String _keyLoginData = "auth_login_data";

  final _storage = const FlutterSecureStorage();

  Future<void> saveToken(String token) async {
    await _storage.write(key: _keyToken, value: token);
  }

  Future<String?> getToken() async {
    return await _storage.read(key: _keyToken);
  }

  /// Persist login state so app can open directly to tank inspection when already logged in.
  Future<void> saveIsLoggedIn(bool value) async {
    await _storage.write(key: _keyIsLoggedIn, value: value.toString());
  }

  Future<bool> getIsLoggedIn() async {
    final value = await _storage.read(key: _keyIsLoggedIn);
    return value == "true";
  }

  /// Save login response (e.g. email, token) for local auth state.
  Future<void> saveLoginData(LoginData? data) async {
    if (data == null) {
      await _storage.delete(key: _keyLoginData);
      return;
    }
    await _storage.write(
      key: _keyLoginData,
      value: jsonEncode(data.toJson()),
    );
  }

  Future<LoginData?> getLoginData() async {
    final raw = await _storage.read(key: _keyLoginData);
    if (raw == null || raw.isEmpty) return null;
    try {
      return LoginData.fromJson(
        jsonDecode(raw) as Map<String, dynamic>,
      );
    } catch (_) {
      return null;
    }
  }

  Future<void> clear() async {
    await _storage.deleteAll();
  }
}

final secureStorage = SecureStorageService();
