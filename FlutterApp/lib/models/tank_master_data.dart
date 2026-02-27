class TankMasterResponse {
  bool? success;
  String? message;
  TankMasterData? data;

  TankMasterResponse({this.success, this.message, this.data});

  factory TankMasterResponse.fromJson(Map<String, dynamic> json) {
    return TankMasterResponse(
      success: json["success"],
      message: json["message"],
      data: json["data"] != null
          ? TankMasterData.fromJson(json["data"])
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    "success": success,
    "message": message,
    "data": data?.toJson(),
  };
}


class TankMasterData {
  List<TankStatus>? tankStatuses;
  List<Product>? products;
  List<InspectionType>? inspectionTypes;
  List<Location>? locations;
  List<SafetyValve>? safetyValveBrands;
  List<SafetyValveModel>? safetyValveModels;
  List<SafetyValveSize>? safetyValveSizes;

  TankMasterData({
    this.tankStatuses,
    this.products,
    this.inspectionTypes,
    this.locations,
    this.safetyValveBrands,
    this.safetyValveModels,
    this.safetyValveSizes,
  });

  factory TankMasterData.fromJson(Map<String, dynamic> json) {
    return TankMasterData(
      tankStatuses: (json['tank_statuses'] as List?)
          ?.map((e) => TankStatus.fromJson(e))
          .toList(),
      products: (json['products'] as List?)
          ?.map((e) => Product.fromJson(e))
          .toList(),
      inspectionTypes: (json['inspection_types'] as List?)
          ?.map((e) => InspectionType.fromJson(e))
          .toList(),
      locations: (json['locations'] as List?)
          ?.map((e) => Location.fromJson(e))
          .toList(),
      safetyValveBrands: (json['safety_valve_brands'] as List?)
          ?.map((e) => SafetyValve.fromJson(e))
          .toList(),
      safetyValveModels: (json['safety_valve_models'] as List?)
          ?.map((e) => SafetyValveModel.fromJson(e))
          .toList(),
      safetyValveSizes: (json['safety_valve_sizes'] as List?)
          ?.map((e) => SafetyValveSize.fromJson(e))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    "tank_statuses": tankStatuses?.map((e) => e.toJson()).toList(),
    "products": products?.map((e) => e.toJson()).toList(),
    "inspection_types": inspectionTypes?.map((e) => e.toJson()).toList(),
    "locations": locations?.map((e) => e.toJson()).toList(),
    "safety_valve_brands": safetyValveBrands?.map((e) => e.toJson()).toList(),
    "safety_valve_models": safetyValveModels?.map((e) => e.toJson()).toList(),
    "safety_valve_sizes": safetyValveSizes?.map((e) => e.toJson()).toList(),
  };
}

class TankStatus {
  int? statusId;
  String? statusName;
  String? description;
  String? createdAt;
  String? updatedAt;

  TankStatus({
    this.statusId,
    this.statusName,
    this.description,
    this.createdAt,
    this.updatedAt,
  });

  factory TankStatus.fromJson(Map<String, dynamic> json) {
    return TankStatus(
      statusId: json['status_id'],
      statusName: json['status_name'],
      description: json['description'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() => {
    "status_id": statusId,
    "status_name": statusName,
    "description": description,
    "created_at": createdAt,
    "updated_at": updatedAt,
  };
}

class Product {
  int? productId;
  String? productName;
  String? description;
  String? createdAt;
  String? updatedAt;

  Product({this.productId, this.productName, this.description, this.createdAt, this.updatedAt});

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      productId: json['product_id'],
      productName: json['product_name'],
      description: json['description'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() => {
    "product_id": productId,
    "product_name": productName,
    "description": description,
    "created_at": createdAt,
    "updated_at": updatedAt,
  };
}

class InspectionType {
  int? inspectionTypeId;
  String? inspectionTypeName;
  String? description;
  String? createdAt;
  String? updatedAt;

  InspectionType({this.inspectionTypeId, this.inspectionTypeName, this.description, this.createdAt, this.updatedAt});

  factory InspectionType.fromJson(Map<String, dynamic> json) {
    return InspectionType(
      inspectionTypeId: json['inspection_type_id'],
      inspectionTypeName: json['inspection_type_name'],
      description: json['description'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() => {
    "inspection_type_id": inspectionTypeId,
    "inspection_type_name": inspectionTypeName,
    "description": description,
    "created_at": createdAt,
    "updated_at": updatedAt,
  };
}

class Location {
  int? locationId;
  String? locationName;
  String? description;
  String? createdAt;
  String? updatedAt;

  Location({this.locationId, this.locationName, this.description, this.createdAt, this.updatedAt});

  factory Location.fromJson(Map<String, dynamic> json) {
    return Location(
      locationId: json['location_id'],
      locationName: json['location_name'],
      description: json['description'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() => {
    "location_id": locationId,
    "location_name": locationName,
    "description": description,
    "created_at": createdAt,
    "updated_at": updatedAt,
  };
}

class SafetyValve {
  int? id;
  String? brandName;
  String? description;
  String? createdAt;
  String? updatedAt;
  String? modelName;
  String? sizeLabel;

  SafetyValve({this.id, this.brandName, this.description, this.createdAt, this.updatedAt, this.modelName, this.sizeLabel});

  factory SafetyValve.fromJson(Map<String, dynamic> json) {
    return SafetyValve(
      id: json['id'],
      brandName: json['brand_name'],
      description: json['description'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
      modelName: json['model_name'],
      sizeLabel: json['size_label'],
    );
  }

  Map<String, dynamic> toJson() => {
    "id": id,
    "brand_name": brandName,
    "description": description,
    "created_at": createdAt,
    "updated_at": updatedAt,
    "model_name": modelName,
    "size_label": sizeLabel,
  };
}

class SafetyValveModel {
  int? id;
  String? modelName;
  String? description;
  String? createdAt;
  String? updatedAt;

  SafetyValveModel({this.id, this.modelName, this.description, this.createdAt, this.updatedAt});

  factory SafetyValveModel.fromJson(Map<String, dynamic> json) {
    return SafetyValveModel(
      id: json['id'],
      modelName: json['model_name'],
      description: json['description'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() => {
    "id": id,
    "model_name": modelName,
    "description": description,
    "created_at": createdAt,
    "updated_at": updatedAt,
  };
}

class SafetyValveSize {
  int? id;
  String? sizeLabel;
  String? description;
  String? createdAt;
  String? updatedAt;

  SafetyValveSize({this.id, this.sizeLabel, this.description, this.createdAt, this.updatedAt});

  factory SafetyValveSize.fromJson(Map<String, dynamic> json) {
    return SafetyValveSize(
      id: json['id'],
      sizeLabel: json['size_label'],
      description: json['description'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() => {
    "id": id,
    "size_label": sizeLabel,
    "description": description,
    "created_at": createdAt,
    "updated_at": updatedAt,
  };
}




