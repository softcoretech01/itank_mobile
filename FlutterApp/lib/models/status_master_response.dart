class StatusMasterResponse {
  final bool success;
  final List<StatusData> data;

  StatusMasterResponse({
    required this.success,
    required this.data,
  });

  factory StatusMasterResponse.fromJson(Map<String, dynamic> json) {
    return StatusMasterResponse(
      success: json['success'] ?? false,
      data: (json['data'] as List<dynamic>?)
          ?.map((e) => StatusData.fromJson(e))
          .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'data': data.map((e) => e.toJson()).toList(),
    };
  }

  StatusMasterResponse copyWith({
    bool? success,
    List<StatusData>? data,
  }) {
    return StatusMasterResponse(
      success: success ?? this.success,
      data: data ?? this.data,
    );
  }
}

class StatusData {
  final int statusId;
  final String statusName;
  final String description;
  final int sortOrder;
  final String? createdAt;
  final String? updatedAt;

  StatusData({
    required this.statusId,
    required this.statusName,
    required this.description,
    required this.sortOrder,
    this.createdAt,
    this.updatedAt,
  });

  factory StatusData.fromJson(Map<String, dynamic> json) {
    return StatusData(
      statusId: json['id'] ?? 0,
      statusName: json['name'] ?? '',
      description: json['description'] ?? '',
      sortOrder: json['sort_order'] ?? 0,
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': statusId,
      'name': statusName,
      'description': description,
      'sort_order': sortOrder,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }

  StatusData copyWith({
    int? statusId,
    String? statusName,
    String? description,
    int? sortOrder,
    String? createdAt,
    String? updatedAt,
  }) {
    return StatusData(
      statusId: statusId ?? this.statusId,
      statusName: statusName ?? this.statusName,
      description: description ?? this.description,
      sortOrder: sortOrder ?? this.sortOrder,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}
