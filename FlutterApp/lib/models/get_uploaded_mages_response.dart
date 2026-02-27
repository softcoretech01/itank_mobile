class GetUploadedImagesResponse {
  final bool success;
  final UploadedImagesData? data;
  final String? message;

  GetUploadedImagesResponse({
    required this.success,
    this.data,
    this.message,
  });

  factory GetUploadedImagesResponse.fromJson(Map<String, dynamic> json) {
    return GetUploadedImagesResponse(
      success: json["success"] ?? false,
      message: json["message"],
      data: json["data"] != null
          ? UploadedImagesData.fromJson(json["data"])
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    "success": success,
    "message": message,
    "data": data?.toJson(),
  };
}
class UploadedImagesData {
  final String inspectionId;
  final String tankId;
  final String empId;
  final List<UploadedImage> images;

  UploadedImagesData({
    required this.inspectionId,
    required this.tankId,
    required this.empId,
    required this.images,
  });

  factory UploadedImagesData.fromJson(Map<String, dynamic> json) {
    return UploadedImagesData(
      inspectionId: json["inspection_id"].toString(),
      tankId: json["tank_id"].toString(),
      empId: json["emp_id"]?.toString() ?? "",
      images: (json["images"] as List<dynamic>)
          .map((e) => UploadedImage.fromJson(e))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    "inspection_id": inspectionId,
    "tank_id": tankId,
    "emp_id": empId,
    "images": images.map((e) => e.toJson()).toList(),
  };
}

class UploadedImage {
  final int id;
  final int? empId;
  final int inspectionId;
  final int imageId;
  final String imagePath;
  final String? thumbnailPath;
  final String? createdDate;
  final String createdAt;
  final String updatedAt;
  final int imageTypeId;
  final int tankId;

  UploadedImage({
    required this.id,
    this.empId,
    required this.inspectionId,
    required this.imageId,
    required this.imagePath,
    this.thumbnailPath,
    this.createdDate,
    required this.createdAt,
    required this.updatedAt,
    required this.imageTypeId,
    required this.tankId,
  });

  factory UploadedImage.fromJson(Map<String, dynamic> json) {
    return UploadedImage(
      id: json["id"],
      empId: json["emp_id"],
      inspectionId: json["inspection_id"],
      imageId: json["image_id"],
      imagePath: json["image_path"] ?? "",
      thumbnailPath: json["thumbnail_path"],
      createdDate: json["created_date"],
      createdAt: json["created_at"] ?? "",
      updatedAt: json["updated_at"] ?? "",
      imageTypeId: json["image_type_id"],
      tankId: json["tank_id"],
    );
  }

  Map<String, dynamic> toJson() => {
    "id": id,
    "emp_id": empId,
    "inspection_id": inspectionId,
    "image_id": imageId,
    "image_path": imagePath,
    "thumbnail_path": thumbnailPath,
    "created_date": createdDate,
    "created_at": createdAt,
    "updated_at": updatedAt,
    "image_type_id": imageTypeId,
    "tank_id": tankId,
  };
}

