// utils/image_picker_helper.dart
import 'dart:io';
import 'package:flutter/cupertino.dart';
import 'package:image_picker/image_picker.dart';
import 'permission_utils.dart';
import 'image_compression.dart';


class ImagePickerHelper {
  static final ImagePicker _picker = ImagePicker();

  /// Pick from camera → only request camera permission.
  /// [targetKb] and [maxWidth] reduce file size for faster uploads.
  static Future<File?> pickFromCamera(BuildContext context, {int targetKb = 300, int? maxWidth}) async {
    final granted = await PermissionUtils.requestCamera(context);
    if (!granted) return null;

    final XFile? xfile = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 100,
    );
    if (xfile == null) return null;

    final file = File(xfile.path);
    final compressed = await ImageCompression.compressToTarget(
      file,
      targetKb: targetKb,
      maxWidth: maxWidth,
    );
    return compressed;
  }

  /// Pick from gallery → request storage permission
  static Future<File?> pickFromGallery(BuildContext context,{int targetKb = 300}) async {
    /*print("pickLifterPhoto4");
    final granted = await PermissionUtils.requestStorageOnly(context);
    if (!granted) return null;*/

    final XFile? xfile = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 100,
    );
    if (xfile == null) return null;

    final file = File(xfile.path);
    final compressed = await ImageCompression.compressToTarget(
      file,
      targetKb: targetKb,
    );
    return compressed;
  }
}

