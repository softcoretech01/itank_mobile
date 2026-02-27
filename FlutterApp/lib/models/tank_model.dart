class TankModel {
  bool? success;
  String? message;
  Data? data;

  TankModel({this.success, this.message, this.data});

  TankModel copyWith({
    bool? success,
    String? message,
    Data? data,
  }) =>
      TankModel(
        success: success ?? this.success,
        message: message ?? this.message,
        data: data ?? this.data,
      );

  // -------------------- FROM JSON --------------------
  factory TankModel.fromJson(Map<String, dynamic> json) => TankModel(
    success: json["success"],
    message: json["message"],
    data: json["data"] != null ? Data.fromJson(json["data"]) : null,
  );

  // -------------------- TO JSON --------------------
  Map<String, dynamic> toJson() => {
    "success": success,
    "message": message,
    "data": data?.toJson(),
  };
}

class Data {
  List<ActiveTank>? activeTanks;

  Data({this.activeTanks});

  Data copyWith({
    List<ActiveTank>? activeTanks,
  }) =>
      Data(
        activeTanks: activeTanks ?? this.activeTanks,
      );

  // -------------------- FROM JSON --------------------
  factory Data.fromJson(Map<String, dynamic> json) => Data(
    activeTanks: json["active_tanks"] == null
        ? []
        : List<ActiveTank>.from(
      json["active_tanks"].map((x) => ActiveTank.fromJson(x)),
    ),
  );

  // -------------------- TO JSON --------------------
  Map<String, dynamic> toJson() => {
    "active_tanks": activeTanks == null
        ? []
        : List<dynamic>.from(activeTanks!.map((x) => x.toJson())),
  };
}

class ActiveTank {
  int? tankId;
  String? tankNumber;

  ActiveTank({this.tankId, this.tankNumber});

  ActiveTank copyWith({
    int? tankId,
    String? tankNumber,
  }) =>
      ActiveTank(
        tankId: tankId ?? this.tankId,
        tankNumber: tankNumber ?? this.tankNumber,
      );

  // -------------------- FROM JSON --------------------
  factory ActiveTank.fromJson(Map<String, dynamic> json) => ActiveTank(
    tankId: json["tank_id"],
    tankNumber: json["tank_number"],
  );

  // -------------------- TO JSON --------------------
  Map<String, dynamic> toJson() => {
    "tank_id": tankId,
    "tank_number": tankNumber,
  };
}
