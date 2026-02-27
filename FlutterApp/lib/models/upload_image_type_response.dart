class UploadImageTypeResponse {
  final bool success;
  final List<UploadImageType> data;

  UploadImageTypeResponse({
    required this.success,
    required this.data,
  });

  factory UploadImageTypeResponse.fromJson(Map<String, dynamic> json) {
    return UploadImageTypeResponse(
      success: json['success'] ?? false,
      data: (json['data'] as List<dynamic>?)
          ?.map((e) => UploadImageType.fromJson(e))
          .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "success": success,
      "data": data.map((e) => e.toJson()).toList(),
    };
  }

  UploadImageTypeResponse copyWith({
    bool? success,
    List<UploadImageType>? data,
  }) {
    return UploadImageTypeResponse(
      success: success ?? this.success,
      data: data ?? this.data,
    );
  }
}

class UploadImageType {
  final int imageTypeId;
  final String imageType;
  final String description;
  final int count;

  UploadImageType({
    required this.imageTypeId,
    required this.imageType,
    required this.description,
    required this.count,
  });

  factory UploadImageType.fromJson(Map<String, dynamic> json) {
    return UploadImageType(
      imageTypeId: json["image_type_id"] ?? 0,
      imageType: json["image_type"] ?? "",
      description: json["description"] ?? "",
      count: json["count"] ?? 1,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "image_type_id": imageTypeId,
      "image_type": imageType,
      "description": description,
      "count": count,
    };
  }

  UploadImageType copyWith({
    int? imageTypeId,
    String? imageType,
    String? description,
    int? count,
  }) {
    return UploadImageType(
      imageTypeId: imageTypeId ?? this.imageTypeId,
      imageType: imageType ?? this.imageType,
      description: description ?? this.description,
      count: count ?? this.count,
    );
  }
}
