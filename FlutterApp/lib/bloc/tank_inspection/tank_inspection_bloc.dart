import 'package:bloc/bloc.dart';
import 'package:dio/dio.dart';
import 'package:iso_tank/models/api_result.dart';
import 'package:iso_tank/models/get_uploaded_mages_response.dart';
import 'package:iso_tank/models/tank_master_data.dart';
import 'package:iso_tank/models/tank_model.dart';
import 'package:iso_tank/models/validation_response.dart';
import 'dart:async';
import 'dart:io';
import '../../models/check_list_response.dart' hide Section;
import '../../models/request/check_list_request.dart';
import '../../models/request/tank_info_data.dart';
import '../../models/status_master_response.dart';
import '../../models/submit_review_response.dart';
import '../../models/tank_details_response.dart';
import '../../models/tank_info_response.dart';
import '../../models/tank_inspection_response.dart';
import '../../models/upload_image_type_response.dart';
import '../../repository/tank_repository.dart';

part 'tank_inspection_event.dart';
part 'tank_inspection_state.dart';

class TankInspectionBloc extends Bloc<TankInspectionEvent, TankInspectionState> {
  final TankRepository repo;

  TankInspectionBloc(this.repo) : super(TankInspectionState.initial()) {
    on<InitializeFlowEvent>(_onInitialize);
    on<SaveTankInfoEvent>(_onSaveTankInfo);
    on<SelectTankEvent>(_onSelectTank);
    on<GetImageTypesEvent>(_fetchImageTypes);
    on<GetUploadedImagesEvent>(_fetchUploadedImages);
    on<UploadPhotosEvent>(_onUploadPhotos);
    on<UploadProgressEvent>(_onUploadProgress);
    on<DeleteUploadedPhotoEvent>(_onDeletePhoto);
    on<LoadChecklistMasterEvent>(_onLoadChecklist);
    on<SaveChecklistEvent>(_onSaveChecklist);
    on<GetChecklistByIdEvent>(_fetchCheckListDataById);
    on<GetTodoDataByIdEvent>(_fetchTodoDataById);
    on<CheckAllFormsSubmittedByIdEvent>(_checkAllFormsAreFilled);
    on<ShowTodoEvent>(_onShowTodoStep);
    on<UpdateTodoEvent>(_onSaveTodo);
    on<LoadReviewEvent>(_onLoadReview);
    on<ValidateInspectionEvent>(_onValidateInspection);
    on<ClearValidationEvent>((event, emit) {
      // Manually construct ReviewState to ensure validationResponse is set to null
      // because copyWith(validationResponse: null) uses the old value due to ?? operator.
      emit(state.copyWith(review: ReviewState(
        loading: state.review.loading,
        status: state.review.status,
        tankInspectionResponse: state.review.tankInspectionResponse,
        validationResponse: null, // Explicitly null
        submitReviewResponse: state.review.submitReviewResponse,
        error: state.review.error,
        message: state.review.message,
      )));
    });
    on<SubmitInspectionEvent>(_onSubmitInspection);
    on<ResetTankInfoStateEvent>((event, emit) {
      emit(state.copyWith(
        // Only reset tank info
        tankInfo: state.tankInfo.copyWith(
            flowStatus: FlowStatus.initial
        ),
        // Only reset uploadPhotos flow (optional)
          uploadPhotos: state.uploadPhotos.copyWith(
            uploading: false,
            progress: 0.0,
            error: null,
            flowStatus: FlowStatus.initial,
          ),
        checklist: state.checklist.copyWith(
            flowStatus: FlowStatus.initial
        ),
        // Keep inspectionId intact
        // inspectionId: state.inspectionId,  <-- no need to reset
        error: null,
      ));
    });
    on<ResetAfterSubmitStateEvent>((event, emit) {
      print("Resetting state after submission...");
      emit(state.copyWith(
        inspectionId: null,
        tankId: null,
        activeStep: 0,
        error: null,
        isUpdate:false,
        // Only reset tank info
        masterDataState: state.masterDataState.copyWith(
            flowStatus: FlowStatus.initial
        ),

        tankInfo: state.tankInfo.copyWith(
            flowStatus: FlowStatus.initial
        ),        // Only reset uploadPhotos flow (optional)
        uploadPhotos: state.uploadPhotos.copyWith(
          uploading: false,
          progress: 0.0,
          error: null,
          flowStatus: FlowStatus.initial,
        ),
        checklist: state.checklist.copyWith(
            flowStatus: FlowStatus.initial
        ),
        review:  state.review.copyWith(
            status: FlowStatus.initial
        ),
        validationState:  state.validationState.copyWith(
            status: FlowStatus.initial
        ),
        todoState:  state.todoState.copyWith(
            flowStatus: FlowStatus.initial
        ),

      ));
    });
    on<GoToNextStepEvent>((event, emit) {
      final nextStep = (state.activeStep ?? 0) + 1;
      if (nextStep == 4) {
        add(LoadReviewEvent());
      }
      emit(state.copyWith(activeStep: nextStep));
    });
    on<GoToPreviousStepEvent>((event, emit) {
      final current = state.activeStep ?? 0;
      if (current > 0) {
        emit(state.copyWith(activeStep: current - 1));
      }
    });
    on<GoToStepEvent>((event, emit) {
      if (event.step == 4) {
        add(LoadReviewEvent());
      }
      emit(state.copyWith(activeStep: event.step));
    });

  }


