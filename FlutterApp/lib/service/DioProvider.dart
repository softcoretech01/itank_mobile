import 'package:dio/dio.dart';
import '../utils/constants.dart'; // ✅ REQUIRED for BASE_URL
import 'secure_storage_service.dart';

class DioProvider {
  static Dio createDio() {
    final dio = Dio(
      BaseOptions(
        baseUrl: BASE_URL,
        // Increase timeouts to reduce spurious connection timeout errors
        connectTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),

        // 🔥 VERY IMPORTANT FOR 400 VALIDATION RESPONSES
        validateStatus: (status) {
          return status != null && status < 500;
        },
      ),
    );

    // ✅ Logging interceptor
    dio.interceptors.add(
      LogInterceptor(
        request: true,
        requestHeader: true,
        requestBody: true,
        responseBody: true,
        responseHeader: false,
        error: true,
      ),
    );

    // 🔒 Auth interceptor – attach Bearer token on every request (except login)
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final path = options.path;

          // Skip auth endpoints that should not send token
          if (path.contains('auth/login')) {
            return handler.next(options);
          }

          final token = await secureStorage.getToken();

          // Only attach if we actually have a token and the header isn't already set
          if (token != null &&
              token.isNotEmpty &&
              !options.headers.containsKey('Authorization')) {
            options.headers['Authorization'] = 'Bearer $token';
          }

          handler.next(options);
        },
      ),
    );

    return dio;
  }
}
