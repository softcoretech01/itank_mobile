// cargo.js
import { escapeHtml, setTableLoading } from "./utils.js";
import { showModal, hideModal } from "./modal.js";


const API_CARGO_MASTER = "https://uat.spairyx.com/iti-web/api/cargo_tank_master";
const API_CARGO_TANK = "https://uat.spairyx.com/iti-web/api/cargo_tank";

// ---------------------------------------------------------
//  INIT CARGO TAB
// ---------------------------------------------------------
export function initCargoTab() {
  const saveBtn = document.getElementById("btnSaveCargo");
  const cargoSelect = document.getElementById("cargoSelect");
  const cargoTableBody = document.querySelector("#cargoTable tbody");
  const tankIdInput = document.getElementById("add_tank_id");
  const btnNewCargo = document.getElementById("btnNewCargo");
  const addCargoModal = document.getElementById("addCargoModal");
  const addCargoForm = document.getElementById("addCargoForm");

  if (!saveBtn || !cargoSelect || !cargoTableBody) return;

  // ✅ Load master list
  loadCargoMasterList();

  // ✅ Save cargo reference (link)
  saveBtn.addEventListener("click", async () => {
    const tankId = tankIdInput.value?.trim();
    const cargoMasterId = cargoSelect.value;

    if (!tankId) {
      alert("❌ Please save the tank first before adding cargo.");
      return;
    }
    if (!cargoMasterId) {
      alert("⚠️ Please select a cargo.");
      return;
    }

    const payload = {
      tank_id: parseInt(tankId),
      cargo_master_id: parseInt(cargoMasterId)    };

    try {
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";

      const res = await fetch(`${API_CARGO_TANK}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to link cargo");

      alert("✅ Cargo linked successfully!");
      await loadCargoForTank(tankId);
    } catch (err) {
      console.error(err);
      alert("❌ Error saving cargo: " + err.message);
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = "Save Cargo Reference";
    }
  });

  // ✅ Auto-load cargo for selected tank when tab opens
  document.querySelector(`.tab-btn[data-tab="tab-cargo"]`)?.addEventListener("click", () => {
    const tankId = tankIdInput.value?.trim();
    if (tankId) loadCargoForTank(tankId);
  });

  // ✅ Handle “+ New Cargo” modal
  btnNewCargo?.addEventListener("click", () => showModal(addCargoModal));
  document.getElementById("closeAddCargoBtn")?.addEventListener("click", () => hideModal(addCargoModal));
  document.getElementById("cancelAddCargo")?.addEventListener("click", () => hideModal(addCargoModal));

  // ✅ Save new cargo to master list
  addCargoForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("newCargoName").value.trim();
    if (!name) {
      alert("⚠️ Please enter a cargo name.");
      return;
    }

    try {
      const saveBtn = addCargoForm.querySelector("button[type='submit']");
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";

      const res = await fetch(`${API_CARGO_MASTER}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cargo_reference: name}),
      });

      if (!res.ok) throw new Error("Failed to add cargo");

      alert("✅ Cargo added successfully!");
      hideModal(addCargoModal);
      document.getElementById("newCargoName").value = "";
      await loadCargoMasterList();
    } catch (err) {
      console.error(err);
      alert("❌ Error creating cargo: " + err.message);
    } finally {
      const saveBtn = addCargoForm.querySelector("button[type='submit']");
      saveBtn.disabled = false;
      saveBtn.textContent = "Save";
    }
  });
}

// ---------------------------------------------------------
//  LOAD CARGO MASTER LIST
// ---------------------------------------------------------
async function loadCargoMasterList() {
  const cargoSelect = document.getElementById("cargoSelect");
  if (!cargoSelect) return;

  try {
    const res = await fetch(`${API_CARGO_MASTER}/`);
    const data = await res.json();
    cargoSelect.innerHTML = `<option value="">Choose a cargo</option>`;
    data.forEach((cargo) => {
      cargoSelect.insertAdjacentHTML(
        "beforeend",
        `<option value="${cargo.id}">${escapeHtml(cargo.cargo_reference)}</option>`
      );
    });
  } catch (err) {
    console.error("Error loading cargo master:", err);
    cargoSelect.innerHTML = `<option value="">Error loading cargo list</option>`;
  }
}

// ---------------------------------------------------------
//  LOAD CARGO FOR SPECIFIC TANK
// ---------------------------------------------------------
async function loadCargoForTank(tankId) {
  const cargoTableBody = document.querySelector("#cargoTable tbody");
  if (!cargoTableBody) return;

  setTableLoading(cargoTableBody, 3, "Loading…");

  try {
    const res = await fetch(`${API_CARGO_TANK}/tank/${tankId}`);
    const data = await res.json();

    cargoTableBody.innerHTML = "";

    if (!Array.isArray(data) || !data.length) {
      setTableLoading(cargoTableBody, 3, "No cargo references found");
      return;
    }

    data.forEach((c) => {
      cargoTableBody.insertAdjacentHTML(
        "beforeend",
        `
        <tr>
          <td>${escapeHtml(c.cargo_reference ?? "")}</td>
          <td>
            <button class="btn btn-danger btn-sm delete-cargo" data-id="${c.id}" data-tank="${tankId}">
              🗑 Delete
            </button>
          </td>
        </tr>
      `
      );
    });

    // Delete handler
    cargoTableBody.querySelectorAll(".delete-cargo").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.target.dataset.id;
        if (confirm("Delete this cargo reference?")) {
          await deleteCargoLink(id, tankId);
        }
      });
    });
  } catch (err) {
    console.error("Error loading cargo for tank:", err);
    setTableLoading(cargoTableBody, 3, "Error loading data");
  }
}

// ---------------------------------------------------------
//  DELETE CARGO LINK
// ---------------------------------------------------------
async function deleteCargoLink(transactionId, tankId) {
  try {
    const res = await fetch(`${API_CARGO_TANK}/${transactionId}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Failed to delete cargo`);
    alert("🗑️ Cargo link deleted successfully!");
    await loadCargoForTank(tankId);
  } catch (err) {
    console.error(err);
    alert("❌ Error deleting cargo: " + err.message);
  }
}