  Future<void> _onInitialize(InitializeFlowEvent e, Emitter emit) async {
    emit(state.copyWith(status: FlowStatus.loading, error: null));
    try {
      // load master data common to pages (e.g. status master)
      final master = await repo.fetchMasterData();
      /*emit(state.copyWith(
        masterDataState: state.masterDataState.copyWith(
            flowStatus: FlowStatus.ready,
            masterData: master),
      ));
*/
      // Fetch Active Tanks
      final review = await repo.fetchTanks();
      // map to state models (Inspection, images, checklist)
      emit(state.copyWith(
        masterDataState: state.masterDataState.copyWith(
            flowStatus: FlowStatus.ready,
          activeTanks: review,
            masterData: master
        ),
      ));

      if( state.tankId != null ){
        add(SelectTankEvent(state.tankId));
      }

    } catch (err) {
      emit(state.copyWith(status: FlowStatus.error, error: err.toString()));
    }
  }
  void _onSelectTank(
      SelectTankEvent event,
      Emitter<TankInspectionState> emit,
      ) async {
    emit(state.copyWith(status: FlowStatus.loading, error: null));

    try {
      // ------------------------------------
      // 1️⃣ Fetch tank details (tank master only)
      // ------------------------------------
      final tankDetails = await repo.fetchTankDetailsByID(event.tank ?? 0);

      // ------------------------------------
      // 2️⃣ Independently fetch latest draft inspection for this tank+emp
      // ------------------------------------
      final inspectionId = await repo.fetchLatestDraftInspectionId(event.tank ?? 0);

      // ------------------------------------
      // 3️⃣ CASE A — No draft inspection exists → fresh form
      // ------------------------------------
      if (inspectionId == null) {
        emit(state.copyWith(
          tankInfo: state.tankInfo.copyWith(
            // Always keep master tank details available for UI
            selectedTank: tankDetails,
            inspectionDetails: null,
          ),
          tankId: event.tank,
          inspectionId: null,
          isUpdate: false,
          status: FlowStatus.ready,
        ));
        return;
      }

      // ------------------------------------
      // 4️⃣ CASE B — Draft inspection exists → Load and prefill form
      // ------------------------------------
      try {
        final inspectionDetails = await repo.getInspectionById(inspectionId);

        emit(state.copyWith(
          tankInfo: state.tankInfo.copyWith(
              // Keep tank master details separate from inspection-specific data
              selectedTank: tankDetails,
              inspectionDetails: inspectionDetails,
            flowStatus: FlowStatus.ready,
          ),
          tankId: event.tank,
          inspectionId: inspectionId,
          isUpdate: true,
          status: FlowStatus.ready,
        ));

      } catch (e) {
        emit(state.copyWith(
          status: FlowStatus.error,
          error: "Inspection API error: ${e.toString()}",
        ));
      }

    } catch (e) {
      // ------------------------------------
      // Catches ANY error from first API
      // ------------------------------------
      emit(state.copyWith(
        status: FlowStatus.error,
        error: "Tank details API error: ${e.toString()}",
      ));
    }
  }



