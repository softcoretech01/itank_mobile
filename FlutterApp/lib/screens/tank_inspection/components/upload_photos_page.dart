import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:iso_tank/models/get_uploaded_mages_response.dart';
import 'package:iso_tank/utils/constants.dart';
import 'package:shimmer/shimmer.dart';

import '../../../bloc/tank_inspection/tank_inspection_bloc.dart';
import '../../../models/upload_image_type_response.dart';
import '../../../repository/tank_repository.dart';
import '../../../widgets/bottom_sheet_preview.dart';
import '../../../utils/image_picker_helper.dart';

class UploadPhotosPage extends StatefulWidget {
  final Function(FormData, int) onPhotosSelected;
  final Function(Set<String>)? onDentViewsChanged;

  const UploadPhotosPage({
    super.key,
    required this.onPhotosSelected,
    this.onDentViewsChanged,
  });

  @override
  State<UploadPhotosPage> createState() => UploadPhotosPageState();
}

class UploadPhotosPageState extends State<UploadPhotosPage> {
  TankRepository? repo;

  List<UploadImageType> types = [];
  Map<int, List<File>> photos = {};
  Map<int, List<UploadedImage>> networkPhotos = {};
  // already uploaded images

  bool isLoading = true;
  bool loaded = false;
  bool isUndersideImageOne = false;
  final Set<String> _dentMarkedViews = {};

