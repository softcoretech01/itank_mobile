// utils/image_compression.dart
import 'dart:io';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

class ImageCompression {
  /// Compress to target KB (approx). Returns compressed File or original on failure.

  static Future<File?> compressToTarget(File file, {int targetKb = 300}) async {
    try {
      final dir = await getTemporaryDirectory();
      String targetPath = p.join(
        dir.path,
        'cmp_${DateTime.now().millisecondsSinceEpoch}.jpg',
      );

      int quality = 95;
      File? finalFile;

      while (quality >= 25) {
        final XFile? compressedXFile = await FlutterImageCompress.compressAndGetFile(
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