  Future<void> _onSaveTankInfo(SaveTankInfoEvent e, Emitter emit) async {
    emit(state.copyWith(
        status: FlowStatus.saving,
        tankInfo: state.tankInfo.copyWith(flowStatus: FlowStatus.saving),
        error: null,
    ));
    try {
      final payload = {
        "created_by": "",
        "tank_id": e.tankInfoData.tankId,
        "notes": e.tankInfoData.reportNumber,
        "status_id": e.tankInfoData.tankStatus,
        "inspection_type_id": e.tankInfoData.inspectionType,
        "product_id": e.tankInfoData.product,
        "location_id": e.tankInfoData.location,
        "safety_valve_brand_id": e.tankInfoData.safetyValve,
        "vacuum_reading": e.tankInfoData.vacuumReading,
        "lifter_weight_value": e.tankInfoData.lifterWeightValue,
      };

      final TankInfoResponse? res;

      // ********************************************************
      // 🚀 1. CALL CORRECT API (Create OR Update)
      // ********************************************************
      if (e.tankInfoData.inspectionId != null) {
        res = await repo.updateTankInspection(
          inspectionId: e.tankInfoData.inspectionId!,
          payload: payload,
        );

      } else {
        res = await repo.createTankInspection(payload: payload);
      }

      if ((res.success == true) && res.data != null) {
        final inspectionId = res.data?.inspectionId;
        // -----------------------------------------------
        // NEW PART: AFTER SUCCESS, UPLOAD LIFTER PHOTO
        // -----------------------------------------------
        if (e.tankInfoData.lifterPhoto != null) {
          await repo.submitLifterWeight(
            lifterPhoto: e.tankInfoData.lifterPhoto!,
            inspectionId: inspectionId ?? 0,
          );
        }

        emit(state.copyWith(
          tankInfo: state.tankInfo.copyWith(
            savedTankResponse: res,
              flowStatus: FlowStatus.saved
          ),
          inspectionId: inspectionId,
          status: FlowStatus.ready,
        ));

        // 🚀 Add this reset immediately so UI won’t see READY twice
        emit(state.copyWith(
          tankInfo: state.tankInfo.copyWith(flowStatus: FlowStatus.initial),
        ));

      } else {
        emit(state.copyWith(
            status: FlowStatus.error, error: res.message,
          tankInfo: state.tankInfo.copyWith(
            flowStatus: FlowStatus.error
          )
        ));}
    } catch (err) {
      emit(state.copyWith(status: FlowStatus.error, error: err.toString(),
          tankInfo: state.tankInfo.copyWith(
              flowStatus: FlowStatus.error
          )));
    }
  }
  // Upload images Methods

  void _fetchImageTypes(
      GetImageTypesEvent event,
      Emitter<TankInspectionState> emit,
      ) async {
    emit(state.copyWith(
      status: FlowStatus.loading,
      uploadPhotos: state.uploadPhotos.copyWith(
          flowStatus: FlowStatus.loading),
      error: null,
    ));
    final details = await repo.getUploadImageTypes();

    emit(state.copyWith(
      uploadPhotos: state.uploadPhotos.copyWith(
          uploadImageTypeResponse: details,
        flowStatus: FlowStatus.ready
      ),
      status: FlowStatus.ready,
    ));

    // ⬇️ AFTER IMAGE TYPES ARE LOADED → check inspectionId
    if (state.inspectionId != null) {
      add(GetUploadedImagesEvent(state.inspectionId!));
    }
  }

