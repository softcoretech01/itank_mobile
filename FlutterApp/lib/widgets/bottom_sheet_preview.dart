// widgets/bottom_sheet_preview.dart
import 'dart:io';
import 'package:flutter/material.dart';

import '../utils/constants.dart';

/*
Future<void> showImagePreviewBottomSheet(BuildContext context, File imageFile, String title) {
  final sheetHeight = MediaQuery.of(context).size.height * 0.75;
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) {
      return SizedBox(
        height: sheetHeight,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Image.file(imageFile, height: sheetHeight - 150, fit: BoxFit.contain),
              ),
            ],
          ),
        ),
      );
    },
  );
}
*/

Future<void> showImagePreviewBottomSheet(
    BuildContext context, {
      File? file,
      String? networkUrl,
      required String title,
    }) {
  final sheetHeight = MediaQuery.of(context).size.height * 0.60;

  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) {
      return SizedBox(
        width: double.infinity,
        height: sheetHeight,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title,
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),

              /// *** FIX: Use Expanded to avoid overflow ***
              Expanded(
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey.shade300),
                  ),
                  child: _buildPreviewImage(file, networkUrl),
                ),
              ),
            ],
          ),
        ),
      );
    },
  );
}

Widget _buildPreviewImage(File? file, String? networkUrl) {
  if (file != null) {
    return Image.file(
      file,
      width: double.infinity,
      fit: BoxFit.contain,
    );
  } else if (networkUrl != null) {
    return Image.network(
      "$IMAGE_BASE_URL$networkUrl",
      width: double.infinity,
      fit: BoxFit.contain,
      errorBuilder: (_, __, ___) =>
      const Center(child: Icon(Icons.broken_image, size: 60)),
      loadingBuilder: (_, child, progress) {
        if (progress == null) return child;
        return const Center(child: CircularProgressIndicator());
      },
    );
  }
  return const SizedBox.shrink();
}


