class LoginRequest {
  final String loginName;
  final String password;

  LoginRequest({
    required this.loginName,
    required this.password,
  });

  Map<String, dynamic> toJson() => {
    "login_name": loginName,
    "password": password,
  };

  LoginRequest copyWith({
    String? loginName,
    String? password,
  }) {
    return LoginRequest(
      loginName: loginName ?? this.loginName,
      password: password ?? this.password,
    );
  }
}
