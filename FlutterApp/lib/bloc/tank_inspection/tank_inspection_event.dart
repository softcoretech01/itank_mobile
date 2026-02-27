part of 'tank_inspection_bloc.dart';

abstract class TankInspectionEvent {}

class InitializeFlowEvent extends TankInspectionEvent {
  InitializeFlowEvent();
}

class SaveTankInfoEvent extends TankInspectionEvent {
  final TankInfoData tankInfoData;
  SaveTankInfoEvent({required this.tankInfoData});
}

class SelectTankEvent extends TankInspectionEvent {
  final int? tank;
  SelectTankEvent(this.tank);
}

class GetInspectionDataByIdEvent extends TankInspectionEvent {
  final int? inspectionId;
  final int? tankId;

  GetInspectionDataByIdEvent({
    required this.inspectionId,
    required this.tankId,
  });
}

class GetImageTypesEvent extends TankInspectionEvent{}

class GetUploadedImagesEvent extends TankInspectionEvent {
  final int inspectionId;
  GetUploadedImagesEvent(this.inspectionId);
}

class UploadPhotosEvent extends TankInspectionEvent {
  final FormData photos;
  final void Function(double progress)? onProgress;

  UploadPhotosEvent(this.photos, {this.onProgress});
}
class DeleteUploadedPhotoEvent extends TankInspectionEvent {
  final int imageId;
  DeleteUploadedPhotoEvent({required this.imageId});
}

class UploadProgressEvent extends TankInspectionEvent {
  final double progress;
  UploadProgressEvent(this.progress);
}

class UpdateUploadPhotosEvent extends TankInspectionEvent {
  final Map<int, List<File>> photos;
  final void Function(double progress)? onProgress;

  UpdateUploadPhotosEvent(this.photos, {this.onProgress});
}

class UpdateUploadProgressEvent extends TankInspectionEvent {
  final double progress;
  UpdateUploadProgressEvent(this.progress);
}



class LoadChecklistMasterEvent extends TankInspectionEvent {}

class SaveChecklistEvent extends TankInspectionEvent {
  final List<Section> sections;
  SaveChecklistEvent({required this.sections});
}

class UpdateChecklistEvent extends TankInspectionEvent {
  final List<Section> sections;
  UpdateChecklistEvent({required this.sections});
}

class GetChecklistByIdEvent extends TankInspectionEvent {
  GetChecklistByIdEvent();
}

class GetTodoDataByIdEvent extends TankInspectionEvent {
  GetTodoDataByIdEvent();
}

class ShowTodoEvent extends TankInspectionEvent {}

class UpdateTodoEvent extends TankInspectionEvent {
  final List<Section> sections;
  UpdateTodoEvent({required this.sections});
}

class CheckAllFormsSubmittedByIdEvent extends TankInspectionEvent {
  CheckAllFormsSubmittedByIdEvent();
}

class LoadReviewEvent extends TankInspectionEvent {}

class ValidateInspectionEvent extends TankInspectionEvent {}

class ClearValidationEvent extends TankInspectionEvent {}

class SubmitInspectionEvent extends TankInspectionEvent {}

class ResetTankInfoStateEvent extends TankInspectionEvent {}

class GoToNextStepEvent extends TankInspectionEvent {}
class GoToPreviousStepEvent extends TankInspectionEvent {}
class GoToStepEvent extends TankInspectionEvent {
  final int step;
  GoToStepEvent(this.step);
}
class ClearFlowStatusEvent extends TankInspectionEvent {}

class ResetAfterSubmitStateEvent extends TankInspectionEvent {}






