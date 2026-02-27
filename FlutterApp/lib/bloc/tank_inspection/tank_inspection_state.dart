part of 'tank_inspection_bloc.dart';

enum FlowStatus { initial, loading, ready, saving, saved, uploading, error, submitted }

class TankInspectionState {
  final FlowStatus status;
  final int? inspectionId;
  final int? activeStep;
  final int? tankId;
  final bool? isUpdate;
  final bool? showTodoStep;
  final MasterDataState masterDataState;
  final TankInfoState tankInfo;
  final UploadPhotosState uploadPhotos;
  final DeletedPhotosState deletedPhotosState;
  final ChecklistState checklist;
  final TodoState todoState;
  final ValidationState validationState;
  final ReviewState review;

  final String? error;

  TankInspectionState({
    required this.status,
    this.inspectionId,
    this.activeStep = 0,
    this.tankId,
    this.isUpdate,
    this.showTodoStep,
    required this.masterDataState,
    required this.tankInfo,
    required this.checklist,
    required this.uploadPhotos,
    required this.deletedPhotosState,
    required this.todoState,
    required this.validationState,
    required this.review,
    this.error,
  });

  factory TankInspectionState.initial() => TankInspectionState(
    status: FlowStatus.initial,
    masterDataState: MasterDataState(),
    tankInfo: TankInfoState(),
    checklist: ChecklistState(),
    uploadPhotos: UploadPhotosState(),
    deletedPhotosState: DeletedPhotosState(),
    review: ReviewState(),
    todoState: TodoState(),
    validationState: ValidationState(),
  );

  TankInspectionState copyWith({
    FlowStatus? status,
    int? activeStep,
    int? inspectionId,
    int? tankId,
    bool? isUpdate,
    bool? showTodoStep,
    MasterDataState? masterDataState,
    TankInfoState? tankInfo,
    ChecklistState? checklist,
    UploadPhotosState? uploadPhotos,
    DeletedPhotosState? deletedPhotosState,
    ReviewState? review,
    TodoState? todoState,
    ValidationState? validationState,
    String? error,
  }) {
    return TankInspectionState(
      status: status ?? this.status,
      activeStep: activeStep ?? this.activeStep,
      inspectionId: inspectionId ?? this.inspectionId,
      tankId: tankId ?? this.tankId,
      isUpdate: isUpdate ?? this.isUpdate,
      showTodoStep: showTodoStep ?? this.showTodoStep,
      masterDataState: masterDataState ?? this.masterDataState,
      tankInfo: tankInfo ?? this.tankInfo,
      checklist: checklist ?? this.checklist,
      uploadPhotos: uploadPhotos ?? this.uploadPhotos,
      deletedPhotosState: deletedPhotosState ?? this.deletedPhotosState,
      review: review ?? this.review,
      todoState: todoState ?? this.todoState,
      validationState: validationState ?? this.validationState,
      error: error ?? this.error,
    );
  }
}
class MasterDataState {
  final FlowStatus flowStatus;
  final bool loading;
  final TankMasterResponse? masterData;
  final TankModel? activeTanks;
  final String? error;

  MasterDataState({
    this.loading = false,
    this.flowStatus = FlowStatus.initial,
    this.masterData,
    this.activeTanks,
    this.error,
  });

  MasterDataState copyWith({
    FlowStatus? flowStatus,
    bool? loading,
    TankMasterResponse? masterData,
    TankModel? activeTanks,
    String? error,
  }) {
    return MasterDataState(
      flowStatus: flowStatus ?? this.flowStatus,
      loading: loading ?? this.loading,
      masterData: masterData ?? this.masterData,
      activeTanks: activeTanks ?? this.activeTanks,
      error: error ?? this.error,
    );
  }
}

