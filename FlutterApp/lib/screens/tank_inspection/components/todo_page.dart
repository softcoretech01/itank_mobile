
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shimmer/shimmer.dart';

import '../../../bloc/tank_inspection/tank_inspection_bloc.dart';
import '../../../models/check_list_response.dart';
import '../../../models/request/check_list_request.dart' as clr;
import '../../../models/status_master_response.dart';
import '../../../repository/master_data.dart';

class TodoPage extends StatefulWidget {

  const TodoPage({super.key});

  @override
  State<TodoPage> createState() => TodoPageState();
}

class TodoPageState extends State<TodoPage> {
  /// SECTION STATUS -> stores the selected status_id as String
  Map<String, String?> status = {};

  /// COMMENT VISIBILITY + TEXT FOR EACH ITEM
  Map<String, bool> showCommentBox = {};
  final Map<String, TextEditingController> comments = {};

  /// ITEM STATUSES
  Map<String, String> itemStatuses = {};

  List<Section> sections = [];

  MasterData? repo;
  List<StatusData> statusOptions = [];

  bool isLoading = true;
  bool loaded = false;

  List<Section> todoSections = [];

  String? faultyId;

  // HELPER METHODS
  // -----------------------------------------------------------

  String? _findStatusIdByKeywords(List<String> kws) {
    for (var s in statusOptions) {
      final name = s.statusName.toLowerCase();
      for (var k in kws) {
        if (name.contains(k)) return s.statusId.toString();
      }
    }
    return null;
  }

  // -----------------------------------------------------------
  @override
  void initState() {
    super.initState();
    context.read<TankInspectionBloc>().add(LoadChecklistMasterEvent());
  }

  @override
  void dispose() {
    comments.forEach((_, c) => c.dispose());
    super.dispose();
  }

  // -----------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    return BlocConsumer<TankInspectionBloc, TankInspectionState>(
        listener: (context, state) {

          // -------------------------------------------------
          // 1. MASTER DATA LOADED
          // -------------------------------------------------
          if (state.checklist.flowStatus == FlowStatus.ready &&
              state.checklist.statusMasterResponse != null &&
              statusOptions.isEmpty) {

            statusOptions = state.checklist.statusMasterResponse?.data ?? [];
            faultyId = _findStatusIdByKeywords(['fault', 'faulty', 'red']) ?? '2';
          }

          // -------------------------------------------------
          // 2. TODO DATA LOADED
          // -------------------------------------------------
          if (state.todoState.checkListResponse?.data != null && !loaded) {

            loaded = true;

            final uploadedSections = state.todoState.checkListResponse!.data!.sections;

            todoSections = uploadedSections;

            for (var section in todoSections) {
              status[section.jobId] = section.statusId;
              for (var item in section.items) {
                comments[item.subJobId] = TextEditingController(text: item.comment);
                showCommentBox[item.subJobId] = true; // Always show comment box in todo
                itemStatuses[item.subJobId] = item.statusId;
              }
            }

            setState(() {});
          }
        },
        builder: (context, state) {
          if (state.status == FlowStatus.loading) {
            return Scaffold(
              body: Center(
                child: Shimmer.fromColors(
                  baseColor: Colors.grey[300]!,
                  highlightColor: Colors.grey[100]!,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    mainAxisSize: MainAxisSize.max,
                    children: List.generate(18, (index) =>
                        Container(
                          width: 280,
                          margin: const EdgeInsets.symmetric(vertical: 8),
                          color: Colors.white,
                        )),
                  ),
                ),
              ),
            );
          }


