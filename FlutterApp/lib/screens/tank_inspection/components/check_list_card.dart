import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shimmer/shimmer.dart';
import 'dart:async';

import '../../../bloc/tank_inspection/tank_inspection_bloc.dart';
import '../../../models/check_list_response.dart';
import '../../../models/request/check_list_request.dart' as clr;
import '../../../models/status_master_response.dart';
import '../../../repository/master_data.dart';

class ChecklistPage extends StatefulWidget {
  const ChecklistPage({super.key});

  @override
  State<ChecklistPage> createState() => ChecklistPageState();
}

class ChecklistPageState extends State<ChecklistPage> {
  Map<String, String?> status = {};
  Map<String, bool> showCommentBox = {};
  final Map<String, TextEditingController> comments = {};
  Map<String, String?> itemStatus = {};
  Map<String, String?> itemClicked = {};
  Map<String, bool> buttonDisabled = {};
  Map<String, Timer?> buttonTimers = {};

  List<Section> sections = [];

  MasterData? repo;
  List<StatusData> statusOptions = [];
  String? faultyId;

  String? _findStatusIdByKeywords(List<String> kws) {
    for (var s in statusOptions) {
      final name = s.statusName.toLowerCase();
      for (var k in kws) {
        if (name.contains(k)) return s.statusId.toString();
      }
    }
    return null;
  }

  @override
  void initState() {
    super.initState();
    context.read<TankInspectionBloc>().add(LoadChecklistMasterEvent());
  }

