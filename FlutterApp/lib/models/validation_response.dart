class ValidationResponse {
  final bool? success;
  final String? message;
  final ValidationData? data;

  ValidationResponse({
    this.success,
    this.message,
    this.data,
  });

  ValidationResponse copyWith({
    bool? success,
    String? message,
    ValidationData? data,
  }) {
    return ValidationResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      data: data ?? this.data,
    );
  }

  factory ValidationResponse.fromJson(Map<String, dynamic> json) {
    return ValidationResponse(
      success: json['success'],
      message: json['message'],
      data: json['data'] != null
          ? ValidationData.fromJson(json['data'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "success": success,
      "message": message,
      "data": data?.toJson(),
    };
  }
}

class ValidationData {
  final int? inspectionId;
  final ValidationIssues? issues;

  ValidationData({
    this.inspectionId,
    this.issues,
  });

  ValidationData copyWith({
    int? inspectionId,
    ValidationIssues? issues,
  }) {
    return ValidationData(
      inspectionId: inspectionId ?? this.inspectionId,
      issues: issues ?? this.issues,
    );
  }

  factory ValidationData.fromJson(Map<String, dynamic> json) {
    return ValidationData(
      inspectionId: json['inspection_id'],

      issues: json['issues'] != null
          ? ValidationIssues.fromJson(json['issues'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "inspection_id": inspectionId,
      "issues": issues?.toJson(),
    };
  }
}

class ValidationIssues {
  final List<InspectionIssue>? inspection;
  final List<dynamic>? checklist;
  final List<TodoListIssue>? toDoList;
  final List<ImageIssue>? images;

  ValidationIssues({
    this.inspection,
    this.checklist,
    this.toDoList,
    this.images,
  });

  ValidationIssues copyWith({
    List<InspectionIssue>? inspection,
    List<dynamic>? checklist,
    List<TodoListIssue>? toDoList,
    List<ImageIssue>? images,
  }) {
    return ValidationIssues(
      inspection: inspection ?? this.inspection,
      checklist: checklist ?? this.checklist,
      toDoList: toDoList ?? this.toDoList,
      images: images ?? this.images,
    );
  }

  factory ValidationIssues.fromJson(Map<String, dynamic> json) {
    return ValidationIssues(
      inspection: json['inspection'] != null
          ? List<InspectionIssue>.from(
          json['inspection'].map((x) => InspectionIssue.fromJson(x)))
          : [],
      checklist: json['checklist'] ?? [],
      toDoList: json['to_do_list'] != null
          ? List<TodoListIssue>.from(
          json['to_do_list'].map((x) => TodoListIssue.fromJson(x)))
          : [],
      images: json['images'] != null
          ? List<ImageIssue>.from(
          json['images'].map((x) => ImageIssue.fromJson(x)))
          : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "inspection":
      inspection?.map((x) => x.toJson()).toList() ?? [],
      "checklist": checklist,
      "to_do_list":
      toDoList?.map((x) => x.toJson()).toList() ?? [],
      "images": images?.map((x) => x.toJson()).toList() ?? [],
    };
  }
}

class InspectionIssue {
  final String? field;
  final String? reason;

  InspectionIssue({this.field, this.reason});

  InspectionIssue copyWith({
    String? field,
    String? reason,
  }) {
    return InspectionIssue(
      field: field ?? this.field,
      reason: reason ?? this.reason,
    );
  }

  factory InspectionIssue.fromJson(Map<String, dynamic> json) {
    return InspectionIssue(
      field: json['field'],
      reason: json['reason'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "field": field,
      "reason": reason,
    };
  }
}

class TodoListIssue {
  final String? reason;
  final List<FlaggedJob>? flaggedJobs;

  TodoListIssue({
    this.reason,
    this.flaggedJobs,
  });

  TodoListIssue copyWith({
    String? reason,
    List<FlaggedJob>? flaggedJobs,
  }) {
    return TodoListIssue(
      reason: reason ?? this.reason,
      flaggedJobs: flaggedJobs ?? this.flaggedJobs,
    );
  }

  factory TodoListIssue.fromJson(Map<String, dynamic> json) {
    return TodoListIssue(
      reason: json['reason'],
      flaggedJobs: json['flagged_jobs'] != null
          ? List<FlaggedJob>.from(
          json['flagged_jobs'].map((x) => FlaggedJob.fromJson(x)))
          : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "reason": reason,
      "flagged_jobs":
      flaggedJobs?.map((x) => x.toJson()).toList() ?? [],
    };
  }
}

class FlaggedJob {
  final String? jobId;
  final String? jobName;
  final int? statusId;

  FlaggedJob({
    this.jobId,
    this.jobName,
    this.statusId,
  });

  FlaggedJob copyWith({
    String? jobId,
    String? jobName,
    int? statusId,
  }) {
    return FlaggedJob(
      jobId: jobId ?? this.jobId,
      jobName: jobName ?? this.jobName,
      statusId: statusId ?? this.statusId,
    );
  }

  factory FlaggedJob.fromJson(Map<String, dynamic> json) {
    return FlaggedJob(
      jobId: json['job_id'],
      jobName: json['job_name'],
      statusId: json['status_id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "job_id": jobId,
      "job_name": jobName,
      "status_id": statusId,
    };
  }
}

class ImageIssue {
  final String? reason;
  final List<MissingImage>? missing;

  ImageIssue({
    this.reason,
    this.missing,
  });

  ImageIssue copyWith({
    String? reason,
    List<MissingImage>? missing,
  }) {
    return ImageIssue(
      reason: reason ?? this.reason,
      missing: missing ?? this.missing,
    );
  }

  factory ImageIssue.fromJson(Map<String, dynamic> json) {
    return ImageIssue(
      reason: json['reason'],
      missing: json['missing'] != null
          ? List<MissingImage>.from(
          json['missing'].map((x) => MissingImage.fromJson(x)))
          : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "reason": reason,
      "missing": missing?.map((x) => x.toJson()).toList() ?? [],
    };
  }
}

class MissingImage {
  final int? imageTypeId;
  final String? imageType;
  final String? reason;
  final int? index;

  MissingImage({
    this.imageTypeId,
    this.imageType,
    this.reason,
    this.index,
  });

  MissingImage copyWith({
    int? imageTypeId,
    String? imageType,
    String? reason,
    int? index,
  }) {
    return MissingImage(
      imageTypeId: imageTypeId ?? this.imageTypeId,
      imageType: imageType ?? this.imageType,
      reason: reason ?? this.reason,
      index: index ?? this.index,
    );
  }

  factory MissingImage.fromJson(Map<String, dynamic> json) {
    return MissingImage(
      imageTypeId: json['image_type_id'],
      imageType: json['image_type'],
      reason: json['reason'],
      index: json['index'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "image_type_id": imageTypeId,
      "image_type": imageType,
      "reason": reason,
      "index": index,
    };
  }
}
