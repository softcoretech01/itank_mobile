class LoginResponse {
  final bool? success;
  final String? message;
  final LoginData? data;

  LoginResponse({
    this.success,
    this.message,
    this.data,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) =>
      LoginResponse(
        success: json["success"],
        message: json["message"],
        data: json["data"] != null
            ? LoginData.fromJson(json["data"])
            : null,
      );

  Map<String, dynamic> toJson() => {
    "success": success,
    "message": message,
    "data": data?.toJson(),
  };

  LoginResponse copyWith({
    bool? success,
    String? message,
    LoginData? data,
  }) {
    return LoginResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      data: data ?? this.data,
    );
  }
}

class LoginData {
  final String? email;
  final String? token;

  LoginData({
    this.email,
    this.token,
  });

  factory LoginData.fromJson(Map<String, dynamic> json) => LoginData(
    email: json["email"],
    token: json["token"],
  );

  Map<String, dynamic> toJson() => {
    "email": email,
    "token": token,
  };

  LoginData copyWith({
    String? email,
    String? token,
  }) {
    return LoginData(
      email: email ?? this.email,
      token: token ?? this.token,
    );
  }
}
