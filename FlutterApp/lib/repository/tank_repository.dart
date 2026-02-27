import 'dart:convert';
import 'dart:io';


import 'package:dio/dio.dart';
import 'package:iso_tank/models/validation_response.dart';
import '../models/api_result.dart';
import '../models/get_uploaded_mages_response.dart';
import '../models/request/check_list_request.dart';
import '../models/status_master_response.dart';
import '../models/submit_review_response.dart';
import '../models/tank_info_response.dart';
import '../models/tank_inspection_response.dart';
import '../models/tank_master_data.dart';
import '../models/tank_model.dart';
import '../models/upload_image_type_response.dart';
import '../service/ApiClient.dart';
import '../models/tank_details_response.dart';
import '../models/check_list_response.dart';
import '../service/secure_storage_service.dart';

// ----------------------------------------------------------
// HELPER FUNCTIONS
// ----------------------------------------------------------

bool _looksLikeHtml(dynamic d) {
  if (d == null) return false;
  if (d is String) {
    final s = d.trimLeft();
    return s.startsWith('<') && s.length < 10000; // heuristic for HTML error page
  }
  return false;
}

class TankRepository {
  final ApiClient api;
  final Dio dio;

  TankRepository({
    required this.api,
    required this.dio,
  });


  //----------------------------------------------------------
  // FETCH MASTER DATA
  //----------------------------------------------------------
  Future<TankMasterResponse> fetchMasterData() {
    return api.fetchTankMasterData();
  }
  Future<CheckListResponse> fetchChecklist() async {
    return await api.getChecklist();
  }
  Future<StatusMasterResponse> fetchStatusMaster() async {
    return await api.getStatusMaster();
  }
  Future<TankModel> fetchTanks() {
    return api.getTanks();
  }

  //----------------------------------------------------------
  // ️Tank Inspection APIs
  //----------------------------------------------------------

  Future<TankDetailsResponse> fetchTankDetailsByID(int tankId) async {
    try {
      final response = await api.fetchTankDetailsByID("$tankId");
      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;
        print("❌ fetchTankDetailsByID - Dio Error: ${e.response}");

        // FastAPI / Pydantic style error
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);
            return TankDetailsResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            return TankDetailsResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error
        return TankDetailsResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Fallback unexpected error
      print("❌ Unexpected error fetching tank details: $e");
      return TankDetailsResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }


  // ----------------------------------------------------------
  //  Get Inspection Details
  // ----------------------------------------------------------
  Future<TankDetailsResponse> getInspectionById(int id) async {
    try {
      final response = await api.getInspectionById(id);
      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;
        print("❌ getInspectionById - Dio Error: ${e.response}");

        // FastAPI / Pydantic validation errors
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);
            return TankDetailsResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            return TankDetailsResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend message
        return TankDetailsResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected
      print("❌ Unexpected error fetching inspection: $e");
      return TankDetailsResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }



  // ----------------------------------------------------------
  // Create / Update Tank Inspection (JSON Body)
  // ----------------------------------------------------------


  Future<int?> fetchLatestDraftInspectionId(int tankId) async {
    try {
      final resp = await api.fetchLatestDraftInspectionId(tankId);
      final id = resp.data?.inspectionId;
      print("Latest draft inspectionId for tank $tankId => $id");
      return id;
    } catch (e) {
      print("❌ Error fetching latest draft inspection id: $e");
      return null;
    }
  }

