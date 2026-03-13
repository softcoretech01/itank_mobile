import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:easy_stepper/easy_stepper.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:iso_tank/models/validation_response.dart';
import 'package:iso_tank/utils/constants.dart';
import 'package:dio/dio.dart'; // for FormData

import '../../bloc/tank_inspection/tank_inspection_bloc.dart';
import '../../models/request/check_list_request.dart';
import '../../repository/tank_repository.dart';
import '../../repository/upload_images_service.dart';
import '../../service/ApiClient.dart';
import '../../service/DioProvider.dart';
import '../../service/secure_storage_service.dart';
import 'package:iso_tank/screens/login_page.dart';
import '../../utils/app_colors.dart';
import '../../utils/snack_bar_helper.dart';
import 'components/check_list_card.dart';
import 'components/tank_info_page.dart';
import 'components/tank_inspection_review.dart';
import 'components/todo_page.dart';
import 'components/upload_photos_page.dart';

class TankInspectionFlow extends StatefulWidget {
  const TankInspectionFlow({super.key,});

  @override
  State<TankInspectionFlow> createState() => _TankInspectionFlowState();
}

class _TankInspectionFlowState extends State<TankInspectionFlow> {
  List<Section> collectedTodoItems = [];
  final GlobalKey<ChecklistPageState> checklistKey = GlobalKey();
  final GlobalKey<TodoPageState> todoKey = GlobalKey();
  final GlobalKey<TankInfoPageState> tankInfoKey = GlobalKey();
  final GlobalKey<UploadPhotosPageState> uploadPhotosKey = GlobalKey();
  late UploadImagesService uploadService;

  TankRepository? repo;
  String? errorMsg;
  double uploadProgress = 0;
  bool isUploading = false;
  int photoCount = 0;
  // Here we store selected images from UploadPhotosPage
  FormData selectedPhotos = FormData();
  int? inspectionId;
  String? tankId;
  bool canSubmit = false;

  void onPhotosSelected(FormData formData, int count) {
    selectedPhotos = formData; // store ready data
    photoCount = count;
  }




  @override
  void initState() {
    super.initState();
    final dio = DioProvider.createDio();
    repo = TankRepository(api: ApiClient(dio), dio: dio);
    uploadService = UploadImagesService(BASE_URL);
  }