          return Scaffold(
            body: SingleChildScrollView(
              padding: const EdgeInsets.only(
                  left: 16, right: 16, top: 16, bottom: 200),
              child: Column(
                children: todoSections.asMap().entries.map((entry) {
                  final index = entry.key;
                  final section = entry.value;

                  return checklistCard(
                    title: "${index+1}. ${section.title}",

                    /// STORE AND READ USING section.sn
                    statusValue: status[section.jobId],
                    // section.job_id is string => use section.jobId
                    onStatusChanged: (v) {
                      setState(() => status[section.jobId] = v); // Correct key
                    },

                    items: section.items
                        .map((i) => [i.subJobId, i.title])
                        .toList(),
                  );
                }).toList(),
              ),
            ),
          );
        });
  }

  // -----------------------------------------------------------
  // CHECKLIST CARD (Checkbox removed)
  // -----------------------------------------------------------

  Widget checklistCard({
    required String title,
    required List<List<String>> items,
    required String? statusValue,
    required Function(String?) onStatusChanged,
  }) {

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),

            const SizedBox(height: 8),

            ...items.map((item) {
              String sn = item[0];
              String text = item[1];

              return Padding(
                padding: const EdgeInsets.only(bottom: 18),
                child:Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            "$sn  $text",
                            style: const TextStyle(fontSize: 15),
                          ),
                        ),

                        // STATUS BUTTON
                        _statusButton(sn),
                      ],
                    ),

                    const SizedBox(height: 8),

                    AnimatedCrossFade(
                      duration: const Duration(milliseconds: 250),
                      crossFadeState: showCommentBox[sn] == true
                          ? CrossFadeState.showSecond
                          : CrossFadeState.showFirst,

                      firstChild: Container(),

                      secondChild: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [

                          const SizedBox(height: 2),

                          TextField(
                            controller: comments[sn],
                            maxLines: 1,
                            onChanged: (value) {
                              // Removed empty-check that hides the box. 
                              // We want it to stay visible for faulty items.
                            },
                            decoration: InputDecoration(
                              hintText: "Enter comment...",
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _statusButton(String sn) {
    String currentStatus = itemStatuses[sn] ?? '2'; // default to faulty
    Color color;
    String text;
    IconData icon;

    switch (currentStatus) {
      case '1':
        color = Colors.green;
        text = 'OK';
        icon = Icons.check_circle;
        break;
      case '3':
        color = Colors.white;
        text = 'NA';
        icon = Icons.check_circle_outline;
        break;
      default:
        color = Colors.red;
        text = 'Faulty';
        icon = Icons.error;
        break;
    }

    return ElevatedButton(
      onPressed: () {
        setState(() {
          // Cycle: 2 (faulty) -> 3 (NA) -> 1 (OK) -> 2
          if (currentStatus == '2') {
            itemStatuses[sn] = '3';
          } else if (currentStatus == '3') {
            itemStatuses[sn] = '1';
          } else {
            itemStatuses[sn] = '2';
          }
        });
      },
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: color == Colors.white ? Colors.black : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16),
          const SizedBox(width: 4),
          Text(text),
        ],
      ),
    );
  }



  // -----------------------------------------------------------
  // COLLECT DATA FOR API
  // -----------------------------------------------------------

  List<clr.Section> collectSectionsForRequest() {
    List<clr.Section> result = [];

    for (var section in todoSections) {
      // Calculate section status based on items
      int sectionStatus = 1; // OK
      bool hasNA = false;
      bool hasFaulty = false;

      for (var item in section.items) {
        String itemStatus = itemStatuses[item.subJobId] ?? item.statusId;
        if (itemStatus == '2') {
          hasFaulty = true;
        } else if (itemStatus == '3') {
          hasNA = true;
        }
      }

      if (hasFaulty) {
        sectionStatus = 2;
      } else if (hasNA) {
        sectionStatus = 3;
      } else {
        sectionStatus = 1;
      }

      List<clr.Item> itemsList = [];

      for (var item in section.items) {
        itemsList.add(
          clr.Item(
            title: item.title,
            comments: comments[item.subJobId]!.text.trim(),
            subJobId: int.tryParse(item.subJobId) ?? 1,
            statusId: int.tryParse(itemStatuses[item.subJobId] ?? item.statusId) ?? 1,
          ),
        );
      }

      result.add(
        clr.Section(
          jobId: int.tryParse(section.jobId) ?? 1,
          title: section.title,
          statusId: sectionStatus,
          comments: null,
          items: itemsList,
        ),
      );
    }

    return result;
  }
}

