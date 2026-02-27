import 'package:iso_tank/models/tank_master_data.dart';

import '../models/check_list_response.dart';
import '../models/status_master_response.dart';
import '../service/ApiClient.dart';

class MasterData {
  final ApiClient api;

  MasterData(this.api);

  Future<TankMasterResponse> fetchMasterData() {
    return api.fetchTankMasterData();
  }

  Future<CheckListResponse> fetchChecklist() async {
    return await api.getChecklist();
  }

  Future<StatusMasterResponse> fetchStatusMaster() async {
    return await api.getStatusMaster();
  }
}
