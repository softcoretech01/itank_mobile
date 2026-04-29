import 'dart:io';
import 'package:flutter/material.dart';
import 'package:collection/collection.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:iso_tank/models/tank_details_response.dart';
import 'package:shimmer/shimmer.dart';
import 'package:path/path.dart' as p;
import 'package:iso_tank/models/tank_master_data.dart';
import '../../../bloc/tank_inspection/tank_inspection_bloc.dart';
import '../../../models/request/tank_info_data.dart';
import '../../../models/tank_model.dart';
import '../../../repository/tank_repository.dart';
import '../../../service/ApiClient.dart';
import '../../../utils/image_picker_helper.dart';
import '../../../utils/tank_search.dart';
import '../../../widgets/bottom_sheet_preview.dart';
import 'tank_details_card.dart';

class TankInfoPage extends StatefulWidget {
  const TankInfoPage({super.key});

  @override
  State<TankInfoPage> createState() => TankInfoPageState();
}

class TankInfoPageState extends State<TankInfoPage> {
  // Controllers
  final TextEditingController dateController = TextEditingController(
    text: _formatToday(),
  );

  final TextEditingController reportNumberController = TextEditingController();
  final TextEditingController lifterWeightController = TextEditingController();
  final TextEditingController notesController = TextEditingController();
  final TextEditingController vacuumReadingController = TextEditingController();
  final TextEditingController lifterWeightValueController =
      TextEditingController();
  String selectedVacuumUom = "Micron";

  // Dropdowns
  TankStatus? statusMaster;
  InspectionType? inspectionMaster;
  Product? productMaster;
  Location? locationMaster;
  SafetyValve? safetyValveMaster;
  String? ownership, lifterWeightImageURL;
  File? vacuumPhoto;
  File? lifterPhoto;
  late ApiClient apiClient;
  TankRepository? repo;
  TankMasterData? posts;
  TankDetailsResponse? tankDetailsResponse;
  TankDetailsResponse? currentInspection;
  bool isLoading = true;
  ActiveTank? selectedTank;
  List<ActiveTank> allTanks = [];
  List<ActiveTank> filteredTanks = [];
  bool isPrefilled = false;

  static String _formatToday() {
    final now = DateTime.now();
    return "${now.day}-${now.month}-${now.year}";
  }

