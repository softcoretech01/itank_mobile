
import '../models/login_response.dart';
import '../models/request/login_request.dart';
import '../service/ApiClient.dart';
import '../service/secure_storage_service.dart';

class AuthRepository {
  final ApiClient api;

  AuthRepository(this.api);

  Future<LoginResponse> login({
    required String loginName,
    required String password,
  }) async {
    final request = LoginRequest(loginName: loginName, password: password);

    final response = await api.login(request);

    if (response.success == true && response.data?.token != null) {
      await secureStorage.saveToken(response.data!.token!);
    }

    return response;
  }

  Future<void> logout() async {
    try {
      final token = await secureStorage.getToken();
      if (token != null && token.isNotEmpty) {
        // Best effort API logout
        try {
          // If token doesn't have "Bearer " prefix in storage, add it. 
          // Assuming storage has raw token based on login method.
          await api.logout("Bearer $token");
        } catch (_) {
          // Proceed to clear local data even if API fails
        }
      }
    } catch (_) {
      // Safety/fallback
    }
    // Always clear local storage
    await secureStorage.clear();
  }
}
