import 'dart:io';
import 'package:dio/dio.dart';
import '../models/api_result.dart';
import '../service/secure_storage_service.dart';

class UploadImagesService {
  final Dio dio;

  UploadImagesService(String baseUrl)
      : dio = Dio(BaseOptions(baseUrl: baseUrl));

  Future<ApiResult> uploadImagesWithProgress({
    required int inspectionId,
    required Map<int, List<File>> photos,
    required Function(int sent, int total) onProgress,
  }) async {
    try {
      print("🔍 Upload to => ${dio.options.baseUrl}/api/upload/batch/$inspectionId");

      final fileMap = <String, dynamic>{};

      // undersideview → must be exactly 2 photos
      if ((photos[4]?.length ?? 0) != 2) {
        return ApiResult.error("You must upload exactly 2 underside images");
      }

      // Add files to multipart map
      photos.forEach((typeId, files) {
        for (int i = 0; i < files.length; i++) {
          final field = _mapTypeToField(typeId, i);

          fileMap[field] = MultipartFile.fromFileSync(
            files[i].path,
            filename: "$field.jpg",
          );
        }
      });

      final formData = FormData.fromMap(fileMap);

      final token = await secureStorage.getToken();
      final response = await dio.post(
        "upload/batch/$inspectionId",
        data: formData,
        onSendProgress: onProgress,
        options: Options(
          contentType: "multipart/form-data",
          headers: {
            if (token != null && token.isNotEmpty)
              'Authorization': 'Bearer $token',
          },
        ),
      );

      return ApiResult.success(response.data);
    }
    on DioException catch (e) {
      print("❌ Upload Error: ${e.response?.data}");
      return ApiResult.error("Server error: ${e.response?.data}");
    }
    catch (e) {
      return ApiResult.error("Unexpected error: $e");
    }
  }

  // ---------------------------------------------------------
  // Map typeId → field string
  // ---------------------------------------------------------
  String _mapTypeToField(int typeId, int index) {
    const map = {
      1: "frontview",
      2: "rearview",
      3: "topview",
      4: "undersideview", // multi images → add padded index
      5: "frontlhview",
      6: "rearlhview",
      7: "frontrhview",
      8: "rearrhview",
      9: "lhsideview",
      10: "rhsideview",
      11: "valvessectionview",
      12: "safetyvalve",
      13: "levelpressuregauge",
      14: "vacuumreading",
    };

    final base = map[typeId];

    if (base == null) throw Exception("Unknown typeId: $typeId");

    // 🔥 FIX: Backend expects undersideview01, undersideview02
    if (typeId == 4) {
      final padded = (index + 1).toString().padLeft(2, '0');
      return "$base$padded"; // undersideview01, undersideview02
    }

    return base;
  }

}

