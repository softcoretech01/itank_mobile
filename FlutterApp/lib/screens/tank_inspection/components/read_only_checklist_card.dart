import 'package:flutter/material.dart';

import '../../../models/request/check_list_request.dart';


class ReadOnlyChecklistCard extends StatefulWidget {
  final String title;
  final bool isChecked;
  final String status; // ok / faulty / na
  final List<Section> items;

  const ReadOnlyChecklistCard({
    super.key,
    required this.title,
    required this.isChecked,
    required this.status,
    required this.items,
  });

  @override
  State<ReadOnlyChecklistCard> createState() => _ReadOnlyChecklistCardState();
}

class _ReadOnlyChecklistCardState extends State<ReadOnlyChecklistCard> {
  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // ------------------ TITLE + CHECKBOX ------------------
            Row(
              children: [
                Text(
                  widget.title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Checkbox(
                  value: widget.isChecked,
                  onChanged: null, // read-only
                ),
              ],
            ),

            const SizedBox(height: 12),

            // ------------------ SUB ITEMS ------------------
            ...widget.items.map((item) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "1  ${item.title}",
                      style: const TextStyle(fontSize: 15),
                    ),

                    if (item.comments != null && item.comments!.isNotEmpty)
                      Container(
                        width: double.infinity,
                        margin: const EdgeInsets.only(top: 6),
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          "Note: ${item.comments}",
                          style: const TextStyle(color: Colors.black87),
                        ),
                      )
                  ],
                ),
              );
            }),

            const Divider(height: 24),

            // ------------------ LEGEND STATUS ------------------
            const Text(
              "Legend for Status:",
              style: TextStyle(fontWeight: FontWeight.bold),
            ),

            Row(
              children: [
                radioReadOnly("✓ OK", widget.status == "ok"),
                radioReadOnly("X Faulty", widget.status == "faulty"),
                radioReadOnly("NA", widget.status == "na"),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget radioReadOnly(String label, bool selected) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Radio(
          value: true,
          groupValue: selected,
          onChanged: null, // disabled
        ),
        Text(label),
        const SizedBox(width: 12),
      ],
    );
  }
}