  void _fetchUploadedImages(
      GetUploadedImagesEvent event,
      Emitter<TankInspectionState> emit,
      ) async {
    emit(state.copyWith(
      uploadPhotos: state.uploadPhotos.copyWith(flowStatus: FlowStatus.loading),
    ));

    final uploaded = await repo.getUploadedImages(state.inspectionId ?? 0);

    if (uploaded.success && uploaded.data != null) {
      // final Map<int, List<String>> grouped = {};
      //
      // for (var img in uploaded.data!.images) {
      //   grouped.putIfAbsent(img.imageTypeId, () => []);
      //   grouped[img.imageTypeId]!.add(img.imagePath);
      // }

      emit(state.copyWith(
        uploadPhotos: state.uploadPhotos.copyWith(
          uploadedNetworkPhotos: uploaded,
          flowStatus: FlowStatus.ready,
        ),
      ));
    }

  }


  Future<void> _onUploadPhotos(
      UploadPhotosEvent e,
      Emitter<TankInspectionState> emit,
      ) async {

    emit(state.copyWith(
      uploadPhotos: state.uploadPhotos.copyWith(
        uploading: true,
        progress: 0.0,
        error: null,
        flowStatus: FlowStatus.saving,
      ),
    ));

    final bool isUpdate = state.uploadPhotos.uploadedNetworkPhotos?.data?.images.isNotEmpty == true;


    try {
      final result = await (
          isUpdate == true
              ? repo.updateImagesWithProgress(
            inspectionId: state.inspectionId!,
            formData: e.photos,
            onProgress: (sent, total) {
              final progress = total > 0 ? (sent / total) : 0.0;
              add(UploadProgressEvent(progress));
            },
          )
          : repo.uploadImagesWithProgress(
            inspectionId: state.inspectionId!,
            formData: e.photos,
            onProgress: (sent, total) {
              final progress = total > 0 ? (sent / total) : 0.0;
              add(UploadProgressEvent(progress));
            },
          )
      );

      if (!result.success) {
        emit(state.copyWith(
          uploadPhotos: state.uploadPhotos.copyWith(
            uploading: false,
            error: result.message,
            flowStatus: FlowStatus.error,
          ),
        ));
        return;
      }

      emit(state.copyWith(
        uploadPhotos: state.uploadPhotos.copyWith(
          uploading: false,
          flowStatus: FlowStatus.saved,
        ),
      ));

      // Reset
      emit(state.copyWith(
        uploadPhotos: state.uploadPhotos.copyWith(flowStatus: FlowStatus.initial),
      ));

    } catch (e) {
      emit(state.copyWith(
        uploadPhotos: state.uploadPhotos.copyWith(
          uploading: false,
          error: e.toString(),
          flowStatus: FlowStatus.error,
        ),
      ));
    }
  }


  void _onUploadProgress(
      UploadProgressEvent e,
      Emitter<TankInspectionState> emit,
      ) {
    emit(state.copyWith(
      uploadPhotos: state.uploadPhotos.copyWith(
        progress: e.progress,
        flowStatus: FlowStatus.uploading,
      ),
    ));
  }

  Future<void> _onDeletePhoto(DeleteUploadedPhotoEvent e, Emitter emit) async {
    emit(state.copyWith(
        status: FlowStatus.loading, error: null,
        deletedPhotosState: state.deletedPhotosState.copyWith(
          flowStatus: FlowStatus.loading)
    ));

    try {

      final ApiResult result =  await repo.deleteUploadedPhoto(e.imageId);

      if (result.success) {
        // Update state
        emit(
          state.copyWith(
            status: FlowStatus.saved,
            deletedPhotosState: state.deletedPhotosState.copyWith(
              apiResult: result,
              flowStatus: FlowStatus.saved,
            ),
          ),
        );

        if (state.uploadPhotos.uploadedNetworkPhotos != null) {
          state.uploadPhotos.uploadedNetworkPhotos!.data!.images.removeWhere((img) => img.id == e.imageId);
          emit(state.copyWith(
            uploadPhotos: state.uploadPhotos.copyWith(
              flowStatus: FlowStatus.ready,
              uploadedNetworkPhotos: state.uploadPhotos.uploadedNetworkPhotos,
            ),
          ));
        }

        // Reset flowStatus to avoid UI re-trigger
        emit(
          state.copyWith(
            deletedPhotosState: state.deletedPhotosState.copyWith(
              flowStatus: FlowStatus.initial,
            ),
          ),
        );

      } else {
        emit(
          state.copyWith(
            status: FlowStatus.error,
            error: result.message,
          ),
        );
      }
    } catch (err) {
      emit(
        state.copyWith(
          status: FlowStatus.error,
          error: err.toString(),
        ),
      );
    }
  }

