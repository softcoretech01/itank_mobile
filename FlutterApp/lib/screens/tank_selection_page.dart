import 'package:flutter/material.dart';
import 'package:iso_tank/screens/tank_inspection/tank_inspection_flow.dart';

import '../models/tank_model.dart';
import '../repository/tank_repository.dart';
import '../service/ApiClient.dart';
import '../service/DioProvider.dart';
import '../utils/tank_search.dart';

class TankSelectionPage extends StatefulWidget {
  final String userName;

  const TankSelectionPage({super.key, required this.userName});

  @override
  State<TankSelectionPage> createState() => _TankSelectionPageState();
}

class _TankSelectionPageState extends State<TankSelectionPage> {
  ActiveTank? selectedTank;

  List<ActiveTank> allTanks = [];
  List<ActiveTank> filteredTanks = [];

  late TankRepository repo;

  @override
  void initState() {
    super.initState();
    final dio = DioProvider.createDio();
    repo = TankRepository(api: ApiClient(dio), dio: dio);
    loadTanks();
  }

  /// --- Load Tanks From API ---
  Future<void> loadTanks() async {
    try {
      final tankModel = await repo.fetchTanks();

      setState(() {
        allTanks = tankModel.data?.activeTanks ?? [];
        filteredTanks = allTanks;
      });
    } catch (e) {
      print("Tank Fetch Error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          /// --- WAVE BACKGROUND ---
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: ClipPath(
              clipper: _WaveClipper(),
              child: Container(
                height: 260,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Colors.blue, Colors.lightBlueAccent],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
              ),
            ),
          ),

          /// --- MAIN UI ---
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 120),

                Text(
                  "Hi, ${widget.userName} 👋",
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),

                const SizedBox(height: 8),

                const Text(
                  "Select your tank to proceed",
                  style: TextStyle(fontSize: 16, color: Colors.white70),
                ),

                const SizedBox(height: 100),

                /// ----------------------------------------------------------
                /// SELECT TANK BOX (Open Bottom Sheet)
                /// ----------------------------------------------------------
                GestureDetector(
                  onTap: () => openTankBottomSheet(context),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                      vertical: 16,
                      horizontal: 14,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.grey.shade300),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.grey.shade200,
                          blurRadius: 6,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),

                    /// TEXT
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          selectedTank?.tankNumber ?? "Select Tank",
                          style: TextStyle(
                            fontSize: 16,
                            color: selectedTank == null
                                ? Colors.grey
                                : Colors.black,
                          ),
                        ),
                        const Icon(Icons.arrow_drop_down),
                      ],
                    ),
                  ),
                ),

                const Spacer(),

                /// PROCEED BUTTON
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      if (selectedTank == null) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("Please select a tank")),
                        );
                        return;
                      }

                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => TankInspectionFlow()),
                      );

                      print(
                        "Selected Tank ID: ${selectedTank!.tankId} | ${selectedTank!.tankNumber}",
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 3,
                    ),
                    child: const Text(
                      "Proceed",
                      style: TextStyle(fontSize: 18, color: Colors.white),
                    ),
                  ),
                ),

                const SizedBox(height: 100),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// =====================================================================
  /// BOTTOM SHEET -- SHOW API LIST + SEARCH + SELECT
  /// =====================================================================
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
                                onTap: () {
                                  setState(() => selectedTank = tank);
                                  Navigator.pop(context);
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
}

/// Wave background
class _WaveClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    Path path = Path();
    path.lineTo(0, size.height - 50);
    path.quadraticBezierTo(
      size.width / 2,
      size.height,
      size.width,
      size.height - 50,
    );
    path.lineTo(size.width, 0);
    return path;
  }

  @override
  bool shouldReclip(_) => false;
}

/*class TankSelectionPage extends StatelessWidget {
  final String userName;

  const TankSelectionPage({super.key, required this.userName});

  @override
  Widget build(BuildContext context) {
    final TextEditingController menuController = TextEditingController();
    MenuItem? selectedMenu;

    return Scaffold(
      body: Stack(
        children: [
          // --- WAVE BACKGROUND ---
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: ClipPath(
              clipper: _WaveClipper(),
              child: Container(
                height: 260,
                decoration:  BoxDecoration(
                  gradient: LinearGradient(
                    colors: [AppColors.primary, ?AppColors.primarySwatch[200]],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
              ),
            ),
          ),

          // --- MAIN UI ---
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 120),

                // Greeting
                Text(
                  "Hi, $userName 👋",
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 8),

                const Text(
                  "Select your tank to proceed",
                  style: TextStyle(fontSize: 16, color: Colors.white70),
                ),

                const SizedBox(height: 100),

                // Dropdown with search
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  // decoration: BoxDecoration(
                    // color: Colors.white,
                    // borderRadius: BorderRadius.circular(12),
                    // border: Border.all(color: Colors.grey.shade300),
                    // boxShadow: [
                    //   BoxShadow(
                    //     color: Colors.grey.shade200,
                    //     blurRadius: 6,
                    //     offset: const Offset(0, 3),
                    //   ),
                    // ],
                  // ),
                  child: DropdownMenu<MenuItem>(
                    initialSelection: menuItems.first,
                    controller: menuController,
                    width: double.infinity,
                    hintText: "Select Tank",
                    requestFocusOnTap: true,
                    enableFilter: true,
                    label: const Text('Select Tank'),
                    onSelected: (MenuItem? menu) {
                      selectedMenu = menu;
                    },
                    dropdownMenuEntries:
                    menuItems.map<DropdownMenuEntry<MenuItem>>((MenuItem menu) {
                      return DropdownMenuEntry<MenuItem>(
                          value: menu,
                          label: menu.label,);
                    }).toList(),
                  ),
                ),

                const Spacer(),

                // Proceed Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 3,
                    ),
                    child: const Text(
                      "Proceed",
                      style: TextStyle(fontSize: 18, color: Colors.white),
                    ),
                  ),
                ),
                const SizedBox(height: 100),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class MenuItem {
  final int id;
  final String label;
  final IconData icon;

  MenuItem(this.id, this.label, this.icon);
}

List<MenuItem> menuItems = [
  MenuItem(1, 'Tank001', Icons.home),
  MenuItem(2, 'Tank002', Icons.person),
  MenuItem(3, 'Tank003', Icons.settings),
  MenuItem(4, 'Tank004', Icons.favorite),
  MenuItem(5, 'Tank005', Icons.notifications)
];

// WAVE CLIPPER
class _WaveClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    Path path = Path();
    path.lineTo(0, size.height - 50);
    path.quadraticBezierTo(
        size.width / 2, size.height, size.width, size.height - 50);
    path.lineTo(size.width, 0);
    return path;
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}*/
