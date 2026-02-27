
import 'package:dio/dio.dart';
import 'package:iso_tank/models/tank_details_response.dart';
import 'package:iso_tank/models/upload_image_type_response.dart';
import 'package:retrofit/retrofit.dart';
import '../models/api_result.dart';
import '../models/check_list_response.dart';
import '../models/get_uploaded_mages_response.dart';
import '../models/login_response.dart';
import '../models/request/login_request.dart';
import '../models/status_master_response.dart';
import '../models/submit_review_response.dart';
import '../models/tank_info_response.dart';
import '../models/tank_inspection_response.dart';
import '../models/tank_master_data.dart';
import '../models/tank_model.dart';
import '../models/validation_response.dart';
import '../utils/constants.dart';

part 'ApiClient.g.dart'; // 👈 REQUIRED

// @RestApi(baseUrl: "https://jsonplaceholder.typicode.com/")
// @RestApi(baseUrl: "http://192.168.0.118:8000/api/")
// @RestApi(baseUrl: "http://172.27.113.2:8000/api/")
// @RestApi(baseUrl: "http://192.168.1.33:8000/api/")
@RestApi(baseUrl: BASE_URL)
abstract class ApiClient {
  factory ApiClient(Dio dio, {String baseUrl}) = _ApiClient;

  @POST("auth/login")
  Future<LoginResponse> login(@Body() LoginRequest request);

  @POST("auth/logout")
  Future<dynamic> logout(@Header("Authorization") String token);

  // Tank Inspection APIs
  @GET("tank_inspection_checklist/active-tanks")
  Future<TankModel> getTanks();

  @GET("tank_inspection_checklist/masters")
  Future<TankMasterResponse> fetchTankMasterData();

  @GET("tank_inspection_checklist/tank-details/{id}")
  Future<TankDetailsResponse> fetchTankDetailsByID(
      @Path("id") String id);

  // Latest draft inspection id for a tank (scoped by emp_id + is_submitted = 0)
  @GET("tank_inspection_checklist/inspection/latest-draft/{tank_id}")
  Future<TankDetailsResponse> fetchLatestDraftInspectionId(
      @Path("tank_id") int tankId);

  @GET("tank_inspection_checklist/get/inspection/{id}")
  Future<TankDetailsResponse> getInspectionById(
      @Path("id") int id);

  @POST("tank_inspection_checklist/{inspection_id}/lifter_weight")
  @MultiPart()
  Future<ApiResult> addLifterWeight(
      @Path("inspection_id") int inspectionId,
      @Part(name: "file") MultipartFile? file,
      );

  @POST("/tank_inspection_checklist/create/tank_inspection")
  Future<TankInfoResponse> createTankInspection(
      @Header("Authorization") String token,
      @Body() Map<String, dynamic> tankData,
      );

  @PUT("tank_inspection_checklist/update/tank_inspection_details/{inspection_id}")
  Future<TankInfoResponse> updateTankInspection(
      @Path("inspection_id") int inspectionId,
      @Body() Map<String, dynamic> tankData,
      );

  //Upload Image Page APIs

  @GET("upload/types")
  Future<UploadImageTypeResponse> fetchUploadImageTypes();

  @GET("upload/images/inspection/{inspection_id}")
  Future<GetUploadedImagesResponse> getUploadedImages(
      @Path("inspection_id") int inspectionId,
      );

  //Checklist Page APIs

  @GET("tank_checkpoints/export/checklist")
  Future<CheckListResponse> getChecklist();

  @GET("tank_checkpoints/inspection_status")
  Future<StatusMasterResponse> getStatusMaster();

  @POST("tank_checkpoints/create/inspection_checklist_bulk")
  Future<CheckListResponse> submitChecklistBulk(
      @Header("Authorization") String token,
      @Header("inspection_id") int inspectionId,
      @Body() Map<String, dynamic> payload,
      );

  @PUT("tank_checkpoints/update/checklist")
  Future<CheckListResponse> updateCheckList(
      @Header("Authorization") String token,
      @Header("inspection_id") int inspectionId,
      @Body() Map<String, dynamic> payload,
      );

  @GET("tank_checkpoints/get/checklist_by_inspection_id/{inspection_id}")
  Future<CheckListResponse> getCheckListsById(
      @Header("Authorization") String token,
      @Path("inspection_id") int inspectionId,
      );

  //To-Do List Page APIs

  @GET("to_do_list/flagged/inspection/{id}/grouped/")
  Future<CheckListResponse> getToDoData(
      @Path("id") int inspectionId,
      );

  @PUT("to_do_list/update")
  Future<CheckListResponse> updateTodoList(
      @Header("Authorization") String token,
      @Body() Map<String, dynamic> payload,
      );

  // Review & Submit Page APIs

  @GET("tank_inspection_checklist/review/{id}")
  Future<TankInspectionResponse> getInspectionReview(
      @Path("id") int inspectionId,
  );

  @GET("tank_inspection_checklist/submit")
  Future<SubmitReviewResponse> submitReview(
      @Header("inspection-id") int inspectionId,
  );

  @GET("validation/inspection/{id}")
  Future<ValidationResponse> checkAllFormsValidated(
      @Path("id") int inspectionId,
      );

  @POST("upload/{tank_number}/{image_type}")
  @MultiPart()
  Future<HttpResponse> uploadTankImage(
      @Path("tank_number") String tankNumber,
      @Path("image_type") String imageType,
      @Part(name: "file") MultipartFile file,
      );

  @DELETE("upload/images/{inspection_id}")
  Future<ApiResult> deletePhoto(
      @Header("Authorization") String token,
      @Path("inspection_id") int inspectionId,
      );

}