  @override
  void initState() {
    super.initState();
    context.read<TankInspectionBloc>().add(GetImageTypesEvent());
    
    // Reset parent state to 0 photos initially to prevent stale state issues
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        widget.onPhotosSelected(FormData(), 0);
      }
    });
  }
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
  }


  /// Use a lower target size (150 KB) for inspection photos to speed up upload of many images.
  static const int _inspectionPhotoTargetKb = 150;

  Future<void> pickPhoto(UploadImageType type) async {
    if (photos[type.imageTypeId]!.length >= type.count) return;

    final File? file = await ImagePickerHelper.pickFromCamera(
      context,
      targetKb: _inspectionPhotoTargetKb,
      maxWidth: 1280,
    );
    if (file != null) {
      setState(() {
        photos[type.imageTypeId]!.add(file);
      });
    }
    final formData = buildFormData();
    
    // Calculate total selected photos count
    int count = 0;
    photos.forEach((k, v) => count += v.length);
    
    widget.onPhotosSelected(formData, count);
  }

  FormData buildFormData() {
    final Map<String, dynamic> fileMap = {};

    photos.forEach((typeId, localFiles) {
      final net = networkPhotos[typeId] ?? [];

      int networkCount = net.length; // existing network photos offset

      for (int i = 0; i < localFiles.length; i++) {
        final actualIndex = networkCount + i;
        final field = _mapTypeToField(typeId, actualIndex);

        final filePath = localFiles[i].path;

        if (filePath.isEmpty) {
          // 🔹 Add null when file path is empty/missing
          fileMap[field] = null;
        } else {
          // 🔹 Add actual file
          fileMap[field] = MultipartFile.fromFileSync(
            filePath,
            filename: "$field.jpg",
          );
        }
      }
    });

    return FormData.fromMap(fileMap);
  }


  String _mapTypeToField(int typeId, int index) {
    const map = {
      1: "frontview",
      2: "rearview",
      3: "topview",
      4: "undersideview",
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
    if (base == null) {
      throw Exception("Unknown typeId $typeId");
    }

    // undersideview → must be padded with 2 digits
    if (typeId == 4) {
      final padded = (index + 1).toString().padLeft(2, '0');
      return "$base$padded"; // e.g. undersideview01, undersideview02
    }

    // all other image types → single name only
    return base;
  }


  @override
  Widget build(BuildContext context) {
    return BlocBuilder<TankInspectionBloc, TankInspectionState>(
        builder: (context, state) {
          if (state.status == FlowStatus.loading) {
            return Scaffold(
              body: Center(
                child: Shimmer.fromColors(
                  baseColor: Colors.grey[300]!,
                  highlightColor: Colors.grey[100]!,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    mainAxisSize: MainAxisSize.max,
                    children: List.generate(18, (index) =>
                        Container(
                          width: 280,
                          margin: const EdgeInsets.symmetric(vertical: 8),
                          color: Colors.white,
                        )),
                  ),
                ),
              ),
            );
          }

          if (types.isEmpty) {
            types = state.uploadPhotos.uploadImageTypeResponse?.data ?? [];

            // Initialize only once
            if (!loaded && types.isNotEmpty) {
              photos = { for (var t in types) t.imageTypeId : [] };
              loaded = true;
            }
          }

          if (state.uploadPhotos.uploadedNetworkPhotos != null) {
            networkPhotos = groupImagesByType(state.uploadPhotos.uploadedNetworkPhotos!.data!);
          }

          return Container(
            margin: EdgeInsets.only(bottom: 100),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: types.length,
              itemBuilder: (_, index) {
                final t = types[index];
                final netImgs = networkPhotos[t.imageTypeId] ?? [];
                final locImgs = photos[t.imageTypeId] ?? [];

                return PhotoTile(
                  label: t.imageType,
                  imageTypeId: t.imageTypeId,
                  networkImages: netImgs,
                  localImages: locImgs,
                  maxCount: t.count,
                  dentMarkedViews: _dentMarkedViews,
                  onToggleDent: _onToggleDent,
                  onAddPhoto: () => pickPhoto(t),
                  onRemoveLocalPhoto: (i) => removeLocalPhoto(t, i),
                  onRemoveNetworkPhoto: (imageId) {
                    print("Removing network photo with ID: $imageId");
                    deleteNetworkPhoto(imageId, t.imageTypeId);
                  },
                  onPreview: (url, file) => showPreview(context, url, file),
                );

              },
            ),
          );
        });
  }
  void removeLocalPhoto(UploadImageType type, int index) {
    setState(() {
      photos[type.imageTypeId]!.removeAt(index);
    });
  }

  void showPreview(BuildContext context, String? url, File? file) {
    showImagePreviewBottomSheet(
      context,
      title: "Preview",
      file: file,
      networkUrl: url,
    );
  }

  deleteNetworkPhoto(int imageTypeId, int i) {
    print("Deleting network photo with ID: $imageTypeId");
    context.read<TankInspectionBloc>().add(DeleteUploadedPhotoEvent(imageId: imageTypeId
    ));
  }

  bool _isDentMarkSupportedType(int imageTypeId) {
    return imageTypeId == 1 || imageTypeId == 2;
  }

  String _viewNameForImageType(int imageTypeId) {
    if (imageTypeId == 1) return "Front view";
    if (imageTypeId == 2) return "Rear view";
    return "";
  }

  void _onToggleDent(int imageTypeId) {
    if (!_isDentMarkSupportedType(imageTypeId)) return;
    final viewName = _viewNameForImageType(imageTypeId);
    if (viewName.isEmpty) return;

    setState(() {
      if (_dentMarkedViews.contains(viewName)) {
        _dentMarkedViews.remove(viewName);
      } else {
        _dentMarkedViews.add(viewName);
      }
    });
    widget.onDentViewsChanged?.call(Set<String>.from(_dentMarkedViews));
  }

}
Map<int, List<UploadedImage>> groupImagesByType(UploadedImagesData data) {
  final Map<int, List<UploadedImage>> result = {};

  for (var img in data.images) {
    result.putIfAbsent(img.imageTypeId, () => []);
    result[img.imageTypeId]!.add(img);   // store full object
  }

  return result;
}



// --------------------------------------------------
//                  PHOTO TILE WIDGET
// --------------------------------------------------

class PhotoTile extends StatelessWidget {
  final String label;
  final int imageTypeId;
  final List<UploadedImage> networkImages;
  final List<File> localImages;
  final int maxCount;
  final Set<String> dentMarkedViews;
  final Function(int) onToggleDent;

