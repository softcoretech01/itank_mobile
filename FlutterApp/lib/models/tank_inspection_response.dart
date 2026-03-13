import 'dart:convert';

TankInspectionResponse tankInspectionResponseFromJson(String str) =>
    TankInspectionResponse.fromJson(json.decode(str));

String tankInspectionResponseToJson(TankInspectionResponse data) =>
    json.encode(data.toJson());

class TankInspectionResponse {
  final bool success;
  final String message;
  final InspectionData? data;

  TankInspectionResponse({
    required this.success,
    required this.message,
    required this.data,
  });

  factory TankInspectionResponse.fromJson(Map<String, dynamic> json) =>
      TankInspectionResponse(
        success: json["success"] ?? false,
        message: json["message"]?.toString() ?? "",
        data: InspectionData?.fromJson(json["data"] ?? {}),
      );

  Map<String, dynamic> toJson() => {
    "success": success,
    "message": message,
    "data": data?.toJson(),
  };
}

class InspectionData {
  final Inspection inspection;
  final List<InspectionImage> images;
  final List<InspectionChecklist> inspectionChecklist;

  InspectionData({
    required this.inspection,
    required this.images,
    required this.inspectionChecklist,
  });

  factory InspectionData.fromJson(Map<String, dynamic> json) =>
      InspectionData(
        inspection: Inspection.fromJson(json["inspection"] ?? {}),
        images: List<InspectionImage>.from(
            (json["images"] ?? []).map((x) => InspectionImage.fromJson(x))),
        inspectionChecklist: List<InspectionChecklist>.from(
            (json["inspection_checklist"] ?? [])
                .map((x) => InspectionChecklist.fromJson(x))),
      );

  Map<String, dynamic> toJson() => {
    "inspection": inspection.toJson(),
    "images": images.map((x) => x.toJson()).toList(),
    "inspection_checklist":
    inspectionChecklist.map((x) => x.toJson()).toList(),
  };
}

class Inspection {
  final int inspectionId;
  final String inspectionDate;
  final String reportNumber;

  final int tankId;
  final String tankNumber;

  final String statusId;
  final String productId;
  final String inspectionTypeId;
  final String locationId;

  final String workingPressure;
  final String? designTemperature;
  final String frameType;
  final String? cabinetType;
  final String? mfgr;

  final int? safetyValveBrandId;
  final int? safetyValveModelId;
  final int? safetyValveSizeId;

  final String? piNextInspectionDate;
  final String ownership;
  final String? notes;

  final String? lifterWeight;
  final String? lifterWeightThumbnail;

  final int? empId;
  final int? operatorId;

  final String createdBy;
  final String updatedBy;

  final String? vacuumReading;
  final String? lifterWeightValue;

  // Additional display fields
  final String status;
  final String location;
  final String inspectionType;
  final String? safetyValveBrand;
  final String product;

  Inspection({
    required this.inspectionId,
    required this.inspectionDate,
    required this.reportNumber,
    required this.tankId,
    required this.tankNumber,
    required this.statusId,
    required this.productId,
    required this.inspectionTypeId,
    required this.locationId,
    required this.workingPressure,
    required this.designTemperature,
    required this.frameType,
    required this.cabinetType,
    required this.mfgr,
    required this.safetyValveBrandId,
    required this.safetyValveModelId,
    required this.safetyValveSizeId,
    required this.piNextInspectionDate,
    required this.ownership,
    required this.notes,
    required this.lifterWeight,
    required this.lifterWeightThumbnail,
    required this.empId,
    required this.operatorId,
    required this.createdBy,
    required this.updatedBy,
    required this.status,
    required this.location,
    required this.inspectionType,
    required this.safetyValveBrand,
    required this.product,
    required this.vacuumReading,
    required this.lifterWeightValue,
  });

