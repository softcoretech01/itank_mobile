class TankInfoResponse {
  final bool? success;
  final String? message;
  final CreatedTankInfoData? data;

  TankInfoResponse({
    this.success,
    this.message,
    this.data,
  });

  // ---------- FROM JSON ----------
  factory TankInfoResponse.fromJson(Map<String, dynamic> json) {
    return TankInfoResponse(
      success: json['success'] as bool?,
      message: json['message'] as String?,
      data: json['data'] != null
          ? CreatedTankInfoData.fromJson(json['data'])
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
  TankInfoResponse copyWith({
    bool? success,
    String? message,
    CreatedTankInfoData? data,
  }) {
    return TankInfoResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      data: data ?? this.data,
    );
  }
}

class CreatedTankInfoData {
  final int? inspectionId;
  final String? inspectionDate;
  final String? createdAt;
  final String? updatedAt;
  final String? reportNumber;
  final int? tankId;
  final String? tankNumber;
  final int? statusId;
  final int? productId;
  final int? inspectionTypeId;
  final int? locationId;
  final String? workingPressure;
  final String? frameType;
  final String? designTemperature;
  final String? cabinetType;
  final String? mfgr;
  final String? safetyValveBrand;
  final String? safetyValveModel;
  final String? safetyValveSize;
  final String? piNextInspectionDate;
  final String? notes;
  final String? lifterWeight;
  final int? operatorId;
  final String? ownership;
  final String? createdBy;
  final String? updatedBy;
  final String? safetyValveBrandId;
  final String? safetyValveModelId;
  final String? safetyValveSizeId;
  final int? empId;

  CreatedTankInfoData({
    this.inspectionId,
    this.inspectionDate,
    this.createdAt,
    this.updatedAt,
    this.reportNumber,
    this.tankId,
    this.tankNumber,
    this.statusId,
    this.productId,
    this.inspectionTypeId,
    this.locationId,
    this.workingPressure,
    this.frameType,
    this.designTemperature,
    this.cabinetType,
    this.mfgr,
    this.safetyValveBrand,
    this.safetyValveModel,
    this.safetyValveSize,
    this.piNextInspectionDate,
    this.notes,
    this.lifterWeight,
    this.operatorId,
    this.ownership,
    this.createdBy,
    this.updatedBy,
    this.safetyValveBrandId,
    this.safetyValveModelId,
    this.safetyValveSizeId,
    this.empId,
  });

  // ---------- FROM JSON ----------
  factory CreatedTankInfoData.fromJson(Map<String, dynamic> json) {
    return CreatedTankInfoData(
      inspectionId: json['inspection_id'],
      inspectionDate: json['inspection_date']?.toString(),
      createdAt: json['created_at']?.toString(),
      updatedAt: json['updated_at']?.toString(),
      reportNumber: json['report_number']?.toString(),
      tankId: json['tank_id'],
      tankNumber: json['tank_number']?.toString(),
      statusId: json['status_id'],
      productId: json['product_id'],
      inspectionTypeId: json['inspection_type_id'],
      locationId: json['location_id'],
      workingPressure: json['working_pressure'],

      // 🔥 FIXED — convert everything to string safely
      frameType: json['frame_type']?.toString(),
      designTemperature: json['design_temperature']?.toString(),
      cabinetType: json['cabinet_type']?.toString(),
      mfgr: json['mfgr']?.toString(),
      safetyValveBrand: json['safety_valve_brand']?.toString(),
      safetyValveModel: json['safety_valve_model']?.toString(),
      safetyValveSize: json['safety_valve_size']?.toString(),

      piNextInspectionDate: json['next_inspection_date']?.toString(),
      notes: json['notes']?.toString(),
      lifterWeight: json['lifter_weight']?.toString(),

      operatorId: json['operator_id'],
      ownership: json['ownership']?.toString(),
      createdBy: json['created_by']?.toString(),
      updatedBy: json['updated_by']?.toString(),

      safetyValveBrandId: json['safety_valve_brand_id']?.toString(),
      safetyValveModelId: json['safety_valve_model_id']?.toString(),
      safetyValveSizeId: json['safety_valve_size_id']?.toString(),
      empId: json['emp_id'],
    );
  }

  // ---------- TO JSON ----------
  Map<String, dynamic> toJson() {
    return {
      'inspection_id': inspectionId,
      'inspection_date': inspectionDate,
      'created_at': createdAt,
      'updated_at': updatedAt,
      'report_number': reportNumber,
      'tank_id': tankId,
      'tank_number': tankNumber,
      'status_id': statusId,
      'product_id': productId,
      'inspection_type_id': inspectionTypeId,
      'location_id': locationId,
      'working_pressure': workingPressure,
      'frame_type': frameType,
      'design_temperature': designTemperature,
      'cabinet_type': cabinetType,
      'mfgr': mfgr,
      'safety_valve_brand': safetyValveBrand,
      'safety_valve_model': safetyValveModel,
      'safety_valve_size': safetyValveSize,
      'pi_next_inspection_date': piNextInspectionDate,
      'notes': notes,
      'lifter_weight': lifterWeight,
      'operator_id': operatorId,
      'ownership': ownership,
      'created_by': createdBy,
      'updated_by': updatedBy,
      'safety_valve_brand_id': safetyValveBrandId,
      'safety_valve_model_id': safetyValveModelId,
      'safety_valve_size_id': safetyValveSizeId,
      'emp_id': empId,
    };
  }

  // ---------- COPYWITH ----------
  CreatedTankInfoData copyWith({
    int? inspectionId,
    String? inspectionDate,
    String? createdAt,
    String? updatedAt,
    String? reportNumber,
    int? tankId,
    String? tankNumber,
    int? statusId,
    int? productId,
    int? inspectionTypeId,
    int? locationId,
    String? workingPressure,
    String? frameType,
    String? designTemperature,
    String? cabinetType,
    String? mfgr,
    String? safetyValveBrand,
    String? safetyValveModel,
    String? safetyValveSize,
    String? piNextInspectionDate,
    String? notes,
    String? lifterWeight,
    int? operatorId,
    String? ownership,
    String? createdBy,
    String? updatedBy,
    String? safetyValveBrandId,
    String? safetyValveModelId,
    String? safetyValveSizeId,
    int? empId,
  }) {
    return CreatedTankInfoData(
      inspectionId: inspectionId ?? this.inspectionId,
      inspectionDate: inspectionDate ?? this.inspectionDate,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      reportNumber: reportNumber ?? this.reportNumber,
      tankId: tankId ?? this.tankId,
      tankNumber: tankNumber ?? this.tankNumber,
      statusId: statusId ?? this.statusId,
      productId: productId ?? this.productId,
      inspectionTypeId: inspectionTypeId ?? this.inspectionTypeId,
      locationId: locationId ?? this.locationId,
      workingPressure: workingPressure ?? this.workingPressure,
      frameType: frameType ?? this.frameType,
      designTemperature: designTemperature ?? this.designTemperature,
      cabinetType: cabinetType ?? this.cabinetType,
      mfgr: mfgr ?? this.mfgr,
      safetyValveBrand: safetyValveBrand ?? this.safetyValveBrand,
      safetyValveModel: safetyValveModel ?? this.safetyValveModel,
      safetyValveSize: safetyValveSize ?? this.safetyValveSize,
      piNextInspectionDate:
      piNextInspectionDate ?? this.piNextInspectionDate,
      notes: notes ?? this.notes,
      lifterWeight: lifterWeight ?? this.lifterWeight,
      operatorId: operatorId ?? this.operatorId,
      ownership: ownership ?? this.ownership,
      createdBy: createdBy ?? this.createdBy,
      updatedBy: updatedBy ?? this.updatedBy,
      safetyValveBrandId:
      safetyValveBrandId ?? this.safetyValveBrandId,
      safetyValveModelId:
      safetyValveModelId ?? this.safetyValveModelId,
      safetyValveSizeId:
      safetyValveSizeId ?? this.safetyValveSizeId,
      empId: empId ?? this.empId,
    );
  }
}
