// tank.js
import { escapeHtml, setTableLoading } from "./utils.js";
import { showModal, hideModal } from "./modal.js";

const API_TANK = "https://uat.spairyx.com/iti-web/api/tank-details";

export async function loadTanks() {
  const tankTableBody = document.querySelector("#tankTable tbody");
  setTableLoading(tankTableBody, 5, "Loading…");

  try {
    const res = await fetch(`${API_TANK}/`);
    const data = await res.json();
    tankTableBody.innerHTML = "";

    if (!Array.isArray(data) || !data.length) {
      setTableLoading(tankTableBody, 5, "No tanks found");
      return;
    }

    data.forEach((t) => {
      tankTableBody.insertAdjacentHTML(
        "beforeend",
        `
        <tr>
          <td>${escapeHtml(t.tank_number ?? "")}</td>
          <td>${escapeHtml(t.pv_code ?? "")}</td>
          <td>${escapeHtml(t.un_iso_code ?? "")}</td>
          <td>${t.capacity_l ?? ""}</td>
          <td>
            <button class="btn-ghost btn edit-btn" data-id="${t.id}">✏ Edit</button>
            <button class="btn btn-danger delete-btn" data-id="${t.id}">🗑 Delete</button>
          </td>
        </tr>
      `
      );
    });
  } catch (err) {
    console.error(err);
    setTableLoading(tankTableBody, 5, "Error loading tanks");
  }
}

// ---------------------------------------------------------
//  INITIALIZE EVENTS (Open/Close Modals, Buttons)
// ---------------------------------------------------------
export function initTankEvents() {
  const addModal = document.getElementById("addModal");
  const editModal = document.getElementById("editModal");

  document.getElementById("btnNewTank").addEventListener("click", () => {
    document.getElementById("addForm").reset();
    showModal(addModal);

    // ✅ Auto-sync tank number fields across tabs (Regulations + Cargo)
    syncTankNumberFields();
  });

  document.getElementById("closeAddBtn").addEventListener("click", () => hideModal(addModal));
  document.getElementById("cancelAdd").addEventListener("click", () => hideModal(addModal));
  document.getElementById("closeEditBtn").addEventListener("click", () => hideModal(editModal));
  document.getElementById("cancelEdit").addEventListener("click", () => hideModal(editModal));

  // Handle edit/delete button clicks
  document.querySelector("#tankTable").addEventListener("click", async (e) => {
    const id = e.target.dataset.id;
    if (e.target.classList.contains("edit-btn")) {
      await onEdit(id);
    } else if (e.target.classList.contains("delete-btn")) {
      await onDelete(id);
    }
  });
}

