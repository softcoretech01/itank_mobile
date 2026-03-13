import '../models/tank_model.dart';

String normalizeTankSearch(String value) {
  return value.trim().toLowerCase().replaceAll(RegExp(r'\s+'), '');
}

bool tankMatchesSearch(ActiveTank tank, String query) {
  if (query.isEmpty) {
    return true;
  }

  final normalizedTankNumber = normalizeTankSearch(tank.tankNumber ?? '');
  final normalizedTankId = normalizeTankSearch('${tank.tankId ?? ''}');

  return normalizedTankNumber.contains(query) ||
      normalizedTankId.contains(query);
}
