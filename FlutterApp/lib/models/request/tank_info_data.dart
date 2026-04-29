import 'dart:io';

class TankInfoData {
  final String date;
  final String tankId;
  final String reportNumber;
  final String? tankStatus;
  final String? inspectionType;
  final String lifterWeight;
  final File? lifterPhoto;
  final String? product;
  final String? location;
  final String? safetyValve;
  final int? inspectionId;
  final String? vacuumReading;
  final String? vacuumReadingUom;
  final String? lifterWeightValue;

  TankInfoData({
    required this.date,
    required this.tankId,
    required this.reportNumber,
    this.tankStatus,
    this.inspectionType,
    required this.lifterWeight,
    this.lifterPhoto,
    this.product,
    this.location,
    this.safetyValve,
    this.inspectionId,
    this.vacuumReading,
    this.vacuumReadingUom,
    this.lifterWeightValue,
  });

  Map<String, dynamic> toJson() {
    return {
      "date": date,
      "tank_id": tankId,
      "report_number": reportNumber,
      "tank_status_id": tankStatus,
      "inspection_type_id": inspectionType,
      "lifter_weight": lifterWeight,
      "product_id": product,
      "location_id": location,
      "safety_valve_id": safetyValve,
      "inspection_id": inspectionId,
      "vacuum_reading": vacuumReading,
      "vacuum_reading_uom": vacuumReadingUom,
      "lifter_weight_value": lifterWeightValue,
      // Photos are handled separately (multipart)
    };
  }
}
