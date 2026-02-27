class OperatorsResponse {
  final bool? success;
  final String? message;
  final List<OperatorData>? data;

  OperatorsResponse({
    this.success,
    this.message,
    this.data,
  });

  // fromJson
  factory OperatorsResponse.fromJson(Map<String, dynamic> json) {
    return OperatorsResponse(
      success: json['success'],
      message: json['message'],
      data: (json['data'] as List?)
          ?.map((e) => OperatorData.fromJson(e))
          .toList(),
    );
  }

  // toJson
  Map<String, dynamic> toJson() => {
    'success': success,
    'message': message,
    'data': data?.map((e) => e.toJson()).toList(),
  };

  // copyWith
  OperatorsResponse copyWith({
    bool? success,
    String? message,
    List<OperatorData>? data,
  }) {
    return OperatorsResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      data: data ?? this.data,
    );
  }
}

class OperatorData {
  final int? empId;
  final String? name;

  OperatorData({
    this.empId,
    this.name,
  });

  // fromJson
  factory OperatorData.fromJson(Map<String, dynamic> json) {
    return OperatorData(
      empId: json['emp_id'],
      name: json['name'],
    );
  }

  // toJson
  Map<String, dynamic> toJson() => {
    'emp_id': empId,
    'name': name,
  };

  // copyWith
  OperatorData copyWith({
    int? empId,
    String? name,
  }) {
    return OperatorData(
      empId: empId ?? this.empId,
      name: name ?? this.name,
    );
  }
}
