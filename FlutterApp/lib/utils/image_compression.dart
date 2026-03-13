// utils/image_compression.dart
import 'dart:io';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

class ImageCompression {
  /// Compress to target KB (approx). Returns compressed File or original on failure.

  /// [maxWidth] caps the longest side to reduce file size (e.g. 1280 for inspection photos).
  static Future<File?> compressToTarget(File file, {int targetKb = 300, int? maxWidth}) async {
    try {
      final dir = await getTemporaryDirectory();
      String targetPath = p.join(
        dir.path,
        'cmp_${DateTime.now().millisecondsSinceEpoch}.jpg',
      );

      int quality = 95;
      File? finalFile;

      while (quality >= 25) {
        final XFile? compressedXFile = maxWidth != null
            ? await FlutterImageCompress.compressAndGetFile(
                file.absolute.path,
                targetPath,
                quality: quality,
                format: CompressFormat.jpeg,
                minWidth: maxWidth,
                minHeight: maxWidth,
              )
            : await FlutterImageCompress.compressAndGetFile(
                file.absolute.path,
                targetPath,
                quality: quality,
                format: CompressFormat.jpeg,
              );

        if (compressedXFile == null) break;

        // Convert XFile → File
        File compressedFile = File(compressedXFile.path);

        double sizeKb = compressedFile.lengthSync() / 1024;

        if (sizeKb <= targetKb || quality <= 30) {
          finalFile = compressedFile;
          break;
        }

        // reduce quality and try again
        quality -= 10;
      }

      return finalFile ?? file;
    } catch (e) {
      print("Compression Error: $e");
      return file;
    }
  }
}
