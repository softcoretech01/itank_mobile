class ApiResult {
  final bool success;
  final dynamic data;
  final String? message;

  ApiResult({
    required this.success,
    this.data,
    this.message,
  });

  /// Success factory
  factory ApiResult.success(dynamic data) =>
      ApiResult(success: true, data: data);

  /// Error factory
  factory ApiResult.error(String message, [dynamic data]) =>
      ApiResult(success: false, message: message, data: data);

  /// FROM JSON
  factory ApiResult.fromJson(Map<String, dynamic> json) {
    return ApiResult(
      success: json['success'] ?? false,
      data: json['data'],
      message: json['message'],
    );
  }

  /// TO JSON
  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'data': data,
      'message': message,
    };
  }

  /// COPYWITH
  ApiResult copyWith({
    bool? success,
    dynamic data,
    String? message,
  }) {
    return ApiResult(
      success: success ?? this.success,
      data: data ?? this.data,
      message: message ?? this.message,
    );
  }
}

class ApiValidationError {
  final String type;
  final List<String> loc;
  final String msg;
  final dynamic input;

  ApiValidationError({
    required this.type,
    required this.loc,
    required this.msg,
    this.input,
  });

  factory ApiValidationError.fromJson(Map<String, dynamic> json) {
    return ApiValidationError(
      type: json['type'] ?? "",
      loc: List<String>.from(json['loc'] ?? []),
      msg: json['msg'] ?? "",
      input: json['input'],
    );
  }
}

class ApiErrorResponse {
  final List<ApiValidationError> detail;

  ApiErrorResponse({
    required this.detail,
  });

  factory ApiErrorResponse.fromJson(Map<String, dynamic> json) {
    return ApiErrorResponse(
      detail: (json['detail'] as List<dynamic>?)
          ?.map((e) => ApiValidationError.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
    );
  }
}



