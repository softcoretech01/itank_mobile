class ChecklistSection {
  String sn;
  String title;
  List<ChecklistItem> items;

  ChecklistSection({required this.sn, required this.title, required this.items});

  factory ChecklistSection.fromJson(Map<String, dynamic> json) {
    return ChecklistSection(
      sn: json["sn"],
      title: json["title"],
      items: (json["items"] as List)
          .map((x) => ChecklistItem.fromJson(x))
          .toList(),
    );
  }
}

class ChecklistItem {
  String sn;
  String title;

  ChecklistItem({required this.sn, required this.title});

  factory ChecklistItem.fromJson(Map<String, dynamic> json) {
    return ChecklistItem(
      sn: json["sn"],
      title: json["title"],
    );
  }
}