  Future<void> _onLoadChecklist(LoadChecklistMasterEvent e, Emitter emit) async {
    emit(state.copyWith(status: FlowStatus.loading, error: null));
    try {
      final checklistResp = await repo.fetchChecklist(); // returns List<ChecklistSection>
      final statusRepo = await repo.fetchStatusMaster(); // returns List<ChecklistSection>
      emit(state.copyWith(
          checklist: state.checklist.copyWith(
              checkListMasterData: checklistResp,
              statusMasterResponse: statusRepo,
              flowStatus: FlowStatus.ready
          ), status: FlowStatus.ready));
    } catch (err) {
      emit(state.copyWith(status: FlowStatus.error, error: err.toString()));
    }
  }

  void _fetchCheckListDataById(
      GetChecklistByIdEvent event,
      Emitter<TankInspectionState> emit,
      ) async {
    emit(state.copyWith(
      checklist: state.checklist.copyWith(flowStatus: FlowStatus.loading),
    ));

    final uploaded = await repo.fetchChecklistDataUsingId(state.inspectionId ?? 0);

    if (uploaded.success && uploaded.data != null) {
        emit(state.copyWith(
        checklist: state.checklist.copyWith(
          checkListResponse: uploaded,
          flowStatus: FlowStatus.ready,
        ),
      ));
    }else{
      emit(state.copyWith(
        checklist: state.checklist.copyWith(
          checkListResponse: uploaded,
          flowStatus: FlowStatus.error,
        ),
      ));
    }

  }

  Future<void> _onSaveChecklist(SaveChecklistEvent e, Emitter emit) async {
    emit(state.copyWith(status: FlowStatus.saving, error: null,
    checklist: state.checklist.copyWith(
      flowStatus: FlowStatus.saving,
    )));

    try {
      if (state.inspectionId == null) {
        throw Exception("Inspection ID missing");
      }

      final request = CheckListRequest(
        inspectionId: state.inspectionId!.toString(),
        tankId: state.tankId?.toString() ?? "",
        sections: e.sections,
      );

      final bool isUpdate = state.checklist.checkListResponse?.data?.sections.isNotEmpty == true;
      // If checklist already exists → UPDATE
      // If no checklist saved before → SUBMIT

      final CheckListResponse result = isUpdate
          ? await repo.updateChecklistBulk(request, state.inspectionId!)
          : await repo.submitChecklistBulk(request, state.inspectionId!);

      if (result.success) {
        // Update state
        emit(
          state.copyWith(
            status: FlowStatus.saved,
            checklist: state.checklist.copyWith(
              checkListResponse: result,
              flowStatus: FlowStatus.saved,
            ),
          ),
        );

        // Reset flowStatus to avoid UI re-trigger
        emit(
          state.copyWith(
            checklist: state.checklist.copyWith(
              flowStatus: FlowStatus.initial,
            ),
          ),
        );

      } else {
        print("Checklist save error: ${result.message}");
        emit(
          state.copyWith(
            status: FlowStatus.error,
            error: result.message,
            checklist: state.checklist.copyWith(
              flowStatus: FlowStatus.error,
            ),
          ),
        );
      }
    } catch (err) {
      emit(
        state.copyWith(
          status: FlowStatus.error,
          error: err.toString(),
          checklist: state.checklist.copyWith(
            flowStatus: FlowStatus.error,
          ),
        ),
      );
    }
  }

