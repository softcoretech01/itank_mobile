class CheckListRequest {
  final String inspectionId;
  final String tankId;
  final List<Section> sections;

  CheckListRequest({
    required this.inspectionId,
    required this.tankId,
    required this.sections,
  });

  factory CheckListRequest.fromJson(Map<String, dynamic> json) {
    return CheckListRequest(
      inspectionId: json['inspection_id'] ?? '',
      tankId: json['tank_id']?.toString() ?? '', // Ensure it's a string
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

  CheckListRequest copyWith({
    String? inspectionId,
    String? tankId,
    List<Section>? sections,
  }) {
    return CheckListRequest(
      inspectionId: inspectionId ?? this.inspectionId,
      tankId: tankId ?? this.tankId,
      sections: sections ?? this.sections,
    );
  }
}

class Section {
  final int? jobId;
  final String title;
  final int statusId;
  final String? comments;
  final List<Item> items;

  Section({
    this.jobId,
    required this.title,
    required this.statusId,
    this.comments,
    required this.items,
  });

  factory Section.fromJson(Map<String, dynamic> json) {
    return Section(
      jobId: json['job_id'] ?? 0,
      title: json['title'] ?? '',
      statusId: json['status_id'] ?? 0,
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
    int? jobId,
    String? title,
    int? statusId,
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
  final String comments;
  final int subJobId;
  final int statusId;

  Item({
    required this.title,
    required this.comments,
    required this.subJobId,
    required this.statusId,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    return Item(
       title: json['title'] ?? '',
      comments: json['comments'] ?? '',
      subJobId: json['sub_job_id'] ?? 0,
      statusId: json['status_id'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'comments': comments,
      'sub_job_id': subJobId,
      'status_id': statusId,
    };
  }

  Item copyWith({
    String? title,
    String? comments,
    int? subJobId,
    int? statusId,
  }) {
    return Item(
      title: title ?? this.title,
      comments: comments ?? this.comments,
      subJobId: subJobId ?? this.subJobId,
      statusId: statusId ?? this.statusId,
    );
  }
}
