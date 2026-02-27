// regulations.js — revised for Regulations tab inside Add Modal
const API_REG = "https://uat.spairyx.com/iti-web/api/regulations";

/**
 * Initialize the Regulations Tab inside Add Modal
 */
export function initRegulationTab() {
  const btnNewReg = document.getElementById("btnNewRegFromTank");
  const regulationSelect = document.getElementById("regulationSelect");
  const regulationText = document.getElementById("regulationText");
  const btnSaveRegulation = document.getElementById("btnSaveRegulation");

  // These IDs exist inside your tab layout
  if (!btnNewReg || !regulationSelect) return;

  // ----------------------------------------------------------------
  // LOAD ALL REGULATIONS INTO DROPDOWN
  // ----------------------------------------------------------------
  async function loadRegulations() {
    try {
      const res = await fetch(`${API_REG}/`);
      if (!res.ok) throw new Error(`Failed to load: ${res.status}`);
      const data = await res.json();

      regulationSelect.innerHTML = '<option value="">Choose a regulation</option>';
      if (Array.isArray(data) && data.length > 0) {
        data.forEach((r) => {
          const opt = document.createElement("option");
          opt.value = r.id;
          opt.textContent = r.regulation_name;
          regulationSelect.appendChild(opt);
        });
      }
    } catch (err) {
      console.error("Error loading regulations:", err);
    }
  }

  // ----------------------------------------------------------------
  // SHOW/HIDE APPROVAL TEXT AREA WHEN SELECT CHANGES
  // ----------------------------------------------------------------
  regulationSelect.addEventListener("change", () => {
    if (regulationSelect.value) {
      regulationText.style.display = "block";
    } else {
      regulationText.style.display = "none";
      regulationText.value = "";
    }
  });

  // ----------------------------------------------------------------
  // CREATE NEW REGULATION (inline, no popup)
  // ----------------------------------------------------------------
  btnNewReg.addEventListener("click", async () => {
    const newReg = prompt("Enter new Regulation name:");
    if (!newReg) return;

    try {
      const res = await fetch(`${API_REG}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ regulation_name: newReg }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Failed to create regulation");
      }

      alert("✅ Regulation added successfully!");
      await loadRegulations();
      // auto-select newly added regulation
      const allOpts = Array.from(regulationSelect.options);
      const match = allOpts.find((opt) => opt.textContent === newReg);
      if (match) {
        regulationSelect.value = match.value;
        regulationText.style.display = "block";
      }
    } catch (err) {
      alert("❌ Failed to add regulation: " + err.message);
      console.error(err);
    }
  });

  // ----------------------------------------------------------------
  // SAVE REGULATION LINK TO CURRENT TANK
  // ----------------------------------------------------------------
  btnSaveRegulation.addEventListener("click", async () => {
    const tankId = document.getElementById("add_tank_id").value;
    const regulationId = regulationSelect.value;
    const approvalText = regulationText.value.trim();

    if (!tankId) return alert("Please save a tank first.");
    if (!regulationId) return alert("Please select a regulation.");

    const payload = {
      tank_id: tankId,
      regulation_id: regulationId,
      initial_approval_no: approvalText || null,
    };

    try {
      const res = await fetch("https://uat.spairyx.com/iti-web/api/regulations_tank/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Failed to link regulation");
      }

      alert("✅ Regulation linked to tank successfully!");
      await loadTankRegulations(tankId);
    } catch (err) {
      alert("❌ " + err.message);
      console.error(err);
    }
  });

  // ----------------------------------------------------------------
  // LOAD LINKED REGULATIONS FOR CURRENT TANK
  // ----------------------------------------------------------------
  async function loadTankRegulations(tankId) {
    const tableBody = document.querySelector("#regulationsTable tbody");
    if (!tableBody) return;
    tableBody.innerHTML = "<tr><td colspan='3'>Loading...</td></tr>";

    try {
      const res = await fetch(`https://uat.spairyx.com/iti-web/api/regulations_tank/tank/${tankId}`);
      if (!res.ok) throw new Error("Failed to load linked regulations");
      const data = await res.json();

      if (!Array.isArray(data) || data.length === 0) {
        tableBody.innerHTML = "<tr><td colspan='3'>No linked regulations</td></tr>";
        return;
      }

      tableBody.innerHTML = "";
      data.forEach((r) => {
        const tr = document.createElement("tr");

        const tdReg = document.createElement("td");
        tdReg.textContent = r.regulation_name ?? "";
        tr.appendChild(tdReg);

        const tdApp = document.createElement("td");
        const input = document.createElement("input");
        input.type = "text";
        input.value = r.initial_approval_no ?? "";
        input.style.width = "100%";
        input.addEventListener("blur", async () => {
          const val = input.value.trim();
          try {
            const updateRes = await fetch(
              `https://uat.spairyx.com/iti-web/api/regulations_tank/${r.id}`,
              {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ initial_approval_no: val || null }),
              }
            );
            if (!updateRes.ok) throw new Error("Failed to update");
          } catch (err) {
            alert("❌ " + err.message);
          }
        });
        tdApp.appendChild(input);
        tr.appendChild(tdApp);

        const tdActions = document.createElement("td");
        const btnDel = document.createElement("button");
        btnDel.className = "btn btn-danger";
        btnDel.textContent = "🗑 Delete";
        btnDel.addEventListener("click", async () => {
          if (!confirm("Delete this regulation link?")) return;
          try {
            const delRes = await fetch(
              `https://uat.spairyx.com/iti-web/api/regulations_tank/${r.id}`,
              { method: "DELETE" }
            );
            if (!delRes.ok) throw new Error("Failed to delete");
            await loadTankRegulations(tankId);
          } catch (err) {
            alert("❌ " + err.message);
          }
        });
        tdActions.appendChild(btnDel);
        tr.appendChild(tdActions);

        tableBody.appendChild(tr);
      });
    } catch (err) {
      console.error(err);
      tableBody.innerHTML = "<tr><td colspan='3'>Error loading data</td></tr>";
    }
  }

  // ----------------------------------------------------------------
  // INITIAL LOAD
  // ----------------------------------------------------------------
  loadRegulations();

  // re-load linked regulations when user switches to Regulations tab
  const tabBtn = document.querySelector(".tab-btn[data-tab='tab-regulations']");
  if (tabBtn) {
    tabBtn.addEventListener("click", async () => {
      const tankId = document.getElementById("add_tank_id").value;
      if (tankId) await loadTankRegulations(tankId);
    });
  }
}
