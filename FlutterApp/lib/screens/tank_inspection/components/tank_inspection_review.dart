import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:iso_tank/bloc/tank_inspection/tank_inspection_bloc.dart';

import '../../../models/tank_inspection_response.dart';
import '../../../models/validation_response.dart';
import '../../../utils/constants.dart';

class TankInspectionReviewPage extends StatefulWidget {
  const TankInspectionReviewPage({super.key});

  @override
  State<TankInspectionReviewPage> createState() =>
      TankInspectionReviewPageState();
}

class TankInspectionReviewPageState extends State<TankInspectionReviewPage> {
  bool showChecklistError = false;
  bool showTodoError = false;
  List<String> missingImages = [];
  String? insufficientImagesMessage;

  @override
  void initState() {
    super.initState();
    print("Loading review data");

    context.read<TankInspectionBloc>().add(LoadReviewEvent());
  }

  void _showValidationDialog(BuildContext context, ValidationResponse response) {
    if (response.success != true) {
      // Error dialog
      final validationIssues = response.data?.issues;
      final checklistIssues = validationIssues?.checklist ?? [];
      final imageIssues = validationIssues?.images ?? [];
      final todoIssues = validationIssues?.toDoList ?? [];
      final inspectionIssues = validationIssues?.inspection ?? [];

      final messages = <String>[];

      if (checklistIssues.isNotEmpty) {
        messages.add('Checklist not completed');
      }
      if (imageIssues.isNotEmpty) {
        for (var issue in imageIssues) {
          final reason = issue.reason;
          if (reason != null && reason.contains('insufficient images')) {
            final match = RegExp(r'found (\d+), expected (\d+)').firstMatch(reason);
            if (match != null) {
              messages.add('Insufficient images (${match.group(1)} / ${match.group(2)})');
            } else {
              messages.add(reason);
            }
          } else if (reason != null) {
            messages.add(reason);
          }
          // Handle missing images
          if (issue.missing != null) {
            for (var missing in issue.missing!) {
              messages.add('Missing image: ${missing.imageType}');
            }
          }
        }
      }
      if (todoIssues.isNotEmpty) {
        for (var issue in todoIssues) {
          if (issue.reason != null) {
            messages.add(issue.reason!);
          }
        }
      }
      for (var issue in inspectionIssues) {
        if (issue.reason != null) {
          messages.add(issue.reason!);
        }
      }

      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text("Cannot Submit Inspection"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: messages.map((msg) => Text('• $msg')).toList(),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("OK"),
            ),
          ],
        ),
      );
    } else {
      // Success, show confirmation
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text("Confirm Submission"),
          content: const Text("Once submitted, data of this inspection cannot be edited.\nDo you want to continue?"),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Back"),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                context.read<TankInspectionBloc>().add(SubmitInspectionEvent());
              },
              child: const Text("OK"),
            ),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<TankInspectionBloc, TankInspectionState>(
        listener: (context, state) {
          // Validation and submission logic moved to TankInspectionFlow
        },
        builder: (context, state) {
          if (state.review.status == FlowStatus.loading) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          } else if (state.review.status == FlowStatus.ready) {
            final inspection = state.review.tankInspectionResponse?.data?.inspection;
            final images = state.review.tankInspectionResponse?.data?.images;
            final checklist = state.review.tankInspectionResponse?.data?.inspectionChecklist;

            // We can still pass these for display if needed, but the dialogs are handled in Flow
            return TankInspectionReview(
              inspection: inspection,
              images: images,
              checklist: checklist,
              showChecklistError: false,
              showTodoError: false,
              missingImages: [],
              insufficientImagesMessage: null,
              inspectionId: inspection?.inspectionId ?? 0,
            );
          } else if (state.review.status == FlowStatus.error) {
            return Scaffold(
              body: Center(child: Text("Error: ${state.review.error}")),
            );
          }
          return Container();
        });
  }
}


class TankInspectionReview extends StatelessWidget {
  final Inspection? inspection;
  final List<InspectionImage>? images;
  final List<InspectionChecklist>? checklist;
  final bool showChecklistError;
  final bool showTodoError;
  final List<String> missingImages;
  final String? insufficientImagesMessage;
  final int inspectionId;

