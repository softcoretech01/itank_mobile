import 'package:flutter/material.dart';

import '../../../models/tank_details_response.dart';
import '../../../models/tank_model.dart';

class TankDetailsCard extends StatelessWidget {
  final ActiveTank tankData;
  final TankData? tankDetailsResponse;

  const TankDetailsCard({
    super.key,
    required this.tankData,required this.tankDetailsResponse,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: Colors.white,
      margin: const EdgeInsets.symmetric(horizontal: 20),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 10),
            _row("Working Pressure", "${tankDetailsResponse?.workingPressure}"),
            _row("Design Temperature", "${tankDetailsResponse?.designTemperature}"),
            _row("Frame Type", "${tankDetailsResponse?.frameType}"),
            _row("Cabinet Type", "${tankDetailsResponse?.cabinetType}"),
            _row("Ownership", "${tankDetailsResponse?.ownership}"),
            _row("PI - Next Inspection Date", "${tankDetailsResponse?.piNextInspectionDate}"),
            _row("Manufacturer", "${tankDetailsResponse?.mfgr}"),
          ],
        ),
      ),
    );
  }

  Widget _row(String key, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(key, style: const TextStyle(fontWeight: FontWeight.w400,color: Colors.grey)),
          Text(value, style: const TextStyle(color: Colors.black,fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