  @override
  void dispose() {
    comments.forEach((_, c) => c.dispose());
    buttonTimers.forEach((_, t) => t?.cancel());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<TankInspectionBloc, TankInspectionState>(
      listener: (context, state) {
        if (state.checklist.flowStatus == FlowStatus.ready &&
            state.checklist.checkListMasterData != null &&
            state.checklist.statusMasterResponse != null &&
            sections.isEmpty) {

          sections = state.checklist.checkListMasterData?.data?.sections ?? [];
          statusOptions = state.checklist.statusMasterResponse?.data ?? [];
          faultyId = _findStatusIdByKeywords(['fault', 'faulty', 'red']) ?? '2';

          for (var section in sections) {
            for (var item in section.items) {
              comments[item.subJobId] = TextEditingController();
              showCommentBox[item.subJobId] = false;
              itemStatus[item.subJobId] = '1'; // Default to green (OK)
              itemClicked[item.subJobId] = null;
              buttonDisabled[item.subJobId] = false;
            }
          }

          context.read<TankInspectionBloc>().add(GetChecklistByIdEvent());
        }

        if (state.checklist.flowStatus == FlowStatus.ready &&
            state.checklist.checkListResponse?.data != null) {

          final uploadedSections =
              state.checklist.checkListResponse!.data!.sections;

          for (var saved in uploadedSections) {
            status[saved.jobId] = saved.statusId;
            for (var savedItem in saved.items) {
              if (comments.containsKey(savedItem.subJobId)) {
                itemStatus[savedItem.subJobId] = savedItem.statusId;
                showCommentBox[savedItem.subJobId] =
                    savedItem.statusId == faultyId;
                comments[savedItem.subJobId]!.text = savedItem.comment;

              }
            }
          }
          setState(() {});
        }
      },
      builder: (context, state) {
        if (state.checklist.flowStatus == FlowStatus.loading) {
          return Scaffold(
            body: Center(
              child: Shimmer.fromColors(
                baseColor: Colors.grey[300]!,
                highlightColor: Colors.grey[100]!,
                child: Column(
                  children: List.generate(
                    18,
                    (_) => Container(
                      height: 20,
                      margin: const EdgeInsets.symmetric(vertical: 8),
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            ),
          );
        }

        return Scaffold(
          body: SingleChildScrollView(
            padding: const EdgeInsets.only(
                left: 16, right: 16, bottom: 200),
            child: Column(
              children: sections.map((section) {
                return checklistCard(section: section);
              }).toList(),
            ),
          ),
        );
      },
    );
  }

  // ------------------------------------------------------------
  // CHECKLIST CARD
  // ------------------------------------------------------------

  Widget checklistCard({required Section section}) {
    final faulty = faultyId ?? '2';
    const ok = '1';
    const na = '3';

    Color sectionColor() {
      for (var it in section.items) {
        if (itemStatus[it.subJobId] == faulty) return Colors.red;
      }
      return Colors.green;
    }

    Widget itemButton(String subJobId) {
      Color colorFor(String? s) {
        if (s == faulty) return Colors.red;
        if (s == na) return Colors.white;
        return Colors.green;
      }

      String nextState(String? current) {
        // Cycle: Green (1) → Red (2) → White (3) → Green (1)
        if (current == null || current == ok) return faulty;  // Green → Red
        if (current == faulty) return na;  // Red → White
        return ok;  // White → Green
      }

      final current = itemStatus[subJobId];
      final color = colorFor(current);

      return GestureDetector(
        onTap: buttonDisabled[subJobId] == true
            ? null
            : () {
                setState(() {
                  final ns = nextState(itemStatus[subJobId]);
                  itemStatus[subJobId] = ns;

                  showCommentBox[subJobId] = ns == faulty;
                  if (ns != faulty) comments[subJobId]?.clear();

                  buttonDisabled[subJobId] = true;
                  buttonTimers[subJobId]?.cancel();
                  buttonTimers[subJobId] =
                      Timer(const Duration(seconds: 1), () {
                    if (mounted) {
                      setState(() {
                        buttonDisabled[subJobId] = false;
                      });
                    }
                  });
                });
              },
        child: Column(
          children: [
            Container(
              width: 19,
              height: 19,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.grey),
              ),
              // No tick mark - just solid color circle
            ),
            if (buttonDisabled[subJobId] == true)
              const Padding(
                padding: EdgeInsets.only(top: 4),
                child: Text(
                  "WAIT FOR A SECOND",
                  style: TextStyle(fontSize: 9, color: Colors.red),
                ),
              )
          ],
        ),
      );
    }

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(section.title,
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                Container(
                  width: 18,
                  height: 18,
                  decoration: BoxDecoration(
                    color: sectionColor(),
                    shape: BoxShape.circle,
                  ),
                )
              ],
            ),
            const Divider(),
            ...section.items.map((item) {
              final id = item.subJobId;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text("${item.subJobId} ${item.title}"),
                      ),
                      itemButton(id),
                    ],
                  ),
                  if (showCommentBox[id] == true)
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: TextField(
                        controller: comments[id],
                        decoration: const InputDecoration(
                          hintText: "Enter comment",
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                  const SizedBox(height: 8),
                ],
              );
            }),
          ],
        ),
      ),
    );
  }

  // ------------------------------------------------------------
  // COLLECT DATA FOR SAVE
  // ------------------------------------------------------------

  List<clr.Section> collectSectionsForRequest() {
    List<clr.Section> result = [];

    for (var section in sections) {
      bool anyFaulty = false;

      for (var it in section.items) {
        if (itemStatus[it.subJobId] == faultyId) {
          anyFaulty = true;
          break;
        }
      }

      final sectionStatus =
          anyFaulty ? int.parse(faultyId!) : 1;

      result.add(
        clr.Section(
          jobId: int.tryParse(section.jobId) ?? 1,
          title: section.title,
          statusId: sectionStatus,
          comments: null,
          items: section.items.map((i) {
            return clr.Item(
              title: i.title,
              subJobId: int.tryParse(i.subJobId) ?? 1,
              statusId:
                  int.tryParse(itemStatus[i.subJobId] ?? '1') ?? 1,
              comments: (comments[i.subJobId]?.text ?? '').trim(),

            );
          }).toList(),
        ),
      );
    }

    return result;
  }
}