  Future<TankInfoResponse> createTankInspection({
    required Map<String, dynamic> payload,
  }) async {
    try {
      print("Payload => $payload");
      final token = await secureStorage.getToken();
      print("TOKEN BEFORE CREATE => $token");
      if (token == null || token.isEmpty) {
        // Do NOT call backend with an empty/invalid token – surface a clear error instead.
        throw Exception("Token missing before createTankInspection API call");
      }

      // Retrofit API call
      final TankInfoResponse response =
          await api.createTankInspection("Bearer $token", payload);

      print("API Response => ${response.toJson()}");

      return response;   // success or failure handled by UI

    } catch (e, stack) {
      print("RAW ERROR => $e");
      print("STACK => $stack");

      // ---------- HANDLE DIO ERRORS ----------
      if (e is DioException) {
        final data = e.response?.data;
        print("DIO ERROR RESPONSE => $data");

        // Backend validation (FastAPI-style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          final error = ApiErrorResponse.fromJson(data);
          return TankInfoResponse(
            success: false,
            message: error.detail.first.msg,
          );
        }

        // Simple backend error message
        if (data is Map<String, dynamic> && data.containsKey("message")) {
          return TankInfoResponse(
            success: false,
            message: data["message"].toString(),
          );
        }

        return TankInfoResponse(
          success: false,
          message: "Server error",
        );
      }

      // ---------- NON-DIO ERROR ----------
      return TankInfoResponse(
        success: false,
        message: e.toString(),
      );
    }
  }


  // ----------------------------------------------------------
  // 3️⃣ Upload Lifter Weight Photo
  // ----------------------------------------------------------
  Future<ApiResult> submitLifterWeight({
    required int inspectionId,
    File? lifterPhoto,
  }) async {
    try {
      MultipartFile? lifterFile;

      if (lifterPhoto != null) {
        lifterFile = await MultipartFile.fromFile(
          lifterPhoto.path,
          filename: "lifter_${DateTime.now().millisecondsSinceEpoch}.jpg",
        );
      }

      final response = await api.addLifterWeight(
        inspectionId,
        lifterFile,
      );

      if (response.success == true) {
        return ApiResult.success(response.data);
      } else {
        return ApiResult.error("Something went wrong");
      }
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("🚨 Dio Error Response:");
        print(e.response);

        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          final error = ApiErrorResponse.fromJson(data);

          return ApiResult.error(
            error.detail.first.msg,
            error,
          );
        }
      }

      return ApiResult.error("Unexpected error occurred");
    }
  }


  Future<TankInfoResponse> updateTankInspection({
    required int inspectionId,
    required Map<String, dynamic> payload,
  }) async {
    try {
      final TankInfoResponse response =
      await api.updateTankInspection(inspectionId, payload);

      return response;
    } catch (e) {

      if (e is DioException) {
        final data = e.response?.data;
        print("DIO ERROR RESPONSE => $data");

        // FastAPI-style error
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          final error = ApiErrorResponse.fromJson(data);
          return TankInfoResponse(
            success: false,
            message: error.detail.first.msg,
          );
        }

        // Normal backend error message
        if (data is Map<String, dynamic> && data.containsKey("message")) {
          return TankInfoResponse(
            success: false,
            message: data["message"].toString(),
          );
        }

        return TankInfoResponse(
          success: false,
          message: "Server error",
        );
      }

      return TankInfoResponse(
        success: false,
        message: e.toString(),
      );
    }
  }

  // ----------------------------------------------------------
  // Image Upload APIs
  // ----------------------------------------------------------

  // FETCH UPLOAD IMAGE TYPES
  Future<UploadImageTypeResponse> getUploadImageTypes() async {
    try {
      final response = await api.fetchUploadImageTypes();

      if (response.success) {
        return response;
      } else {
        return UploadImageTypeResponse(
          success: false,
          data: [],
        );
      }
    } catch (e) {
      return UploadImageTypeResponse(
        success: false,
        data: [],
      );
    }
  }

  Future<GetUploadedImagesResponse> getUploadedImages(int inspectionId) async {
    try {
      final response = await api.getUploadedImages(inspectionId);
      return response;
    } catch (e) {
      print("ERROR fetching uploaded images => $e");

      return GetUploadedImagesResponse(
        success: false,
        data: null,
        message: "Unable to load uploaded images",
      );
    }
  }


  Future<ApiResult> uploadImagesWithProgress({
    required int inspectionId,
    required FormData formData,
    required Function(int sent, int total) onProgress,
  }) async {
    try {
      print("Uploading => ${dio.options.baseUrl}/api/upload/batch/$inspectionId");
      final token = await secureStorage.getToken();
      if (token == null || token.isEmpty) {
        throw Exception("Token missing before uploadImagesWithProgress API call");
      }

      /*// undersideview must be exactly 2
      if ((photos[4]?.length ?? 0) != 2) {
        return ApiResult.error("You must upload exactly 2 underside images");
      }*/

      // Build multipart body
      /*photos.forEach((typeId, files) {
        for (int i = 0; i < files.length; i++) {
          String field = _mapTypeToField(typeId, i);
          fileMap[field] = MultipartFile.fromFileSync(
            files[i].path,
            filename: "$field.jpg",
          );
        }
      });

      final formData = FormData.fromMap(fileMap);*/

      final response = await dio.post(
        "/upload/batch/$inspectionId",
        data: formData,
        onSendProgress: onProgress,
        options: Options(
          contentType: "multipart/form-data",
          headers: {
            'Authorization': 'Bearer $token',
          },
        ),
      );

      return ApiResult.success(response.data);
    }
    on DioException catch (e) {
      print("Upload Error => ${e.response?.data}");
      return ApiResult.error("Server Error: ${e.response?.data}");
    }
    catch (e) {
      return ApiResult.error("Unexpected error: $e");
    }
  }

  // Map type ID to upload field name




  Future<ApiResult> updateImagesWithProgress({
    required int inspectionId,
    required FormData formData,
    required Function(int sent, int total) onProgress,
  }) async {
    try {
      print("Updating Images => ${dio.options.baseUrl}/api/upload/images/inspection/$inspectionId");
      final token = await secureStorage.getToken();
      if (token == null || token.isEmpty) {
        throw Exception("Token missing before updateImagesWithProgress API call");
      }

      /*final Map<String, dynamic> fileMap = {};

      // Build multipart body
      photos.forEach((typeId, files) {
        for (int i = 0; i < files.length; i++) {
          String field = _mapTypeToField(typeId, i);
          fileMap[field] = MultipartFile.fromFileSync(
            files[i].path,
            filename: "$field.jpg",
          );
        }
      });

      final formData = FormData.fromMap(fileMap);*/

      print("------ FORM DATA START ------");
      for (var element in formData.fields) {
        print("Field: ${element.key} = ${element.value}");
      }
      for (var file in formData.files) {
        print("File Field: ${file.key}");
        print("  File Name : ${file.value.filename}");
        print("  File Path : ${file.value}");
      }
      print("------ FORM DATA END ------");

      final response = await dio.put(
        "/upload/images/inspection/$inspectionId",
        data: formData,
        onSendProgress: onProgress,
        options: Options(
          contentType: "multipart/form-data",
          headers: {
            'Authorization': 'Bearer $token',
          },
        ),
      );

      return ApiResult.success(response.data);
    }
    on DioException catch (e) {
      print("Update Error => ${e.response?.data}");
      return ApiResult.error("Server Error: ${e.response?.data}");
    }
    catch (e) {
      return ApiResult.error("Unexpected error: $e");
    }
  }

  Future<ApiResult> deleteUploadedPhoto(
      int inspectionId,
      ) async {
    try {
      final token = await secureStorage.getToken();

      final response = await api.deletePhoto(
        "Bearer $token",
        inspectionId,
      );

      /// Directly convert to CheckListResponse

      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("Checklist Error Response: ${e.response}");

        // Backend validation error (FastAPI / Pydantic style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);
            print("Checklist Error Response11: ${error.detail.first.msg}");
            return ApiResult(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            // fallback if parsing fails
            return ApiResult(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response
        return ApiResult(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected error
      return ApiResult(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }


  //-------------------------------------------
  // CheckList Page API's
  //-------------------------------------------


  Future<CheckListResponse> submitChecklistBulk(
      CheckListRequest request,
      int inspectionId,
      ) async {
    try {
      final token = await secureStorage.getToken();

      print("FINAL JSON => ${jsonEncode(request.toJson())}");
      print("FINAL JSON => $token");
      print("FINAL JSON => $inspectionId");

      final response = await api.submitChecklistBulk(
        "Bearer $token",
        inspectionId,
        request.toJson(),
      );

      /// Directly convert to CheckListResponse

      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("Checklist Error Response: ${e.response}");

        // Backend validation error (FastAPI / Pydantic style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);

            return CheckListResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            // fallback if parsing fails
            return CheckListResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response
        return CheckListResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected error
      return CheckListResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }

  Future<CheckListResponse> updateChecklistBulk(
      CheckListRequest request,
      int inspectionId,
      ) async {
    try {
      final token = await secureStorage.getToken();

      print("FINAL JSON => ${jsonEncode(request.toJson())}");
      print("FINAL JSON => $token");
      print("FINAL JSON => $inspectionId");

      final response = await api.updateCheckList(
        "Bearer $token",
        inspectionId,
        request.toJson(),
      );

      /// Directly convert to CheckListResponse

      // If backend added has_flagged in the data payload (recommended),
      // it will be available in response.data. Log it if present:
      try {
        dynamic raw = response.data;

        // If raw is Map and has flagged info, log it for navigation decisions:
        if (raw is Map<String, dynamic>) {
          final hasFlagged = raw['has_flagged'] ?? raw['flagged_count'];
          if (hasFlagged != null) {
            print("Update returned has_flagged/flagged_count = $hasFlagged");
          }
        }
      } catch (e) {
        print("Couldn't read has_flagged from update response: $e");
      }

      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("Checklist Error Response: ${e.response}");

        // Backend validation error (FastAPI / Pydantic style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);

            return CheckListResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            // fallback if parsing fails
            return CheckListResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response
        return CheckListResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected error
      return CheckListResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }

  /// Update a single checklist item with minimal payload.
  /// Called by UI when user clicks to cycle item status.
  Future<CheckListResponse> updateChecklistItem(
      Map<String, dynamic> payload,
      int inspectionId,
      ) async {
    try {
      final token = await secureStorage.getToken();

      print("Updating checklist item => $payload");

      final response = await api.updateCheckList(
        "Bearer $token",
        inspectionId,
        payload,
      );

      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("Checklist item update error: ${e.response}");

        // Backend validation error (FastAPI / Pydantic style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);
            return CheckListResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            return CheckListResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response
        return CheckListResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected error
      print("Unexpected error updating checklist item: $e");
      return CheckListResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }

  Future<CheckListResponse> fetchChecklistDataUsingId(
      int inspectionId,
      ) async {
    try {

      final token = await secureStorage.getToken();

      final response = await api.getCheckListsById(
        "Bearer $token",
        inspectionId,
      );
      /// Directly convert to CheckListResponse

      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("Checklist Error Response: ${e.response}");

        // If backend returned an HTML error page (nginx 404 etc), return empty result
        if (_looksLikeHtml(data)) {
          print("Received HTML response from server for checklist endpoint. Returning empty result.");
          return CheckListResponse(
            success: false,
            message: "No checklist data (server returned HTML).",
            data: null,
          );
        }

        // Backend validation error (FastAPI / Pydantic style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);

            return CheckListResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            // fallback if parsing fails
            return CheckListResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response
        return CheckListResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected error
      return CheckListResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }



  // ----------------------------------------------------------
  // Todo Page API's
  //----------------------------------------------------------


  Future<CheckListResponse> fetchTodoDataUsingId(
      int inspectionId,
      ) async {
    try {
      final response = await api.getToDoData(
        inspectionId,
      );
      // If api.getToDoData returns a typed CheckListResponse already, just return it:
      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;
        print("Checklist Error Response: ${e.response}");

        // If backend returned an HTML error page (nginx 404 etc), return empty result instead of crashing
        if (_looksLikeHtml(data)) {
          print("Received HTML response from server for todo endpoint. Returning empty list.");
          return CheckListResponse(
            success: false,
            message: "No TODO data (server returned HTML).",
            data: null,
          );
        }

        // FastAPI / Pydantic validation error style
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);
            return CheckListResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            return CheckListResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response with JSON
        if (data is Map<String, dynamic> && data.containsKey("message")) {
          return CheckListResponse(
            success: false,
            message: data['message']?.toString() ?? "Request failed",
            data: null,
          );
        }

        // If the server returned JSON but fields might be strings for numeric values,
        // the model's fromJson should be robust. If not, you can pre-normalize here.
        return CheckListResponse(
          success: false,
          message: "Request failed",
          data: null,
        );
      }

      // Unexpected error
      print("Unexpected error fetching todo: $e");
      return CheckListResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }

  Future<CheckListResponse> updateTodoBulk(
      CheckListRequest request,
      int inspectionId,
      ) async {
    try {
      final token = await secureStorage.getToken();

      print("FINAL JSON => ${jsonEncode(request.toJson())}");
      print("FINAL JSON => $token");
      print("FINAL JSON => $inspectionId");

      final response = await api.updateTodoList(
        "Bearer $token",
        request.toJson(),
      );

      /// Directly convert to CheckListResponse

      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("Checklist Error Response: ${e.response}");

        // Backend validation error (FastAPI / Pydantic style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);

            return CheckListResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            // fallback if parsing fails
            return CheckListResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response
        return CheckListResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected error
      return CheckListResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }

  //----------------------------------------------------------
  // Review Page API's
  //----------------------------------------------------------

  Future<ValidationResponse> checkAllFormsAreSubmitted(
      int inspectionId,
      ) async {
    try {
      final response = await api.checkAllFormsValidated(inspectionId);
      /// Directly convert to CheckListResponse

      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;

        print("Checklist Error Response: ${e.response}");

        // Backend validation error (FastAPI / Pydantic style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);

            return ValidationResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            // fallback if parsing fails
            return ValidationResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend error response
        return ValidationResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected error
      return ValidationResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }


  Future<TankInspectionResponse> getTankReviewData(int id) async {
    try {
      final response = await api.getInspectionReview(id);
      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;
        // FastAPI / Pydantic validation errors
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          try {
            final error = ApiErrorResponse.fromJson(data);
            return TankInspectionResponse(
              success: false,
              message: error.detail.first.msg,
              data: null,
            );
          } catch (_) {
            return TankInspectionResponse(
              success: false,
              message: "Validation error",
              data: null,
            );
          }
        }

        // Normal backend message
        return TankInspectionResponse(
          success: false,
          message: data?['message'] ?? "Request failed",
          data: null,
        );
      }

      // Unexpected
      print("❌ Unexpected error fetching inspection: $e");
      return TankInspectionResponse(
        success: false,
        message: "Unexpected error",
        data: null,
      );
    }
  }

  Future<SubmitReviewResponse> postReviewData({
    required int? inspectionId,
  }) async {
    try {
      print("Payload => $inspectionId");

      // Retrofit API call
      final SubmitReviewResponse response =
      await api.submitReview(inspectionId ?? 0);

      print("API Response => ${response.toJson()}");

      return response;   // success or failure handled by UI

    } catch (e, stack) {
      print("RAW ERROR => $e");
      print("STACK => $stack");

      // ---------- HANDLE DIO ERRORS ----------
      if (e is DioException) {
        final data = e.response?.data;
        print("DIO ERROR RESPONSE => $data");

        // Backend validation (FastAPI-style)
        if (data is Map<String, dynamic> && data.containsKey("detail")) {
          final error = ApiErrorResponse.fromJson(data);
          return SubmitReviewResponse(
            success: false,
            message: error.detail.first.msg,
          );
        }

        // Simple backend error message
        if (data is Map<String, dynamic> && data.containsKey("message")) {
          return SubmitReviewResponse(
            success: false,
            message: data["message"].toString(),
          );
        }

        return SubmitReviewResponse(
          success: false,
          message: "Server error",
        );
      }

      // ---------- NON-DIO ERROR ----------
      return SubmitReviewResponse(
        success: false,
        message: e.toString(),
      );
    }
  }


  // ----------------------------------------------------------
  // Logout
  // ----------------------------------------------------------
  Future<void> logout() async {
    try {
      // Clear stored authentication data
      await secureStorage.clear();
      print("✅ User logged out successfully");
    } catch (e) {
      print("❌ Error during logout: $e");
      rethrow;
    }
  }


  // ----------------------------------------------------------
  Future<void> uploadTankImage({
    required String tankNumber,
    required String imageType,
    required File file,
  }) async {
    MultipartFile multiFile = await MultipartFile.fromFile(
      file.path,
      filename: "${imageType}_${DateTime.now().millisecondsSinceEpoch}.jpg",
    );

    try {
      final response = await api.uploadTankImage(
        tankNumber,
        imageType,
        multiFile,
      );

      if (response.response.statusCode == 200) {
        print("✅ Tank image uploaded successfully!");
      } else {
        print("❌ Upload failed: ${response.response.statusCode}");
      }
    } catch (e) {
      print("❌ Error uploading tank image: $e");
      rethrow;
    }
  }

  Future<ValidationResponse> checkAllFormsValidated(int inspectionId) async {
    try {
      final response = await api.checkAllFormsValidated(inspectionId);
      return response;
    } catch (e) {
      if (e is DioException) {
        final data = e.response?.data;
        return ValidationResponse(
          success: false,
          message: data?['message'] ?? "Validation failed",
          data: null,
        );
      }
      return ValidationResponse(
        success: false,
        message: "Validation error",
        data: null,
      );
    }
  }
}