  @override
  Widget build(BuildContext context) {

    return BlocConsumer<TankInspectionBloc, TankInspectionState>(
        // listenWhen: (p, c) =>
        //   p.uploadPhotos.flowStatus != c.uploadPhotos.flowStatus,
        listener: (context, state) {
            if (state.tankInfo.flowStatus == FlowStatus.saved) {
              showSnack(context, state.tankInfo.savedTankResponse?.message ?? "Saved");
              context.read<TankInspectionBloc>().add(GoToNextStepEvent());
              // context.read<TankInspectionBloc>().add(ResetTankInfoStateEvent());
            }else if (state.tankInfo.flowStatus == FlowStatus.error && state.error != null) {
              showSnack(context, state.error ?? "Something went wrong", isError: true);
              context.read<TankInspectionBloc>().add(ResetTankInfoStateEvent());
            }
            else if (state.uploadPhotos.flowStatus == FlowStatus.saved) {
              showSnack(context, "Image Uploaded successfully");
              context.read<TankInspectionBloc>().add(GoToNextStepEvent());
              context.read<TankInspectionBloc>().add(ResetTankInfoStateEvent());
            }
            else if (state.uploadPhotos.flowStatus == FlowStatus.error) {
              showSnack(context, state.uploadPhotos.error ?? "Upload failed", isError: true);
              context.read<TankInspectionBloc>().add(ResetTankInfoStateEvent());
            }else if (state.checklist.flowStatus == FlowStatus.error && state.error != null) {
              showSnack(context, state.error ?? "Something went wrong", isError: true);
              context.read<TankInspectionBloc>().add(ResetTankInfoStateEvent());
            }// ---------------- CHECKLIST SAVED ----------------
            else if (state.checklist.flowStatus == FlowStatus.saved) {
              showSnack(context,
                  state.checklist.checkListResponse?.message ?? "Saved");

              // Always go to TODO
              context.read<TankInspectionBloc>().add(GetTodoDataByIdEvent());
            }

            // ---------------- FETCH TODO COMPLETED ----------------
            else if (state.todoState.flowStatus == FlowStatus.saved) {
              showSnack(context, state.todoState.checkListResponse?.message ?? "Saved");
              // Navigation is handled in bloc, no need to refetch
            }else if (state.todoState.flowStatus == FlowStatus.ready) {
              // Always show TODO step and go to it
              context.read<TankInspectionBloc>().add(ShowTodoEvent());
              context.read<TankInspectionBloc>().add(GoToStepEvent(3));
            }

            // ---------------- VALIDATION COMPLETED ----------------
            else if (state.validationState.status == FlowStatus.saved) {
              print("Validation passed, all forms submitted.");
              // Validation success → No errors → Move to Review Page
              /// Jump to final step (Review & Submit)
              context.read<TankInspectionBloc>().add(GoToStepEvent(4));
            }

            else if (state.validationState.status == FlowStatus.error) {
              final resp = state.validationState.validationResponse;

              final title = resp?.message ?? "Validation Failed";
              final issueList = extractIssueReasons(resp);

              showValidationPopup(context, title, issueList);
            }


            else if (state.review.status == FlowStatus.ready) {
              final checklists = state.review.tankInspectionResponse?.data?.inspectionChecklist ?? [];
              canSubmit = !checklists.any((c) => c.statusName != 'OK' && c.statusName != 'NA');
            }else if (state.review.status == FlowStatus.submitted) {
              showSnack(context, state.review.message ?? "Saved");
              Future.microtask(() {
                if (!context.mounted) return;
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const TankInspectionFlow()),
                );
              });
            }

            // ---------------- VALIDATION ERROR HANDLER ---------------- 
            if (state.review.error != null && state.review.loading == false) {
              showSnack(context, "Validation error: ${state.review.error}", isError: true);
              // Clear error after showing
              context.read<TankInspectionBloc>().add(ClearValidationEvent());
            }

            // ---------------- VALIDATION RESPONSE HANDLER ---------------- 
            if (state.review.validationResponse != null) {
              final response = state.review.validationResponse!;
              print("VALIDATION RESPONSE RECEIVED: success=${response.success}");
              
              // Clear validation response immediately to prevent re-triggering
              context.read<TankInspectionBloc>().add(ClearValidationEvent());

              if (response.success == false) {
                // Show Error Dialog
                final issues = extractIssueReasons(response);
                if (issues.isEmpty) {
                   issues.add(response.message ?? "Validation failed");
                }
                print("SHOWING VALIDATION POPUP WITH ISSUES: $issues");
                showValidationPopup(context, "Cannot Submit Inspection", issues);
              } else {
                // Show Confirmation Dialog
                print("SHOWING CONFIRMATION DIALOG");
                _showSubmitConfirmation(context);
              }
            }
        },
        builder: (context, state) {
          final steps = [
            EasyStep(icon: Icon(Icons.storage), title: 'Tank Info'),
            EasyStep(icon: Icon(Icons.photo_camera), title: 'Upload Photos'),
            EasyStep(icon: Icon(Icons.checklist), title: 'Checklist'),

            if (state.showTodoStep == true)
              EasyStep(icon: Icon(Icons.list_alt), title: 'Todo'),

            EasyStep(icon: Icon(Icons.check_circle_outline), title: 'Review & Submit'),
          ];
          return PopScope(
            canPop: false,
            onPopInvokedWithResult: (bool didPop, dynamic result) async {
              if (didPop) return;
              final step = state.activeStep ?? 0;
              final stepsLength = steps.length;

              // Tank Info (step 0): confirm exit
              if (step == 0) {
                final shouldExit = await _showExitConfirmation(context);
                if (shouldExit == true && context.mounted) {
                  SystemNavigator.pop();
                }
                return;
              }

              // Upload Photos → Tank Info
              if (step == 1) {
                context.read<TankInspectionBloc>().add(GoToStepEvent(0));
                return;
              }

              // Checklist → Upload Photos
              if (step == 2) {
                context.read<TankInspectionBloc>().add(GoToStepEvent(1));
                return;
              }

              // Todo or Review (step 3 when no Todo) → Checklist
              if (step == 3) {
                context.read<TankInspectionBloc>().add(GoToStepEvent(2));
                return;
              }

              // Review & Submit (step 4 when Todo shown) → Todo / Checklist
              if (step == stepsLength - 1 && step >= 3) {
                context.read<TankInspectionBloc>().add(GoToStepEvent(step - 1));
              }
            },
            child: Scaffold(
            appBar: AppBar(
              title: const Text("Tank Inspection"),
              actions: [
                IconButton(
                  tooltip: 'Logout',
                  icon: const Icon(Icons.logout),
                  onPressed: () async {
                    // call logout API if available, then clear token and navigate to login
                    try {
                      await repo?.logout();
                    } catch (e) {
                      print('Logout API error: $e');
                    }

                    await secureStorage.clear();
                    if (!mounted) return;
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (_) => const LoginPage()),
                    );
                  },
                ),
              ],
            ),

            // ------------ FLOATING NAV BUTTONS ------------
            floatingActionButtonLocation: FloatingActionButtonLocation
                .centerFloat,
            floatingActionButton: Padding(
              padding: EdgeInsets.only(
                left: 30,
                right: 30,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // ---------- PREVIOUS BUTTON ----------
                  if ((state.activeStep ?? 0) > 0)
                    SizedBox(
                      width: 130,
                      height: 48,
                      child: FloatingActionButton.extended(
                        backgroundColor: Colors.grey.shade50,
                        heroTag: "prevBtn",
                        onPressed: () {
                          context.read<TankInspectionBloc>().add(GoToPreviousStepEvent());
                        },
                        label: const Text("Previous"),
                        icon: const Icon(Icons.arrow_back),
                      ),
                    )
                  else
                    const SizedBox(width: 130), // keep alignment balanced

                  // ---------- NEXT BUTTON ----------
                  SizedBox(
                    width: 200,
                    height: 48,
                    child: FloatingActionButton.extended(
                      backgroundColor:
                      (state.status == FlowStatus.saving || state.review.loading)
                          ? Colors.grey // disable color
                          : AppColors.primary,
                      heroTag: "nextBtn",
                      onPressed:
                      (state.status == FlowStatus.saving || state.review.loading)
                          ? null // 🔥 completely disable double taps and during validation
                          : () async {

                        // ---------- STEP 0: TANK INFO ----------
                        if (state.activeStep == 0) {
                          final tankData =
                          tankInfoKey.currentState?.getFormData();
                          if (tankData != null) {
                            context.read<TankInspectionBloc>().add(
                              SaveTankInfoEvent(tankInfoData: tankData),
                            );
                            print("Payload submitted: $tankData");
                          }
                        }

                        // ---------- STEP 1: UPLOAD IMAGES ----------
                        else if (state.activeStep == 1) {
                           // if (selectedPhotos.isNotEmpty) {
                             if (photoCount > 0) {
                               context.read<TankInspectionBloc>().add(
                                 UploadPhotosEvent(selectedPhotos),
                               );
                             } else {
                               // No photos to upload/update, skip network call
                               context.read<TankInspectionBloc>().add(GoToNextStepEvent());
                             }
                           // }
                        }

                        // ---------- STEP 2: CHECKLIST ----------
                        else if (state.activeStep == 2) {
                          final checklistState =
                              checklistKey.currentState;
                          final latestTodos =
                              checklistState?.collectSectionsForRequest() ?? [];

                          print("latestTodos == $latestTodos");

                          // Validate that faulty items have comments
                          bool hasValidationError = false;
                          for (var section in latestTodos) {
                            for (var item in section.items) {
                              if (item.statusId == 2 && item.comments.isEmpty) {
                                hasValidationError = true;
                                break;
                              }
                            }
                            if (hasValidationError) break;
                          }
                          if (hasValidationError) {
                            showSnack(context, "Please enter comments for all faulty items", isError: true);
                            return;
                          }

                          setState(() {
                            collectedTodoItems = latestTodos;
                          });

                          if (latestTodos.isNotEmpty) {
                            // await submitChecklist(steps.length);
                            context.read<TankInspectionBloc>().add(
                              SaveChecklistEvent(sections: collectedTodoItems),
                            );
                          }
                        }
                        else if (state.showTodoStep == true && state.activeStep == 3) {
                          final checklistState =
                              todoKey.currentState;
                          final latestTodos =
                              checklistState?.collectSectionsForRequest() ?? [];

                          print("latestTodos == $latestTodos");

                          // VALIDATE FAULTY ITEMS IN TODO
                          bool hasFaulty = false;
                          for (var s in latestTodos) {
                            for (var item in s.items) {
                              if (item.statusId == 2) {
                                hasFaulty = true;
                                break;
                              }
                            }
                          }
                          
                          if (hasFaulty) {
                            _showErrorDialog(context, "Please resolve all faulty items before proceeding");
                            return;
                          }

                          setState(() {
                            collectedTodoItems = latestTodos;
                          });

                          if (latestTodos.isNotEmpty) {
                            // await submitChecklist(steps.length);
                            context.read<TankInspectionBloc>().add(
                              UpdateTodoEvent(sections: collectedTodoItems),
                            );
                          }
                        }
                        // ---------- LAST STEP: SUBMIT ----------
                        else if (state.activeStep == steps.length - 1) {
                          print("SUBMIT BUTTON CLICKED - TRIGGERING VALIDATION");
                          print("Current inspectionId: ${state.inspectionId}");
                          
                          // Check if inspectionId is available
                          if (state.inspectionId == null) {
                            showSnack(context, "Inspection ID is missing. Please go back and create an inspection first.", isError: true);
                            return;
                          }
                          
                          // Trigger validation instead of direct confirmation
                          context.read<TankInspectionBloc>().add(ValidateInspectionEvent());
                        }

                        // 🔥 Let Bloc update state and re-enable button later
                      },
                      label: Text(
                        (state.activeStep == steps.length - 1)
                            ? "Submit"
                            : "Save & Next",
                        style: const TextStyle(color: Colors.white),
                      ),
                      icon: const Icon(Icons.arrow_forward, color: Colors.white),
                    ),
                  ),
                ],
              ),
            ),

