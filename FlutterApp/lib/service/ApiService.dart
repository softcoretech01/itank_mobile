import 'package:dio/dio.dart';

import 'secure_storage_service.dart';

class ApiService {
  late Dio _dio;

  ApiService() {
    _dio = Dio(
      BaseOptions(
        // Align timeouts with main DioProvider and give slower endpoints more room
        connectTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),
        headers: {
          'Content-Type': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await secureStorage.getToken();
          if (token != null) {
            options.headers["Authorization"] = "Bearer $token";
          }
          handler.next(options);
        },
      ),
    );

    _dio.interceptors.add(LogInterceptor(
      request: true,
      requestBody: true,
      requestHeader: true,
      responseBody: true,
    ));
  }

  // GET request
  Future<Response> getData(String endpoint) async {
    try {
      final response = await _dio.get(endpoint);
      return response;
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  // POST request
  Future<Response> postData(String endpoint, Map<String, dynamic> data) async {
    try {
      return await _dio.post(endpoint, data: data);
    } on DioException catch (e) {
      // If backend sent JSON (422, 400, 500...)
      if (e.response != null) {
        return e.response!;
      }

      // No response (internet issues)
      throw Exception(_handleError(e));
    }
  }

  // Error handling
  String _handleError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
        return "Connection Timeout";
      case DioExceptionType.sendTimeout:
        return "Send Timeout";
      case DioExceptionType.receiveTimeout:
        return "Receive Timeout";
      case DioExceptionType.badResponse:
        return "Server Error: ${error.response?.statusCode}";
      case DioExceptionType.cancel:
        return "Request Cancelled";
      case DioExceptionType.unknown:
      default:
        return "Unexpected Error: ${error.message}";
    }
  }
}
