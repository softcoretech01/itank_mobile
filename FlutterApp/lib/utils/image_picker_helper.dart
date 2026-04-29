// utils/image_picker_helper.dart
import 'dart:io';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import 'image_compression.dart';
import 'permission_utils.dart';

class ImagePickerHelper {
  static final ImagePicker _picker = ImagePicker();

  /// Pick from camera → only request camera permission.
  /// [targetKb] and [maxWidth] reduce file size for faster uploads.
  static Future<File?> pickFromCamera(
    BuildContext context, {
    int targetKb = 300,
    int? maxWidth,
  }) async {
    final granted = await PermissionUtils.requestCamera(context);
    if (!granted) return null;

    final XFile? xfile = await Navigator.of(context).push<XFile>(
      MaterialPageRoute(builder: (_) => const _CameraCapturePage()),
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
  static Future<File?> pickFromGallery(
    BuildContext context, {
    int targetKb = 300,
  }) async {
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

class _CameraCapturePage extends StatefulWidget {
  const _CameraCapturePage();

  @override
  State<_CameraCapturePage> createState() => _CameraCapturePageState();
}

class _CameraCapturePageState extends State<_CameraCapturePage> {
  CameraController? _controller;
  Future<void>? _initializeFuture;
  bool _capturing = false;

  @override
  void initState() {
    super.initState();
    _initializeFuture = _setupCamera();
  }

  Future<void> _setupCamera() async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) {
      throw Exception('No camera available');
    }

    final selectedCamera = cameras.firstWhere(
      (camera) => camera.lensDirection == CameraLensDirection.back,
      orElse: () => cameras.first,
    );

    final controller = CameraController(
      selectedCamera,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    await controller.initialize();
    await controller.lockCaptureOrientation(DeviceOrientation.portraitUp);

    if (!mounted) {
      await controller.dispose();
      return;
    }

    setState(() {
      _controller = controller;
    });
  }

  Future<void> _capture() async {
    if (_capturing || _controller == null) return;

    setState(() {
      _capturing = true;
    });

    try {
      await _controller!.setFlashMode(FlashMode.off);
      final file = await _controller!.takePicture();
      if (!mounted) return;
      Navigator.of(context).pop(file);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Unable to capture image')));
    } finally {
      if (mounted) {
        setState(() {
          _capturing = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _controller?.unlockCaptureOrientation();
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text('Capture Photo'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
      ),
      body: FutureBuilder<void>(
        future: _initializeFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError || _controller == null) {
            return const Center(
              child: Text(
                'Camera not available',
                style: TextStyle(color: Colors.white),
              ),
            );
          }

          return SafeArea(
            child: Column(
              children: [
                Expanded(
                  child: Center(
                    child: _PortraitCameraViewport(controller: _controller!),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(bottom: 28),
                  child: IconButton(
                    onPressed: _capturing ? null : _capture,
                    iconSize: 72,
                    color: Colors.white,
                    icon: Icon(
                      _capturing ? Icons.hourglass_top : Icons.camera_alt,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _CameraGridOverlay extends StatelessWidget {
  const _CameraGridOverlay();

  @override
  Widget build(BuildContext context) {
    return CustomPaint(painter: _GridPainter());
  }
}

class _PortraitCameraViewport extends StatelessWidget {
  const _PortraitCameraViewport({required this.controller});

  final CameraController controller;

  @override
  Widget build(BuildContext context) {
    final previewSize = controller.value.previewSize;

    return AspectRatio(
      aspectRatio: 9 / 16,
      child: ClipRect(
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (previewSize == null)
              CameraPreview(controller)
            else
              FittedBox(
                fit: BoxFit.cover,
                child: SizedBox(
                  // previewSize is usually landscape; swap for portrait rendering.
                  width: previewSize.height,
                  height: previewSize.width,
                  child: CameraPreview(controller),
                ),
              ),
            const IgnorePointer(child: _CameraGridOverlay()),
          ],
        ),
      ),
    );
  }
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.35)
      ..strokeWidth = 1;

    final thirdWidth = size.width / 3;
    final thirdHeight = size.height / 3;

    canvas.drawLine(
      Offset(thirdWidth, 0),
      Offset(thirdWidth, size.height),
      paint,
    );
    canvas.drawLine(
      Offset(thirdWidth * 2, 0),
      Offset(thirdWidth * 2, size.height),
      paint,
    );
    canvas.drawLine(
      Offset(0, thirdHeight),
      Offset(size.width, thirdHeight),
      paint,
    );
    canvas.drawLine(
      Offset(0, thirdHeight * 2),
      Offset(size.width, thirdHeight * 2),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