  Future<void> pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );

    if (picked != null) {
      setState(() {
        dateController.text = "${picked.day}-${picked.month}-${picked.year}";
      });
    }
  }

  Future<void> pickLifterPhoto() async {
    print("pickLifterPhoto");
    final File? file = await ImagePickerHelper.pickFromCamera(context);

    if (file != null) {
      setState(() {
        print("pickLifterPhoto6 $file");
        lifterPhoto = file;
        lifterWeightController.text = p.basename(file.path);
      });
    }
  }

  void previewImage({File? file, String? networkUrl, required String title}) {
    showImagePreviewBottomSheet(
      context,
      file: file,
      networkUrl: networkUrl,
      title: title,
    );
  }

  TankInfoData getFormData() {
    return TankInfoData(
      date: dateController.text,
      tankId: "${selectedTank?.tankId}",
      reportNumber: reportNumberController.text,
      tankStatus: "${statusMaster?.statusId}",
      inspectionType: "${inspectionMaster?.inspectionTypeId}",
      lifterWeight: lifterWeightController.text,
      lifterPhoto: lifterPhoto,
      location: "${locationMaster?.locationId}",
      inspectionId:
          currentInspection?.data?.inspectionId ??
          context.read<TankInspectionBloc>().state.inspectionId,
      vacuumReading: vacuumReadingController.text,
      vacuumReadingUom: selectedVacuumUom,
      lifterWeightValue: lifterWeightValueController.text,
    );
  }

  @override
  void initState() {
    super.initState();
    context.read<TankInspectionBloc>().add(InitializeFlowEvent());
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<TankInspectionBloc, TankInspectionState>(
      listener: (context, state) {
        if (state.masterDataState.flowStatus == FlowStatus.ready) {
          // Tank master data, tank list, selected tank from BLoC
          posts = state.masterDataState.masterData?.data;
          allTanks = state.masterDataState.activeTanks?.data?.activeTanks ?? [];
        }
        if (state.status == FlowStatus.ready) {
          // 1️⃣ Always update master tank details from /tank-details
          final masterDetails = state.tankInfo.selectedTank;
          final inspectionDetails = state.tankInfo.inspectionDetails;

          tankDetailsResponse = masterDetails;
          currentInspection = inspectionDetails;

          // 2️⃣ Prefill form ONLY from inspection data when we are in update mode
          //    Otherwise, ensure a clean form so previous tank's inspection data
          //    never leaks into the new selection.
          if (state.isUpdate == true && inspectionDetails?.data != null) {
            fillInspectionForm(inspectionDetails!.data!);
          } else {
            resetInspectionFormForNewTank();
          }

          // 3️⃣ Assign selected tank in dropdown using tank_id from master (fallback to inspection)
          final selectedTankId =
              masterDetails?.data?.tankId ?? inspectionDetails?.data?.tankId;

          if (selectedTankId != null) {
            selectedTank = allTanks.firstWhere(
              (t) => t.tankId == selectedTankId,
              orElse: () => ActiveTank(
                tankId:
                    masterDetails?.data?.tankId ??
                    inspectionDetails?.data?.tankId,
                tankNumber:
                    masterDetails?.data?.tankNumber ??
                    inspectionDetails?.data?.tankNumber,
              ),
            );

            setState(() {});
          }
        }
      },
      builder: (context, state) {
        if (state.tankInfo.flowStatus == FlowStatus.loading) {
          return Scaffold(
            body: Center(
              child: Shimmer.fromColors(
                baseColor: Colors.grey[300]!,
                highlightColor: Colors.grey[100]!,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.start,
                  mainAxisSize: MainAxisSize.max,
                  children: List.generate(
                    18,
                    (index) => Container(
                      width: 280,
                      margin: const EdgeInsets.symmetric(vertical: 8),
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            ),
          );
        }

        return Scaffold(
          body: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 600),
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 120),
                child: Column(
                  spacing: 16,
                  children: [
                    GestureDetector(
                      onTap: () => openTankBottomSheet(context),
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 16),
                        child: InputDecorator(
                          decoration: InputDecoration(
                            labelText: selectedTank == null
                                ? ""
                                : "Select Tank",
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(6),
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                              vertical: 16,
                              horizontal: 10,
                            ),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                selectedTank?.tankNumber ?? "Select Tank",
                                // <-- SHOW hint text
                                style: TextStyle(
                                  fontSize: 16,
                                  color: selectedTank == null
                                      ? Colors.black
                                      : Colors.black,
                                ),
                              ),
                              const Icon(Icons.arrow_drop_down),
                            ],
                          ),
                        ),
                      ),
                    ),

                    if (selectedTank != null &&
                        tankDetailsResponse?.data != null) ...[
                      TankDetailsCard(
                        tankData: selectedTank!,
                        tankDetailsResponse: tankDetailsResponse?.data,
                      ),
                      SizedBox(height: 5),
                    ],
                    // fieldDate("Date", dateController),
                    if (posts != null &&
                        posts?.tankStatuses?.isNotEmpty == true) ...[
                      dropdownModel<TankStatus>(
                        title: "Tank Status",
                        value: statusMaster,
                        items: posts?.tankStatuses ?? [],
                        label: (e) => e.statusName ?? "",
                        onChange: (v) {
                          setState(() {
                            statusMaster = v;
                          });
                        },
                      ),
                    ],
                    if (posts != null) ...[
                      dropdownModel<InspectionType>(
                        title: "Inspection Type",
                        value: inspectionMaster,
                        items: posts?.inspectionTypes ?? [],
                        label: (e) => e.inspectionTypeName ?? "",
                        onChange: (v) => setState(() => inspectionMaster = v),
                      ),
                    ],

                    if (posts != null) ...[
                      dropdownModel<Location>(
                        title: "Location",
                        value: locationMaster,
                        items: posts!.locations ?? [],
                        label: (e) => e.locationName ?? "",
                        onChange: (v) => setState(() => locationMaster = v),
                      ),
                    ],

                    // Extra free-text fields
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: fieldText("Vacuum Reading", vacuumReadingController),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _uomDropdown(),
                        ),
                      ],
                    ),
                    fieldText("Lifter Weight", lifterWeightValueController),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  /// Clear all inspection-specific fields when a new tank is selected
  /// that does NOT have any existing draft inspection.
  void resetInspectionFormForNewTank() {
    setState(() {
      // Reset basic fields
      dateController.text = _formatToday();
      reportNumberController.clear();
      notesController.clear();
      vacuumReadingController.clear();
      lifterWeightValueController.clear();

      // Clear lifter weight image/file
      lifterPhoto = null;
      lifterWeightImageURL = null;
      lifterWeightController.clear();

      // Clear dropdown selections (user must choose fresh values)
      statusMaster = null;
      inspectionMaster = null;
      locationMaster = null;
      selectedVacuumUom = "Micron";
    });
  }

  // ---------------- UI Helpers -------------------

  Widget fieldText(String title, TextEditingController controller) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 15),
      child: TextFormField(
        controller: controller,
        decoration: InputDecoration(
          labelText: title,
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }

  Widget _uomDropdown() {
    return Container(
      margin: const EdgeInsets.only(right: 15),
      child: DropdownButtonFormField<String>(
        initialValue: selectedVacuumUom,
        decoration: const InputDecoration(
          labelText: "UOM",
          border: OutlineInputBorder(),
        ),
        items: const [
          DropdownMenuItem(value: "Micron", child: Text("Micron")),
          DropdownMenuItem(value: "TORR", child: Text("TORR")),
        ],
        onChanged: (value) {
          if (value == null) return;
          setState(() => selectedVacuumUom = value);
        },
      ),
    );
  }

  Widget fieldDate(String title, TextEditingController controller) {
    return Container(
      width: double.infinity,
      margin: EdgeInsets.only(left: 20, right: 20),
      child: TextFormField(
        controller: controller,
        readOnly: true,
        enabled: false,
        decoration: InputDecoration(
          labelText: title,
          border: const OutlineInputBorder(),
          suffixIcon: IconButton(
            icon: const Icon(Icons.calendar_month),
            onPressed: pickDate,
          ),
        ),
      ),
    );
  }

  Widget dropDownForTankStatus(
    String title,
    TankStatus? value,
    List<TankStatus>? items,
    ValueChanged<TankStatus?> onChange,
  ) {
    print("items ====> $items");
    return Container(
      width: double.infinity,
      margin: EdgeInsets.only(left: 20, right: 20),
      child: DropdownButtonFormField<TankStatus>(
        initialValue: value,
        items: items
            ?.map(
              (e) => DropdownMenuItem<TankStatus>(
                value: e,
                child: Text(e.statusName ?? ""),
              ),
            )
            .toList(),
        decoration: const InputDecoration(
          border: OutlineInputBorder(),
          labelText: "",
        ),
        hint: Text(title),
        onChanged: onChange,
      ),
    );
  }

  // ---------------------------- IMAGE FIELD BOX (OLD DESIGN) ----------------------------

  Widget imageFieldBox({
    required String label,
    required TextEditingController controller,
    required File? photo,
    required String? networkUrl, // NEW
    required VoidCallback onPick,
    required VoidCallback onPreview,
  }) {
    return Container(
      width: double.infinity,
      margin: EdgeInsets.only(left: 18, right: 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 2),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: Colors.grey),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(label, style: const TextStyle(fontSize: 15)),
                IconButton(
                  icon: const Icon(Icons.camera_alt),
                  onPressed: onPick,
                ),
              ],
            ),
          ),

          if (photo != null || networkUrl != null) ...[
            const SizedBox(height: 6),
            GestureDetector(
              onTap: onPreview,
              child: const Text(
                "Preview",
                style: TextStyle(fontSize: 14, color: Colors.blue),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget dropdownModel<T>({
    required String title,
    required T? value,
    required List<T> items,
    required String Function(T) label,
    required Function(T?) onChange,
  }) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 15),
      child: DropdownButtonFormField<T>(
        initialValue: value,
        items: items
            .map((e) => DropdownMenuItem<T>(value: e, child: Text(label(e))))
            .toList(),
        decoration: InputDecoration(
          border: const OutlineInputBorder(),
          labelText: title, // ✅ THIS FIXES LABEL ISSUE
        ),
        onChanged: onChange,
      ),
    );
  }

  void openTankBottomSheet(BuildContext context) {
    TextEditingController searchCtrl = TextEditingController();
    List<ActiveTank> tempList = List.from(allTanks);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(28),
          topRight: Radius.circular(28),
        ),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return SizedBox(
              height: MediaQuery.of(context).size.height * 0.75,
              child: Column(
                children: [
                  const SizedBox(height: 10),

                  /// DRAG INDICATOR
                  Container(
                    height: 5,
                    width: 50,
                    decoration: BoxDecoration(
                      color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),

                  const SizedBox(height: 20),

                  /// SEARCH FIELD
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: TextField(
                      controller: searchCtrl,
                      onChanged: (value) {
                        setSheetState(() {
                          final query = normalizeTankSearch(value);
                          if (query.isEmpty) {
                            tempList = List.from(allTanks);
                            return;
                          }

                          tempList = allTanks
                              .where((tank) => tankMatchesSearch(tank, query))
                              .toList();
                        });
                      },
                      decoration: InputDecoration(
                        prefixIcon: const Icon(Icons.search),
                        hintText: "Search Tank",
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  /// LIST OF TANKS (API)
                  Expanded(
                    child: tempList.isEmpty
                        ? const Center(
                            child: Text(
                              "No tanks found",
                              style: TextStyle(color: Colors.grey),
                            ),
                          )
                        : ListView.builder(
                            itemCount: tempList.length,
                            itemBuilder: (context, index) {
                              final tank = tempList[index];

                              return ListTile(
                                title: Text(tank.tankNumber ?? ""),
                                trailing: selectedTank?.tankId == tank.tankId
                                    ? const Icon(
                                        Icons.check_circle,
                                        color: Colors.blue,
                                      )
                                    : null,
                                onTap: () async {
                                  Navigator.pop(context);
                                  setState(() {
                                    selectedTank = tank;
                                    isPrefilled = false;

                                    // Clear inspection-specific fields before loading the new tank.
                                    statusMaster = null;
                                    inspectionMaster = null;
                                    safetyValveMaster = null;
                                    productMaster = null;
                                    locationMaster = null;

                                    lifterPhoto = null;
                                    lifterWeightImageURL = null;
                                    lifterWeightController.clear();
                                    reportNumberController.clear();
                                    notesController.clear();
                                  });

                                  // Trigger full inspection/tank flow for the selected tank.
                                  context.read<TankInspectionBloc>().add(
                                    SelectTankEvent(tank.tankId),
                                  );
                                },
                              );
                            },
                          ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void fillInspectionForm(TankData data) {
    int? _asInt(dynamic v) {
      if (v == null) return null;
      if (v is int) return v;
      if (v is String && int.tryParse(v) != null) return int.parse(v);
      return null;
    }

    // Normalize IDs (backend may return int or string)
    final statusId = _asInt(data.statusId);
    final inspectionTypeId = _asInt(data.inspectionTypeId);
    final locationId = _asInt(data.locationId);

    // Date
    dateController.text =
        data.inspectionDate?.split("T").first ?? _formatToday();

    // Report Number
    reportNumberController.text = data.reportNumber ?? "";

    // Lifter weight image
    if (data.lifterWeight != null && data.lifterWeight!.isNotEmpty) {
      lifterWeightImageURL = "${data.lifterWeight}";
      print("lifterWeightImageURL ${data.lifterWeight!.split("_").last}");
      lifterWeightController.text = data.lifterWeight!.split("_").last;
    } else {
      lifterWeightImageURL = null; // CLEAR IMAGE
      lifterWeightController.text = ""; // CLEAR NAME
    }

    // Dropdowns (wrap in setState to ensure UI updates)
    setState(() {
      statusMaster = posts?.tankStatuses?.firstWhereOrNull(
        (e) => e.statusId == statusId,
      );

      inspectionMaster = posts?.inspectionTypes?.firstWhereOrNull(
        (e) => e.inspectionTypeId == inspectionTypeId,
      );

      locationMaster = posts?.locations?.firstWhereOrNull(
        (e) => e.locationId == locationId,
      );
    });

    // Notes (if present)
    notesController.text = data.notes ?? "";

    // Vacuum reading and lifter weight value (with null-safe defaults)
    vacuumReadingController.text = data.vacuumReading ?? "";
    selectedVacuumUom = (data.vacuumReadingUom ?? "").toUpperCase() == "TORR"
        ? "TORR"
        : "Micron";
    lifterWeightValueController.text = data.lifterWeightValue ?? "";
  }
}