  final VoidCallback onAddPhoto;
  final Function(int) onRemoveLocalPhoto;
  final Function(int) onRemoveNetworkPhoto;   // ADD THIS
  final Function(String?, File?) onPreview;

  const PhotoTile({
    super.key,
    required this.label,
    required this.imageTypeId,
    required this.networkImages,
    required this.localImages,
    required this.maxCount,
    required this.dentMarkedViews,
    required this.onToggleDent,
    required this.onAddPhoto,
    required this.onRemoveLocalPhoto,
    required this.onRemoveNetworkPhoto,
    required this.onPreview,
  });

  @override
  Widget build(BuildContext context) {
    final totalCount = networkImages.length + localImages.length;
    final showAddButton = totalCount < maxCount;
    final isDentType = imageTypeId == 1 || imageTypeId == 2;
    final dentViewName = imageTypeId == 1 ? "Front view" : "Rear view";
    final isDentMarked = isDentType && dentMarkedViews.contains(dentViewName);

    final List<_TileItem> items = [
      ...networkImages.map((e) => _TileItem(url: e.imagePath, uploadedImage: e)),
      ...localImages.map((e) => _TileItem(file: e)),
    ];
    
    for (var element in items) {
      print("Item: url=${element.url}, file=${element.file}, imageId=${element.uploadedImage?.id}");
      print("Item: uploadedImage=${element.uploadedImage?.imageId} ${element.uploadedImage?.id}");
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 20),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            if (isDentType)
              TextButton.icon(
                onPressed: totalCount == 0 ? null : () => onToggleDent(imageTypeId),
                icon: Icon(
                  Icons.circle,
                  size: 12,
                  color: isDentMarked ? Colors.red : Colors.grey,
                ),
                label: Text(isDentMarked ? "Dent marked" : "Mark as dent"),
              ),
            const SizedBox(height: 10),

            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: items.length + (showAddButton ? 1 : 0),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2, // for better structure
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemBuilder: (_, index) {
                if (index < items.length) {
                  final item = items[index];
                  return GestureDetector(
                    onTap: () => onPreview(item.url, item.file),
                    child: Stack(
                      children: [
                        Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(12),
                            image: DecorationImage(
                              image: item.file != null
                                  ? FileImage(item.file!)
                                  : NetworkImage("$IMAGE_BASE_URL${item.url}") as ImageProvider,
                              fit: BoxFit.cover,
                            ),
                          ),
                        ),

                        if (item.file != null)
                          Positioned(
                            right: -10,
                            top: -10,
                            child: IconButton(
                              icon: const Icon(Icons.cancel, color: Colors.red),
                              onPressed: () =>
                                  onRemoveLocalPhoto(localImages.indexOf(item.file!)),
                            ),
                          ),
                        if(item.url != null)
                          Positioned(
                            right: -10,
                            top: -10,
                            child: IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () {
                                showDialog(
                                  context: context,
                                  builder: (ctx) {
                                    return AlertDialog(
                                      title: const Text("Delete Photo?"),
                                      content: const Text("Are you sure you want to delete this photo?"),
                                      actions: [
                                        TextButton(
                                          onPressed: () => Navigator.pop(ctx), // Close popup
                                          child: const Text("No"),
                                        ),
                                        TextButton(
                                          onPressed: () {
                                            Navigator.pop(ctx); // Close popup first
                                            onRemoveNetworkPhoto(item.uploadedImage!.id); // Trigger delete
                                          },
                                          child: const Text(
                                            "Yes",
                                            style: TextStyle(color: Colors.red),
                                          ),
                                        ),
                                      ],
                                    );
                                  },
                                );
                              },
                            ),
                          )
                      ],
                    ),
                  );
                }

                return GestureDetector(
                  onTap: onAddPhoto,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.add, size: 32),
                  ),
                );
              },
            )
          ],
        ),
      ),
    );
  }
}

class _TileItem {
  final String? url;
  final File? file;
  final UploadedImage? uploadedImage; // ADD THIS
  _TileItem({this.url, this.file, this.uploadedImage});
}