  void _fetchTodoDataById(
      GetTodoDataByIdEvent event,
      Emitter<TankInspectionState> emit,
      ) async {
    emit(state.copyWith(
      todoState: state.todoState.copyWith(flowStatus: FlowStatus.loading),
    ));

    try {
      final response = await repo.fetchTodoDataUsingId(state.inspectionId ?? 0);

      final todoSections = response.data?.sections ?? [];

      // 🔥 NAVIGATION DECISION BASED ON DATA
      final hasTodo = todoSections.isNotEmpty;
      final targetStep = 3;  // Always 3 (If Todo exists -> it's step 3. If no Todo -> Review shifts to step 3)

      if (!hasTodo) {
        add(LoadReviewEvent());
      }

      emit(state.copyWith(
        todoState: state.todoState.copyWith(
          flowStatus: FlowStatus.saved,
          checkListResponse: response,
        ),
        showTodoStep: hasTodo,
        activeStep: targetStep,
      ));

      // reset flow status to avoid re-trigger
      emit(state.copyWith(
        todoState: state.todoState.copyWith(
          flowStatus: FlowStatus.initial,
        ),
      ));
    } catch (e) {
      emit(state.copyWith(
        todoState: state.todoState.copyWith(
          flowStatus: FlowStatus.error,
          error: e.toString(),
        ),
        showTodoStep: false,
        activeStep: 3, // Review fallback, index 3 when no todo
      ));

      // reset flow status to avoid re-trigger
      emit(state.copyWith(
        todoState: state.todoState.copyWith(
          flowStatus: FlowStatus.initial,
        ),
      ));
    }

  }

  Future<void> _onSaveTodo(UpdateTodoEvent e, Emitter emit) async {
    emit(state.copyWith(status: FlowStatus.saving, error: null));

    try {
      if (state.inspectionId == null) {
        throw Exception("Inspection ID missing");
      }

      final request = CheckListRequest(
        inspectionId: state.inspectionId!.toString(),
        tankId: state.tankId?.toString() ?? "",
        sections: e.sections,
      );

      final CheckListResponse result =
          await repo.updateTodoBulk(request, state.inspectionId!);

      if (result.success) {
        // Update state
        emit(
          state.copyWith(
            status: FlowStatus.ready,
            todoState: state.todoState.copyWith(
              checkListResponse: result,
              flowStatus: FlowStatus.saved,
            ),
          ),
        );

        // Refetch TODO to check if still faulty
        add(GetTodoDataByIdEvent());

        // Reset flowStatus to avoid UI re-trigger
        emit(
          state.copyWith(
            todoState: state.todoState.copyWith(
              flowStatus: FlowStatus.initial,
            ),
          ),
        );
      } else {
        emit(
          state.copyWith(
            status: FlowStatus.error,
            error: result.message,
            todoState: state.todoState.copyWith(
              flowStatus: FlowStatus.error,
            ),
          ),
        );
      }
    } catch (err) {
      emit(
        state.copyWith(
          status: FlowStatus.error,
          error: err.toString(),
          todoState: state.todoState.copyWith(
            flowStatus: FlowStatus.error,
          ),
        ),
      );
    }
  }

  void _checkAllFormsAreFilled(
      CheckAllFormsSubmittedByIdEvent event,
      Emitter<TankInspectionState> emit,
      ) async {
    emit(state.copyWith(
      validationState: state.validationState.copyWith(status: FlowStatus.loading),
    ));

    final uploaded = await repo.checkAllFormsAreSubmitted(state.inspectionId ?? 0);

    if (uploaded.success == true) {
        emit(state.copyWith(
          validationState: state.validationState.copyWith(
          validationResponse: uploaded,
          status: FlowStatus.saved,
        ),
      ));
        // reset flow status to avoid re-trigger
        emit(state.copyWith(
          validationState: state.validationState.copyWith(
            status: FlowStatus.initial,
          ),
        ));
    }else{
      emit(state.copyWith(
        validationState: state.validationState.copyWith(
          validationResponse: uploaded,
          status: FlowStatus.error,
        ),
      ));

      // reset flow status to avoid re-trigger
      emit(state.copyWith(
        validationState: state.validationState.copyWith(
          status: FlowStatus.initial,
        ),
      ));
    }

  }

