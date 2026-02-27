class TankDetailsResponse {
  final bool success;
  final String message;
  final TankData? data;

  TankDetailsResponse({
    required this.success,
    required this.message,
    this.data,
  });

  factory TankDetailsResponse.fromJson(Map<String, dynamic> json) {
    return TankDetailsResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? "",
      data: json['data'] != null ? TankData.fromJson(json['data']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "success": success,
      "message": message,
      "data": data?.toJson(),
    };
  }

  TankDetailsResponse copyWith({
    bool? success,
    String? message,
    TankData? data,
  }) {
    return TankDetailsResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      data: data ?? this.data,
    );
  }
}

class TankData {
  final int? inspectionId;
  final int? tankId;
  final String? tankNumber;

  final String? reportNumber;
  final String? inspectionDate;

  final int? statusId;
  final int? productId;
  final int? inspectionTypeId;
  final int? locationId;

  final String? workingPressure;
  final String? designTemperature;

  final String? frameType;
  final String? cabinetType;
  final String? mfgr;

  final String? ownership;
  final String? piNextInspectionDate;
  final String? notes;
  final String? createdBy;

  final String? lifterWeight;

  // Safety valve fields
  final int? safetyValveBrandId;
  final int? safetyValveModelId;
  final int? safetyValveSizeId;

  // Operator fields
  final int? operatorId;
  final int? empId;

  // New fields for vacuum reading and lifter weight value
  final String? vacuumReading;
  final String? lifterWeightValue;

  TankData({
    this.inspectionId,
    this.tankId,
    this.tankNumber,
    this.reportNumber,
    this.inspectionDate,
    this.statusId,
    this.productId,
    this.inspectionTypeId,
    this.locationId,
    this.workingPressure,
    this.designTemperature,
    this.frameType,
    this.cabinetType,
    this.mfgr,
    this.ownership,
    this.piNextInspectionDate,
    this.notes,
    this.createdBy,
    this.lifterWeight,
    this.safetyValveBrandId,
    this.safetyValveModelId,
    this.safetyValveSizeId,
    this.operatorId,
    this.empId,
    this.vacuumReading,
    this.lifterWeightValue,
  });

  factory TankData.fromJson(Map<String, dynamic> json) {
    return TankData(
      inspectionId: json['inspection_id'],
      tankId: json['tank_id'],
      tankNumber: json['tank_number'],
      reportNumber: json['report_number'],
      inspectionDate: json['inspection_date'],
      statusId: json['status_id'],
      productId: json['product_id'],
      inspectionTypeId: json['inspection_type_id'],
      locationId: json['location_id'],
      workingPressure: json['working_pressure'],
      designTemperature: json['design_temperature'],
      frameType: json['frame_type'],
      cabinetType: json['cabinet_type'],
      mfgr: json['mfgr'],
      ownership: json['ownership'],
      piNextInspectionDate: json['pi_next_inspection_date'],
      notes: json['notes'],
      createdBy: json['created_by'],
      lifterWeight: json['lifter_weight']?.toString(),
      safetyValveBrandId: json['safety_valve_brand_id'],
      safetyValveModelId: json['safety_valve_model_id'],
      safetyValveSizeId: json['safety_valve_size_id'],
      operatorId: json['operator_id'],
      empId: json['emp_id'],
      vacuumReading: json['vacuum_reading']?.toString(),
      lifterWeightValue: json['lifter_weight_value']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "inspection_id": inspectionId,
      "tank_id": tankId,
      "tank_number": tankNumber,
      "report_number": reportNumber,
      "inspection_date": inspectionDate,
      "status_id": statusId,
      "product_id": productId,
      "inspection_type_id": inspectionTypeId,
      "location_id": locationId,
      "working_pressure": workingPressure,
      "design_temperature": designTemperature,
      "frame_type": frameType,
      "cabinet_type": cabinetType,
      "mfgr": mfgr,
      "ownership": ownership,
      "pi_next_inspection_date": piNextInspectionDate,
      "notes": notes,
      "created_by": createdBy,
      "lifter_weight": lifterWeight,
      "safety_valve_brand_id": safetyValveBrandId,
      "safety_valve_model_id": safetyValveModelId,
      "safety_valve_size_id": safetyValveSizeId,
      "operator_id": operatorId,
      "emp_id": empId,
      "vacuum_reading": vacuumReading,
      "lifter_weight_value": lifterWeightValue,
    };
  }

  TankData copyWith({
    int? inspectionId,
    int? tankId,
    String? tankNumber,
    String? reportNumber,
    String? inspectionDate,
    int? statusId,
    int? productId,
    int? inspectionTypeId,
    int? locationId,
    String? workingPressure,
    String? designTemperature,
    String? frameType,
    String? cabinetType,
    String? mfgr,
    String? ownership,
    String? piNextInspectionDate,
    String? notes,
    String? createdBy,
    String? lifterWeight,
    int? safetyValveBrandId,
    int? safetyValveModelId,
    int? safetyValveSizeId,
    int? operatorId,
    int? empId,
    String? vacuumReading,
    String? lifterWeightValue,
  }) {
    return TankData(
      inspectionId: inspectionId ?? this.inspectionId,
      tankId: tankId ?? this.tankId,
      tankNumber: tankNumber ?? this.tankNumber,
      reportNumber: reportNumber ?? this.reportNumber,
      inspectionDate: inspectionDate ?? this.inspectionDate,
      statusId: statusId ?? this.statusId,
      productId: productId ?? this.productId,
      inspectionTypeId: inspectionTypeId ?? this.inspectionTypeId,
      locationId: locationId ?? this.locationId,
      workingPressure: workingPressure ?? this.workingPressure,
      designTemperature: designTemperature ?? this.designTemperature,
      frameType: frameType ?? this.frameType,
      cabinetType: cabinetType ?? this.cabinetType,
      mfgr: mfgr ?? this.mfgr,
      ownership: ownership ?? this.ownership,
      piNextInspectionDate:
      piNextInspectionDate ?? this.piNextInspectionDate,
      notes: notes ?? this.notes,
      createdBy: createdBy ?? this.createdBy,
      lifterWeight: lifterWeight ?? this.lifterWeight,
      safetyValveBrandId: safetyValveBrandId ?? this.safetyValveBrandId,
      safetyValveModelId: safetyValveModelId ?? this.safetyValveModelId,
      safetyValveSizeId: safetyValveSizeId ?? this.safetyValveSizeId,
      operatorId: operatorId ?? this.operatorId,
      empId: empId ?? this.empId,
      vacuumReading: vacuumReading ?? this.vacuumReading,
      lifterWeightValue: lifterWeightValue ?? this.lifterWeightValue,
    );
  }

  static String? toStringValue(dynamic value) {
    if (value == null) return null;

    // If already String
    if (value is String) return value;

    // If number → convert to String
    if (value is num) return value.toString();

    // For other types → force convert using toString()
    return value.toString();
  }

}