  const TankInspectionReview({
    super.key,
    required this.inspection,
    required this.images,
    required this.checklist,
    required this.showChecklistError,
    required this.showTodoError,
    required this.missingImages,
    required this.insufficientImagesMessage,
    required this.inspectionId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Inspection Review")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _sectionTitle("Tank Information"),
            _tankInfoCard(inspection),

            if (showChecklistError || showTodoError || insufficientImagesMessage != null || missingImages.isNotEmpty) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                margin: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  border: Border.all(color: Colors.red),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Validation Issues:',
                      style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    if (showChecklistError)
                      const Text('• Checklist not completed', style: TextStyle(color: Colors.red)),
                    if (showTodoError)
                      const Text('• To-do list not completed', style: TextStyle(color: Colors.red)),
                    if (insufficientImagesMessage != null)
                      Text('• $insufficientImagesMessage', style: const TextStyle(color: Colors.red)),
                    ...missingImages.map((img) => Text('• Missing image: $img', style: const TextStyle(color: Colors.red))).toList(),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 24),

            _sectionTitle("Uploaded Images"),
            _imageGrid(images, context),

            const SizedBox(height: 24),

            _sectionTitle("Checklist Review"),
            _checklistCard(checklist),

            const SizedBox(height: 24),

            const SizedBox(height: 200),

            const SizedBox(height: 200),

          ],
        ),
      ),
    );
  }

  // ------------------------------------------------------------------------
  // SECTION TITLE
  // ------------------------------------------------------------------------
  Widget _sectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
    );
  }

  // ------------------------------------------------------------------------
  // TANK INFO CARD  (USING MODEL)
  // ------------------------------------------------------------------------
  Widget _tankInfoCard(Inspection? data) {
    final fields = {
      "Report Number": data?.reportNumber,
      "Tank Number": data?.tankNumber,
      "Pressure (Bar)": data?.workingPressure,
      "Design Temperature": "${data?.designTemperature ?? ""} °C".trim(),
      "Frame Type": data?.frameType,
      "Cabinet Type": data?.cabinetType,
      "Manufacturer": data?.mfgr,
      "Ownership": data?.ownership,
      "Next Inspection Date": data?.piNextInspectionDate,
      "Vacuum Reading": data?.vacuumReading,
      "Lifter Weight": data?.lifterWeightValue,
      "Status": data?.status,
      "Inspection Type": data?.inspectionType,
      "Safety Valve": data?.safetyValveBrand,
      "Product": data?.product,
      "Location": data?.location,
    };

    return Card(
      elevation: 3,
      margin: const EdgeInsets.only(top: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: fields.entries.map((e) {
            final value = e.value?.toString().trim();
            final displayValue = (value == null || value.isEmpty) ? "-" : value;
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 4,
                    child: Text(
                      e.key,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                  Expanded(
                    flex: 6,
                    child: Text(
                      displayValue,
                      textAlign: TextAlign.left,
                      style: TextStyle(color: Colors.grey[700]),
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  // ------------------------------------------------------------------------
  // IMAGE GRID  (USING MODEL)
  // ------------------------------------------------------------------------
  Widget _imageGrid(List<InspectionImage>? images, BuildContext context) {
    return GridView.builder(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
      ),
      itemCount: images?.length ?? 0,
      itemBuilder: (ctx, i) {
        String fullPath = images?[i].imagePath ?? "";

        return GestureDetector(
          onTap: () => _openFullImage(context, fullPath),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.network("$IMAGE_BASE_URL$fullPath", fit: BoxFit.cover),
          ),
        );
      },
    );
  }

  void _openFullImage(BuildContext context, String image) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => Scaffold(
          backgroundColor: Colors.black,
          appBar: AppBar(backgroundColor: Colors.black),
          body: Center(
            child: InteractiveViewer(child: Image.network(image)),
          ),
        ),
      ),
    );
  }

  // ------------------------------------------------------------------------
  // CHECKLIST CARD (USING MODEL)
  // ------------------------------------------------------------------------
  Widget _checklistCard(List<InspectionChecklist>? checklist1) {
    List<InspectionChecklist> checklist = checklist1 ?? [];
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: checklist.map((check) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Job header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        check.title,
                        style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.bold),
                      ),
                    ),
                    _statusBadge(check.status),
                  ],
                ),
                const SizedBox(height: 8),
                // Subjobs
                ...check.items.map((subItem) {
                  return Padding(
                    padding: const EdgeInsets.only(left: 16, bottom: 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                subItem.title,
                                style: const TextStyle(fontSize: 14),
                              ),
                            ),
                            _statusBadge(subItem.statusName),
                          ],
                        ),
                        if (subItem.comment.trim().isNotEmpty) ...[
                          const SizedBox(height: 6),
                          const Text(
                            "Comment:",
                            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                          ),
                          Text(
                            subItem.comment,
                            style: const TextStyle(
                              fontSize: 13,
                              color: Colors.black87,
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                }),
                const Divider(),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }

// Example status badge function
  Widget _statusBadge(String? status) {
    if (status == null || status.isEmpty) {
      return const SizedBox();
    }

    int? id = int.tryParse(status);
    Color bgColor;
    if (id != null) {
      // Status is ID
      if (id == 1) {
        bgColor = Colors.green; // OK
      } else if (id == 2) {
        bgColor = Colors.grey; // NA
      } else if (id == 3) {
        bgColor = Colors.red; // Flagged
      } else {
        bgColor = Colors.blue; // Other
      }
    } else {
      // Status is name
      String lower = status.toLowerCase();
      if (lower == "ok") {
        bgColor = Colors.green;
      } else if (lower == "na") {
        bgColor = Colors.grey;
      } else if (lower == "flagged") {
        bgColor = Colors.red;
      } else {
        bgColor = Colors.blue;
      }
    }

    return Chip(
      label: Text(status),
      backgroundColor: bgColor,
      labelStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
    );
  }

  bool _isValidStatus(String? status) {
    if (status == null) return false;
    String lower = status.toLowerCase();
    return lower == "ok" || lower == "na";
  }

}