class TankInfoState {
  final FlowStatus flowStatus;
  final bool loading;
  final Inspection? existingInspection;
  final TankInfoResponse? savedTankResponse;
  /// Tank master data from /tank-details/{tank_id}
  final TankDetailsResponse? selectedTank;
  /// Inspection-specific data from /get/inspection/{inspection_id}
  final TankDetailsResponse? inspectionDetails;
  final String? error;

  TankInfoState({
    this.loading = false,
    this.flowStatus = FlowStatus.initial,
    this.selectedTank,
    this.inspectionDetails,
    this.existingInspection,
    this.savedTankResponse,
    this.error,
  });

  TankInfoState copyWith({
    FlowStatus? flowStatus,
    bool? loading,
    TankMasterResponse? masterData,
    Inspection? existingInspection,
    TankModel? activeTanks,
    TankDetailsResponse? selectedTank,
    TankDetailsResponse? inspectionDetails,
    TankInfoResponse? savedTankResponse,
    String? error,
  }) {
    return TankInfoState(
      flowStatus: flowStatus ?? this.flowStatus,
      loading: loading ?? this.loading,
      existingInspection: existingInspection ?? this.existingInspection,
      selectedTank: selectedTank ?? this.selectedTank,
      inspectionDetails: inspectionDetails ?? this.inspectionDetails,
      savedTankResponse: savedTankResponse ?? this.savedTankResponse,
      error: error ?? this.error,
    );
  }
}
class ChecklistState {
  FlowStatus? flowStatus;
  bool? loading;
  CheckListResponse? checkListMasterData;
  StatusMasterResponse? statusMasterResponse;
  CheckListResponse? checkListResponse;
  final List<InspectionChecklist> items;
  final String? error;

  ChecklistState({
    this.flowStatus = FlowStatus.initial,
    this.loading = false,
    this.items = const [],
    this.checkListMasterData,
    this.statusMasterResponse,
    this.checkListResponse,
    this.error,
  });

  ChecklistState copyWith({
    bool? loading,
    List<InspectionChecklist>? items,
    FlowStatus? flowStatus,
    CheckListResponse? checkListMasterData,
    StatusMasterResponse? statusMasterResponse,
    CheckListResponse? checkListResponse,
    String? error,
  }) {
    return ChecklistState(
      loading: loading ?? this.loading,
      flowStatus: flowStatus ?? this.flowStatus,
      checkListMasterData: checkListMasterData ?? this.checkListMasterData,
      statusMasterResponse: statusMasterResponse ?? this.statusMasterResponse,
      checkListResponse: checkListResponse ?? this.checkListResponse,
      items: items ?? this.items,
      error: error ?? this.error,

    );
  }
}

class DeletedPhotosState {
  final FlowStatus? flowStatus;
  final bool deleting;
  final String? error;
  final ApiResult? apiResult;

  DeletedPhotosState({
    this.flowStatus = FlowStatus.initial,
    this.deleting = false,
    this.error,
    this.apiResult,
  });

  DeletedPhotosState copyWith({
    FlowStatus? flowStatus,
    bool? deleting,
    String? error,
    ApiResult? apiResult,
  }) {
    return DeletedPhotosState(
      flowStatus: flowStatus ?? this.flowStatus,
      deleting: deleting ?? this.deleting,
      error: error ?? this.error,
      apiResult: apiResult ?? this.apiResult,
    );
  }
}
class UploadPhotosState {
  final FlowStatus? flowStatus;
  final UploadImageTypeResponse? uploadImageTypeResponse;
  final GetUploadedImagesResponse? uploadedNetworkPhotos;
  final bool uploading;
  final double progress; // 0–1
  final List<InspectionImage> uploadedImages;
  final String? error;

  UploadPhotosState({
    this.flowStatus = FlowStatus.initial,
    this.uploadImageTypeResponse,
    this.uploadedNetworkPhotos,
    this.uploading = false,
    this.progress = 0.0,
    this.uploadedImages = const [],
    this.error,
  });