// ---------------------------------------------------------
//  ADD NEW TANK (POST)
// ---------------------------------------------------------
export function initAddForm() {
  const addForm = document.getElementById("addForm");

  addForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      tank_number: document.getElementById("add_tank_number").value.trim(),
      mfgr: document.getElementById("add_mfgr").value.trim(),
      date_mfg: document.getElementById("add_date_mfg").value || null,
      pv_code: document.getElementById("add_pv_code").value.trim(),
      un_iso_code: document.getElementById("add_un_iso_code").value.trim(),
      capacity_l: parseFloat(document.getElementById("add_capacity_l").value) || null,
      mawp: parseFloat(document.getElementById("add_mawp").value) || null,
      design_temperature: document.getElementById("add_design_temperature").value || null,
      tare_weight_kg: parseFloat(document.getElementById("add_tare_weight_kg").value) || null,
      mgw_kg: parseFloat(document.getElementById("add_mgw_kg").value) || null,
      mpl_kg: parseFloat(document.getElementById("add_mpl_kg").value) || null,
      size: document.getElementById("add_size").value.trim(),
      pump_type: document.getElementById("add_pump_type").value.trim(),
      vesmat: document.getElementById("add_vesmat").value.trim(),
      gross_kg: parseFloat(document.getElementById("add_gross_kg").value) || null,
      net_kg: parseFloat(document.getElementById("add_net_kg").value) || null,
      color_body_frame: document.getElementById("add_color_body_frame").value.trim(),
      remark: document.getElementById("add_remark").value.trim(),
      lease: document.getElementById("add_lease").checked ? 1 : 0,
      created_by: document.getElementById("add_created_by").value.trim() || null,
    };

    try {
      const saveBtn = addForm.querySelector("button[type='submit']");
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";

      const res = await fetch(`${API_TANK}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Failed to save");
      }

      const data = await res.json();

      // ✅ Store tank ID
      document.getElementById("add_tank_id").value = data.id || data.tank_id;

      // ✅ Auto-fill tank number in Regulations and Cargo tabs
      const tankNumber = document.getElementById("add_tank_number").value.trim();
      const tankNumberDisplay = document.getElementById("tankNumberDisplay");
      const cargoTankDisplay = document.getElementById("cargoTankNumber");

      if (tankNumberDisplay) tankNumberDisplay.value = tankNumber;
      if (cargoTankDisplay) cargoTankDisplay.value = tankNumber;

      alert("✅ Tank saved successfully! You can now add Regulations or Cargo.");

      // ✅ Keep modal open for next steps
      await loadTanks();
    } catch (err) {
      console.error(err);
      alert("❌ Error saving tank: " + err.message);
    } finally {
      const saveBtn = addForm.querySelector("button[type='submit']");
      saveBtn.disabled = false;
      saveBtn.textContent = "Save";
    }
  });

  // ✅ Live update tank number in other tabs as user types
  const addTankNumberInput = document.getElementById("add_tank_number");
  const tankNumberDisplay = document.getElementById("tankNumberDisplay");
  const cargoTankDisplay = document.getElementById("cargoTankNumber");

  if (addTankNumberInput) {
    addTankNumberInput.addEventListener("input", () => {
      const val = addTankNumberInput.value.trim();
      if (tankNumberDisplay) tankNumberDisplay.value = val;
      if (cargoTankDisplay) cargoTankDisplay.value = val;
    });
  }
}

// ---------------------------------------------------------
//  EDIT TANK (GET + FILL MODAL)
// ---------------------------------------------------------
async function onEdit(id) {
  try {
    const res = await fetch(`${API_TANK}/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch tank: ${res.status}`);
    const t = await res.json();

    // fill form
    document.getElementById("edit_id").value = t.id ?? "";
    document.getElementById("edit_tank_number").value = t.tank_number ?? "";
    document.getElementById("edit_mfgr").value = t.mfgr ?? "";
    document.getElementById("edit_date_mfg").value = t.date_mfg ?? "";
    document.getElementById("edit_pv_code").value = t.pv_code ?? "";
    document.getElementById("edit_un_iso_code").value = t.un_iso_code ?? "";
    document.getElementById("edit_capacity_l").value = t.capacity_l ?? "";
    document.getElementById("edit_mawp").value = t.mawp ?? "";
    document.getElementById("edit_design_temperature").value = t.design_temperature ?? "";
    document.getElementById("edit_tare_weight_kg").value = t.tare_weight_kg ?? "";
    document.getElementById("edit_mgw_kg").value = t.mgw_kg ?? "";
    document.getElementById("edit_mpl_kg").value = t.mpl_kg ?? "";
    document.getElementById("edit_size").value = t.size ?? "";
    document.getElementById("edit_pump_type").value = t.pump_type ?? "";
    document.getElementById("edit_vesmat").value = t.vesmat ?? "";
    document.getElementById("edit_gross_kg").value = t.gross_kg ?? "";
    document.getElementById("edit_net_kg").value = t.net_kg ?? "";
    document.getElementById("edit_color_body_frame").value = t.color_body_frame ?? "";
    document.getElementById("edit_remark").value = t.remark ?? "";
    document.getElementById("edit_lease").checked = t.lease === 1 || t.lease === true;
    document.getElementById("edit_updated_by").value = t.updated_by ?? "";

    showModal(document.getElementById("editModal"));
  } catch (err) {
    console.error(err);
    alert("Unable to open edit modal: " + err.message);
  }
}

// ---------------------------------------------------------
//  UPDATE TANK (PUT)
// ---------------------------------------------------------
export function initEditForm() {
  const editForm = document.getElementById("editForm");

  editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("edit_id").value;

    const payload = {
      tank_number: document.getElementById("edit_tank_number").value.trim(),
      mfgr: document.getElementById("edit_mfgr").value.trim(),
      date_mfg: document.getElementById("edit_date_mfg").value || null,
      pv_code: document.getElementById("edit_pv_code").value.trim(),
      un_iso_code: document.getElementById("edit_un_iso_code").value.trim(),
      capacity_l: parseFloat(document.getElementById("edit_capacity_l").value) || null,
      mawp: parseFloat(document.getElementById("edit_mawp").value) || null,
      design_temperature: document.getElementById("edit_design_temperature").value || null,
      tare_weight_kg: parseFloat(document.getElementById("edit_tare_weight_kg").value) || null,
      mgw_kg: parseFloat(document.getElementById("edit_mgw_kg").value) || null,
      mpl_kg: parseFloat(document.getElementById("edit_mpl_kg").value) || null,
      size: document.getElementById("edit_size").value.trim(),
      pump_type: document.getElementById("edit_pump_type").value.trim(),
      vesmat: document.getElementById("edit_vesmat").value.trim(),
      gross_kg: parseFloat(document.getElementById("edit_gross_kg").value) || null,
      net_kg: parseFloat(document.getElementById("edit_net_kg").value) || null,
      color_body_frame: document.getElementById("edit_color_body_frame").value.trim(),
      remark: document.getElementById("edit_remark").value.trim(),
      lease: document.getElementById("edit_lease").checked ? 1 : 0,
      updated_by: document.getElementById("edit_updated_by").value.trim() || null,
    };

    try {
      const saveBtn = editForm.querySelector("button[type='submit']");
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";

      const res = await fetch(`${API_TANK}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Failed to update");
      }

      alert("✅ Tank updated successfully!");
      hideModal(document.getElementById("editModal"));
      await loadTanks();
    } catch (err) {
      console.error(err);
      alert("❌ Error updating tank: " + err.message);
    } finally {
      const saveBtn = editForm.querySelector("button[type='submit']");
      saveBtn.disabled = false;
      saveBtn.textContent = "Save Changes";
    }
  });
}

// ---------------------------------------------------------
//  DELETE TANK
// ---------------------------------------------------------
async function onDelete(id) {
  if (!confirm("Delete this tank?")) return;
  try {
    const res = await fetch(`${API_TANK}/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Failed to delete: ${res.status}`);
    alert("🗑️ Tank deleted successfully!");
    await loadTanks();
  } catch (err) {
    console.error(err);
    alert("❌ Error deleting tank: " + err.message);
  }
}

// ---------------------------------------------------------
//  SYNC TANK NUMBER ACROSS TABS
// ---------------------------------------------------------
export function syncTankNumberFields() {
  const tankInput = document.getElementById("add_tank_number");
  const regTankDisplay = document.getElementById("tankNumberDisplay");
  const cargoTankDisplay = document.getElementById("cargoTankNumber");

  if (!tankInput) return;

  tankInput.addEventListener("input", () => {
    const val = tankInput.value.trim();
    if (regTankDisplay) regTankDisplay.value = val;
    if (cargoTankDisplay) cargoTankDisplay.value = val;
  });

  const initialVal = tankInput.value.trim();
  if (regTankDisplay) regTankDisplay.value = initialVal;
  if (cargoTankDisplay) cargoTankDisplay.value = initialVal;
}
