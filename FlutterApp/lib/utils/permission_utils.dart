// utils/permissions.dart

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';



class PermissionUtils {
  /// Request camera permission
  static Future<bool> requestCamera(BuildContext context) async {
    final status = await Permission.camera.status;
    print("Camera permission status: $status");

    if (status.isPermanentlyDenied) {
      await _showPermissionDialog(
        context,
        title: "Camera Permission Required",
        message:
        "Camera permission is required to take photos. Please enable it in app settings.",
      );
      return false;
    }

    if (status.isGranted) return true;

    // Request camera permission normally
    final result = await Permission.camera.request();
    return result.isGranted;
  }

  /// Request storage/photos permission
  static Future<bool> requestStorageOnly(BuildContext context) async {
    final status = await Permission.photos.status;
    print("Photo permission status: $status");

    if (status.isPermanentlyDenied) {
      await _showPermissionDialog(
        context,
        title: "Storage Permission Required",
        message:
        "Storage/Photos permission is required to pick images. Please enable it in app settings.",
      );
      return false;
    }

    if (status.isGranted || status.isLimited) return true;

    // Request permission normally
    final result = await Permission.photos.request();
    return result.isGranted || result.isLimited;
  }

  /// Shows popup with settings redirection
  static Future<void> _showPermissionDialog(
      BuildContext context, {
        required String title,
        required String message,
      }) async {
    await showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: Text(title),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text("Cancel"),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                openAppSettings();
              },
              child: const Text("Open Settings"),
            ),
          ],
        );
      },
    );
  }
}