  UploadPhotosState copyWith({
    FlowStatus? flowStatus,
    UploadImageTypeResponse? uploadImageTypeResponse,
    GetUploadedImagesResponse? uploadedNetworkPhotos,
    bool? uploading,
    double? progress,
    List<InspectionImage>? uploadedImages,
    String? error,
  }) {
    return UploadPhotosState(
      flowStatus: flowStatus ?? this.flowStatus,
      uploadImageTypeResponse: uploadImageTypeResponse ?? this.uploadImageTypeResponse,
      uploadedNetworkPhotos: uploadedNetworkPhotos ?? this.uploadedNetworkPhotos,
      uploading: uploading ?? this.uploading,
      progress: progress ?? this.progress,
      uploadedImages: uploadedImages ?? this.uploadedImages,
      error: error ?? this.error,
    );
  }
}

class TodoState {
  FlowStatus? flowStatus;
  bool? loading;
  CheckListResponse? checkListMasterData;
  StatusMasterResponse? statusMasterResponse;
  CheckListResponse? checkListResponse;
  final List<InspectionChecklist> items;
  final String? error;

  TodoState({
    this.flowStatus = FlowStatus.initial,
    this.loading = false,
    this.items = const [],
    this.checkListMasterData,
    this.statusMasterResponse,
    this.checkListResponse,
    this.error,
  });

  TodoState copyWith({
    bool? loading,
    List<InspectionChecklist>? items,
    FlowStatus? flowStatus,
    CheckListResponse? checkListMasterData,
    StatusMasterResponse? statusMasterResponse,
    CheckListResponse? checkListResponse,
    String? error,
  }) {
    return TodoState(
      loading: loading ?? this.loading,
      flowStatus: flowStatus ?? this.flowStatus,
      checkListMasterData: checkListMasterData ?? this.checkListMasterData,
      statusMasterResponse: statusMasterResponse ?? this.statusMasterResponse,
      checkListResponse: checkListResponse ?? this.checkListResponse,
      items: items ?? this.items,
      error: error ?? this.error,

    );
  }
}

class ValidationState {
  final bool loading;
  final FlowStatus status;
  final ValidationResponse? validationResponse;
  final String? error;
  final String? message;

  ValidationState({
    this.loading = false,
    this.status = FlowStatus.initial,
    this.validationResponse,
    this.error,
    this.message,
  });

  ValidationState copyWith({
    bool? loading,
    FlowStatus? status,
    ValidationResponse? validationResponse,
    String? error,
    String? message,
  }) {
    return ValidationState(
      loading: loading ?? this.loading,
      status: status ?? this.status,
      validationResponse: validationResponse ?? this.validationResponse,
      error: error ?? this.error,
      message: message ?? this.message,
    );
  }
}

class ReviewState {
  final bool loading;
  final FlowStatus status;
  final TankInspectionResponse? tankInspectionResponse;
  final ValidationResponse? validationResponse;
  final SubmitReviewResponse? submitReviewResponse;
  final String? error;
  final String? message;

  ReviewState({
    this.loading = false,
    this.status = FlowStatus.initial,
    this.tankInspectionResponse,
    this.validationResponse,
    this.submitReviewResponse,
    this.error,
    this.message,
  });

  ReviewState copyWith({
    bool? loading,
    FlowStatus? status,
    TankInspectionResponse? tankInspectionResponse,
    ValidationResponse? validationResponse,
    SubmitReviewResponse? submitReviewResponse,
    String? error,
    String? message,
  }) {
    return ReviewState(
      loading: loading ?? this.loading,
      status: status ?? this.status,
      tankInspectionResponse: tankInspectionResponse ?? this.tankInspectionResponse,
      validationResponse: validationResponse ?? this.validationResponse,
      submitReviewResponse: submitReviewResponse ?? this.submitReviewResponse,
      error: error ?? this.error,
      message: message ?? this.message,
    );
  }
}