  factory Inspection.fromJson(Map<String, dynamic> json) => Inspection(
    inspectionId: json["inspection_id"] ?? 0,
    inspectionDate: json["inspection_date"]?.toString() ?? "",
    reportNumber: json["report_number"]?.toString() ?? "",

    tankId: json["tank_id"] ?? 0,
    tankNumber: json["tank_number"]?.toString() ?? "",

    statusId: json["status_id"]?.toString() ?? "",
    productId: json["product_id"]?.toString() ?? "",
    inspectionTypeId: json["inspection_type_id"]?.toString() ?? "",
    locationId: json["location_id"]?.toString() ?? "",

    workingPressure: json["working_pressure"]?.toString() ?? "",
    designTemperature: json["design_temperature"]?.toString(),
    frameType: json["frame_type"]?.toString() ?? "",
    cabinetType: json["cabinet_type"]?.toString(),
    mfgr: json["mfgr"]?.toString(),

    safetyValveBrandId: json["safety_valve_brand_id"],
    safetyValveModelId: json["safety_valve_model_id"],
    safetyValveSizeId: json["safety_valve_size_id"],

    piNextInspectionDate: json["next_inspection_date"]?.toString(),
    ownership: json["ownership"]?.toString() ?? "",
    notes: json["notes"]?.toString(),

    lifterWeight: json["lifter_weight"]?.toString(),
    lifterWeightThumbnail: json["lifter_weight_thumbnail"]?.toString(),

    empId: json["emp_id"],
    operatorId: json["operator_id"],

    createdBy: json["created_by"]?.toString() ?? "",
    updatedBy: json["updated_by"]?.toString() ?? "",

    status: json["status_name"]?.toString() ?? "",
    location: json["location_name"]?.toString() ?? "",
    inspectionType: json["inspection_type_name"]?.toString() ?? "",
    safetyValveBrand: json["safety_valve_brand"]?.toString(),
    product: json["product_name"]?.toString() ?? "",
    vacuumReading: json["vacuum_reading"]?.toString(),
    lifterWeightValue: json["lifter_weight_value"]?.toString(),
  );

  Map<String, dynamic> toJson() => {
    "inspection_id": inspectionId,
    "inspection_date": inspectionDate,
    "report_number": reportNumber,
    "tank_id": tankId,
    "tank_number": tankNumber,
    "status_id": statusId,
    "product_id": productId,
    "inspection_type_id": inspectionTypeId,
    "location_id": locationId,
    "working_pressure": workingPressure,
    "design_temperature": designTemperature,
    "frame_type": frameType,
    "cabinet_type": cabinetType,
    "mfgr": mfgr,
    "safety_valve_brand_id": safetyValveBrandId,
    "safety_valve_model_id": safetyValveModelId,
    "safety_valve_size_id": safetyValveSizeId,
    "pi_next_inspection_date": piNextInspectionDate,
    "ownership": ownership,
    "notes": notes,
    "lifter_weight": lifterWeight,
    "lifter_weight_thumbnail": lifterWeightThumbnail,
    "emp_id": empId,
    "operator_id": operatorId,
    "created_by": createdBy,
    "updated_by": updatedBy,
    "status": status,
    "location": location,
    "inspection_type": inspectionType,
    "safety_valve_brand": safetyValveBrand,
    "product": product,
    "vacuum_reading": vacuumReading,
    "lifter_weight_value": lifterWeightValue,
  };
}


class InspectionImage {
  final int id;
  final int inspectionId;
  final String imagePath;

  InspectionImage({
    required this.id,
    required this.inspectionId,
    required this.imagePath,
  });

  factory InspectionImage.fromJson(Map<String, dynamic> json) =>
      InspectionImage(
        id: json["id"] ?? 0,
        inspectionId: json["inspection_id"] ?? 0,
        imagePath: json["image_path"]?.toString() ?? "",
      );

  Map<String, dynamic> toJson() => {
    "id": id,
    "inspection_id": inspectionId,
    "image_path": imagePath,
  };
}

class InspectionChecklist {
  final String sn;
  final String jobId;
  final String title;
  final String status;
  final String statusName;
  final List<InspectionItem> items;

  InspectionChecklist({
    required this.sn,
    required this.jobId,
    required this.title,
    required this.status,
    required this.statusName,
    required this.items,
  });

  factory InspectionChecklist.fromJson(Map<String, dynamic> json) =>
      InspectionChecklist(
        sn: json["sn"]?.toString() ?? "",
        jobId: json["job_id"]?.toString() ?? "",
        title: json["title"]?.toString() ?? "",
        status: json["status"]?.toString() ?? "",
        statusName: json["status_name"]?.toString() ?? "",
        items: List<InspectionItem>.from(
            (json["items"] ?? []).map((x) => InspectionItem.fromJson(x))),
      );

  Map<String, dynamic> toJson() => {
    "sn": sn,
    "job_id": jobId,
    "title": title,
    "status": status,
    "status_name": statusName,
    "items": items.map((x) => x.toJson()).toList(),
  };
}

class InspectionItem {
  final String sn;
  final String title;
  final String comment;
  final String statusName;

  InspectionItem({
    required this.sn,
    required this.title,
    required this.comment,
    required this.statusName,
  });

  factory InspectionItem.fromJson(Map<String, dynamic> json) =>
      InspectionItem(
        sn: json["sn"]?.toString() ?? "",
        title: json["title"]?.toString() ?? "",
        comment: (json["comment"] ?? json["comments"])?.toString() ?? "",
        statusName: json["status_name"]?.toString() ?? "",
      );

  Map<String, dynamic> toJson() => {
    "sn": sn,
    "title": title,
    "comment": comment,
    "status_name": statusName,
  };
}