            body: Stack(
              children: [
                Column(
                  children: [

                // ------------------- STEPPER --------------------
                EasyStepper(
                  activeStep: state.activeStep ?? 0,
                  steps: steps,
                  onStepReached: (index) {
                    // Check if attempting to go to Review Page (last step)
                    final isReviewStep = index == steps.length - 1;
                    
                    if (isReviewStep && state.showTodoStep == true) {
                      // Validate if there are any lingering faulty items in the BLOC state
                      // This forces the user to have SAVED the Todo list with resolved items first
                      final sections = state.todoState.checkListResponse?.data?.sections ?? [];
                      bool hasFaulty = false;
                      for (var s in sections) {
                        for (var item in s.items) {
                          if (item.statusId == "2") { // 2 == Faulty (String comparison)
                            hasFaulty = true; 
                            break;
                          }
                        }
                      }
                      
                      if (hasFaulty) {
                        _showErrorDialog(context, "Please resolve all faulty items before proceeding");
                        return; // Block navigation
                      }
                    }
                    
                    context.read<TankInspectionBloc>().add(GoToStepEvent(index));
                  },
                  internalPadding: 6,
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 8),
                  stepRadius: 18,
                  maxTitleLines: 1,
                  finishedStepBackgroundColor: Colors.green,
                  finishedStepIconColor: Colors.white,
                  titleTextStyle: const TextStyle(
                      fontSize: 10, fontWeight: FontWeight.w500),
                  lineStyle: LineStyle(
                    lineType: LineType.normal,
                    lineThickness: 2,
                    activeLineColor: Colors.grey,
                    finishedLineColor: Colors.green,
                    unreachedLineColor: Colors.grey,
                    lineLength: 40,
                  ),
                  showLoadingAnimation: false,
                ),

                const SizedBox(height: 10),

                // -------------------- PAGE VIEW ---------------------
                /*Expanded(
                  child: IndexedStack(
                    index: activeStep,
                    children: [
                      tankInfoPage(),
                      uploadPhotosPage(),
                      checklistPage(),
                      if (showTodoStep) todoPage(),
                      reviewPage(),
                    ],
                  ),
                ),
*/
                Expanded(
                  child: Builder(
                    builder: (_) {
                      switch (state.activeStep) {
                        case 0:
                          return tankInfoPage();
                        case 1:
                          return UploadPhotosPage(
                            key: uploadPhotosKey,
                            onPhotosSelected: onPhotosSelected,
                          );
                        case 2:
                          return checklistPage();
                        case 3:
                          if (state.showTodoStep == true) return todoPage();
                          return reviewPage();
                        default:
                          return reviewPage();
                      }
                    },
                  ),
                ),
                if (errorMsg != null) ...[
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      errorMsg!,
                      style: const TextStyle(color: Colors.red, fontSize: 14),
                    ),
                  )
                ]

                  ],
                ),

                // Upload overlay: full-screen loader when uploading images
                if (state.uploadPhotos.uploading)
                  Positioned.fill(
                    child: Material(
                      color: Colors.black54,
                      child: Center(
                        child: Card(
                          margin: const EdgeInsets.symmetric(horizontal: 32),
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const CircularProgressIndicator(),
                                const SizedBox(height: 20),
                                const Text(
                                  'Images uploading, please wait...',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  '${(state.uploadPhotos.progress * 100).toStringAsFixed(0)}%',
                                  style: const TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                if (photoCount > 0) ...[
                                  const SizedBox(height: 8),
                                  Text(
                                    'Uploading $photoCount image${photoCount == 1 ? '' : 's'}',
                                    style: TextStyle(
                                      fontSize: 14,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          );
        });
  }

  /// Shows exit confirmation when on Tank Info and user presses back. Returns true if user chose to exit.
  Future<bool?> _showExitConfirmation(BuildContext context) async {
    return showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Close application?'),
        content: const Text(
          'Do you want to close the application? Unsaved changes may be lost.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('No'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Yes'),
          ),
        ],
      ),
    );
  }

  /// ------------------- PAGE 1: TANK INFO -------------------
  Widget tankInfoPage() {
    return TankInfoPage(key: tankInfoKey);
  }

  /// ------------------- PAGE 2: UPLOAD PHOTOS -------------------
  Widget uploadPhotosPage() {
    return UploadPhotosPage(key: uploadPhotosKey,onPhotosSelected: onPhotosSelected,);
  }


  Widget checklistPage() {
    return ChecklistPage(
      key: checklistKey,
    );
  }

  /// ------------------- PAGE 4: TODO (OPTIONAL) -------------------

  Widget todoPage() {
    return TodoPage(
      key: todoKey,
    );
  }


  /// ------------------- PAGE 5: REVIEW -------------------
  Widget reviewPage() {
    return const TankInspectionReviewPage();
  }

  void _showSubmitConfirmation(BuildContext context) {
    showDialog(
      context: context,
      barrierDismissible: false, // cannot close by tapping outside
      builder: (context) {
        return AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          title: const Text(
            "Confirm Submission",
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          content: const Text(
            "Once submitted, data of this inspection cannot be edited.\nDo you want to continue?",
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context); // ❌ close popup
              },
              child: const Text("BACK"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context); // Close popup

                // ✅ Trigger submit event
                context.read<TankInspectionBloc>().add(
                  SubmitInspectionEvent(),
                );
              },
              child: const Text("SUBMIT"),
            ),
          ],
        );
      },
    );
  }

  List<String> extractIssueReasons(ValidationResponse? response) {
    final issues = response?.data?.issues;
    final List<String> allReasons = [];

    if (issues == null) return allReasons;

    // ---- checklist ----
    if (issues.checklist != null && issues.checklist!.isNotEmpty) {
      allReasons.add("Checklist not completed");
    }

    // ---- images list ----
    if (issues.images != null) {
      for (var img in issues.images!) {
        final reason = img.reason;
        
        // Handle "insufficient images" with regex parsing
        if (reason != null && reason.contains('insufficient images')) {
           final match = RegExp(r'found (\d+), expected (\d+)').firstMatch(reason);
           if (match != null) {
             allReasons.add('Insufficient images (${match.group(1)} / ${match.group(2)})');
           } else {
             allReasons.add(reason);
           }
        } 
        // Handle other reasons, skipping "missing images" container label if we list items
        else if (reason != null && reason.trim().isNotEmpty && reason != "missing images") {
           allReasons.add(reason);
        }

        // Add missing[] items
        if (img.missing != null && img.missing!.isNotEmpty) {
          for (var m in img.missing!) {
            allReasons.add("Missing image: ${m.imageType ?? 'Unknown'}");
          }
        }
      }
    }

    // ---- inspection ----
    if (issues.inspection != null) {
      allReasons.addAll(
          issues.inspection!
              .where((e) => e.reason != null && e.reason!.isNotEmpty)
              .map((e) => e.field! + " : " + e.reason!)
      );
    }

    // ---- to_do_list ----
    if (issues.toDoList != null) {
      allReasons.addAll(
          issues.toDoList!
              .where((e) => e.reason != null && e.reason!.isNotEmpty)
              .map((e) => e.reason!)
      );
    }

    print("EXTRACTED ISSUES: $allReasons");
    return allReasons;
  }


  void _showErrorDialog(BuildContext context, String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Action Required", style: TextStyle(color: Colors.red)),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }

  void showValidationPopup(BuildContext context, String title, List<String> issues) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          content: SizedBox(
            width: double.maxFinite,
            child: issues.isEmpty
                ? Container()
                : ListView.builder(
              shrinkWrap: true,
              itemCount: issues.length,
              itemBuilder: (context, index) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // const Icon(Icons.error, color: Colors.red, size: 20),
                      // const SizedBox(width: 8),
                      Expanded(child: Text("• ${issues[index]}", style: const TextStyle(fontSize: 16))),
                    ],
                  ),
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("OK"),
            ),
          ],
        );
      },
    );
  }


}
