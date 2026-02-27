class SubmitReviewResponse {
  final bool? success;
  final String? message;
  final Data? data;

  SubmitReviewResponse({
    this.success,
    this.message,
    this.data,
  });

  // ---------- FROM JSON ----------
  factory SubmitReviewResponse.fromJson(Map<String, dynamic> json) {
    return SubmitReviewResponse(
      success: json['success'] as bool?,
      message: json['message'] as String?,
      data: json['data'] != null
          ? Data.fromJson(json['data'])
          : null,
    );
  }

  // ---------- TO JSON ----------
  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'message': message,
      'data': data?.toJson(),
    };
  }

  // ---------- COPYWITH ----------
  SubmitReviewResponse copyWith({
    bool? success,
    String? message,
    Data? data,
  }) {
    return SubmitReviewResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      data: data ?? this.data,
    );
  }
}

class Data {
  final int? inspectionId;
  final String? status;

  Data({
    this.inspectionId,
    this.status,
  });

  // ---------- FROM JSON ----------
  factory Data.fromJson(Map<String, dynamic> json) {
    return Data(
      inspectionId: json['inspection_id'],
      status: json['status']?.toString(),

    );
  }

  // ---------- TO JSON ----------
  Map<String, dynamic> toJson() {
    return {
      'inspection_id': inspectionId,
      'status': status,
    };
  }

  // ---------- COPYWITH ----------
  Data copyWith({
    int? inspectionId,
    String? status,

  }) {
    return Data(
      inspectionId: inspectionId ?? this.inspectionId,
      status: status ?? this.status,
    );
  }
}