  void _onShowTodoStep(
      ShowTodoEvent event,
      Emitter<TankInspectionState> emit,
      ) {
    emit(state.copyWith(showTodoStep: true));
  }


  Future<void> _onLoadReview(LoadReviewEvent e, Emitter emit) async {
    emit(state.copyWith(status: FlowStatus.loading, error: null));
    try {
      if (state.inspectionId == null) throw Exception("inspection id missing");
      final review = await repo.getTankReviewData(state.inspectionId!);
      // final review = await repo.getTankReviewData(1);
      if (review.success) {
        emit(state.copyWith(
          status: FlowStatus.ready,
          review: state.review.copyWith(
            tankInspectionResponse: review,
            status: FlowStatus.ready
          )
        ));
      } else {
        emit(state.copyWith(status: FlowStatus.error, error: review.message));
      }
    } catch (err) {
      emit(state.copyWith(status: FlowStatus.error, error: err.toString()));
    }
  }

  Future<void> _onValidateInspection(ValidateInspectionEvent e, Emitter emit) async {
    print("VALIDATION EVENT RECEIVED - inspectionId: ${state.inspectionId}");
    
    // Explicitly clear validationResponse on start to avoid old data triggering listener
    emit(state.copyWith(review: ReviewState(
      loading: true,
      status: state.review.status,
      tankInspectionResponse: state.review.tankInspectionResponse,
      validationResponse: null, // Explicitly null
      submitReviewResponse: state.review.submitReviewResponse,
      error: null,
      message: state.review.message,
    )));
    try {
      if (state.inspectionId == null) {
        print("ERROR: inspection id missing");
        throw Exception("inspection id missing");
      }
      print("CALLING VALIDATION API with inspectionId: ${state.inspectionId}");
      final validation = await repo.checkAllFormsValidated(state.inspectionId!);
      print("VALIDATION API RESPONSE: success=${validation.success}, message=${validation.message}");
      emit(state.copyWith(
        review: state.review.copyWith(
          validationResponse: validation,
          loading: false
        )
      ));
    } catch (err) {
      print("VALIDATION ERROR: $err");
      emit(state.copyWith(review: state.review.copyWith(loading: false, error: err.toString())));
    }
  }

  Future<void> _onSubmitInspection(SubmitInspectionEvent e, Emitter emit) async {
    emit(state.copyWith(status: FlowStatus.saving, error: null));
    try {
      // if (state.inspectionId == null) throw Exception("inspection id missing");
      final res = await repo.postReviewData(inspectionId: state.inspectionId!);
      // final res = await repo.postReviewData(inspectionId: 1);
      if (res.success == true) {
        emit(state.copyWith(
          status: FlowStatus.submitted,
        review: state.review.copyWith(
            status: FlowStatus.submitted,
            submitReviewResponse: res,
            message: res.message
        ),
        ));
        //reset other states after submission
        // add(ResetAfterSubmitStateEvent());

        emit(TankInspectionState.initial());
        //reset state to initial after submission
        emit(state.copyWith(
          review: state.review.copyWith(
              status: FlowStatus.initial,
          ),
        ));
      } else {
        emit(state.copyWith(
            status: FlowStatus.error, error: res.message,
        review: state.review.copyWith(
            status: FlowStatus.error,
        )));
      }
    } catch (err) {
      emit(state.copyWith(
          status: FlowStatus.error, error: err.toString(),
          review: state.review.copyWith(
          status: FlowStatus.error,
      )));
    }
  }
}

