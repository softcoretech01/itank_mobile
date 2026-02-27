class CheckListResponse {
  final bool success;
  final String message;
  final InspectionData? data;

  CheckListResponse({
    required this.success,
    required this.message,
    this.data,
  });

  factory CheckListResponse.fromJson(Map<String, dynamic> json) {
    return CheckListResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      data: json['data'] != null ? InspectionData.fromJson(json['data']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'message': message,
      'data': data?.toJson(),
    };
  }

  CheckListResponse copyWith({
    bool? success,
    String? message,
    InspectionData? data,
  }) {
    return CheckListResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      data: data ?? this.data,
    );
  }
}

class InspectionData {
  final String inspectionId;
  final String tankId;
  final List<Section> sections;

  InspectionData({
    required this.inspectionId,
    required this.tankId,
    required this.sections,
  });

  factory InspectionData.fromJson(Map<String, dynamic> json) {
    return InspectionData(
      inspectionId: (json['inspection_id'] ?? '').toString(),
      tankId: (json['tank_id'] ?? '').toString(),
      sections: (json['sections'] as List<dynamic>?)
          ?.map((e) => Section.fromJson(e))
          .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'inspection_id': inspectionId,
      'tank_id': tankId,
      'sections': sections.map((e) => e.toJson()).toList(),
    };
  }

  InspectionData copyWith({
    String? inspectionId,
    String? tankId,
    List<Section>? sections,
  }) {
    return InspectionData(
      inspectionId: inspectionId ?? this.inspectionId,
      tankId: tankId ?? this.tankId,
      sections: sections ?? this.sections,
    );
  }
}

class Section {
  final String jobId;
  final String title;
  final String statusId;
  final String? comments;
  final List<Item> items;

  Section({
    required this.jobId,
    required this.title,
    required this.statusId,
    this.comments,
    required this.items,
  });

  factory Section.fromJson(Map<String, dynamic> json) {
    return Section(
      jobId: (json['job_id'] ?? '').toString(),
      title: json['title'] ?? '',
      statusId: (json['status_id'] ?? '').toString(),
      comments: json['comments'],
      items: (json['items'] as List<dynamic>?)
          ?.map((e) => Item.fromJson(e))
          .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'job_id': jobId,
      'title': title,
      'status_id': statusId,
      if (comments != null) 'comments': comments,
      'items': items.map((e) => e.toJson()).toList(),
    };
  }

  Section copyWith({
    String? jobId,
    String? title,
    String? statusId,
    String? comments,
    List<Item>? items,
  }) {
    return Section(
      jobId: jobId ?? this.jobId,
      title: title ?? this.title,
      statusId: statusId ?? this.statusId,
      comments: comments ?? this.comments,
      items: items ?? this.items,
    );
  }
}

class Item {
  final String title;
  final String comment;
  final String subJobId;
  final String statusId;

  Item({
    required this.title,
    required this.comment,
    required this.subJobId,
    required this.statusId,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    return Item(
      title: json['title'] ?? '',
      comment: json['comments'] ?? json['comment'] ?? '',
      subJobId: (json['sub_job_id'] ?? '').toString(),
      statusId: (json['status_id'] ?? '').toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'comment': comment,
      'sub_job_id': subJobId,
      'status_id': statusId,
    };
  }

  Item copyWith({
    String? title,
    String? comment,
    String? subJobId,
    String? statusId,
  }) {
    return Item(
      title: title ?? this.title,
      comment: comment ?? this.comment,
      subJobId: subJobId ?? this.subJobId,
      statusId: statusId ?? this.statusId,
    );
  }
}
