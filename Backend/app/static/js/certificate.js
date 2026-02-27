// certificate.js
const API_CERT = "http://127.0.0.1:8000/tank-inspection";
const API_TANK_DETAILS = "http://127.0.0.1:8000/tank-details/by-number/";

export function initCertificateTab() {
  console.log("✅ Certificate tab initialized");

  const tankNumberInput = document.getElementById("add_tank_number");
  const yearMfgInput = document.getElementById("add_year_mfg");

  if (tankNumberInput && yearMfgInput) {
    async function fetchYearOfManufacturing(tankNumber) {
      try {
        const res = await fetch(`${API_TANK_DETAILS}${tankNumber}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.date_mfg) {
          const year = new Date(data.date_mfg).getFullYear();
          yearMfgInput.value = year;
        }
      } catch (err) {
        console.error("Error fetching tank details:", err);
      }
    }

    tankNumberInput.addEventListener("change", () => {
      const val = tankNumberInput.value.trim();
      if (val) fetchYearOfManufacturing(val);
    });

    // Also run when user switches to the Certificate tab
    const certTabBtn = document.querySelector('[data-tab="tab-certificate"]');
    if (certTabBtn) {
      certTabBtn.addEventListener("click", () => {
        const val = tankNumberInput.value.trim();
        if (val) fetchYearOfManufacturing(val);
      });
    }
  }
}

// 🔹 Function to save certificate after tank creation
export async function saveCertificate() {
  const insp_date = document.getElementById("add_insp_date")?.value || null;
  const next_insp_date = document.getElementById("add_next_insp_date")?.value || null;
  const tank_cert_no = document.getElementById("add_tank_cert_no")?.value || null;
  const cert_file = document.getElementById("add_certificate_file")?.files[0] || null;
  const created_by = document.getElementById("add_created_by")?.value || null;

  if (!insp_date || !next_insp_date || !tank_cert_no) {
    console.log("ℹ️ Skipping certificate save (incomplete fields).");
    return;
  }

  const certData = {
    insp_2_5y_date: insp_date,
    next_insp_date: next_insp_date,
    tank_certificate: tank_cert_no,
    created_by: created_by || null,
    updated_by: created_by || null
  };

  try {
    if (cert_file) {
      const formData = new FormData();
      formData.append("file", cert_file);

      const uploadRes = await fetch(`${API_CERT}/upload-certificate/`, {
        method: "POST",
        body: formData,
      });
      const uploadData = await uploadRes.json();
      certData.tank_certificate = uploadData.file_path;
    }

    const response = await fetch(`${API_CERT}/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(certData),
    });

    if (response.ok) {
      console.log("✅ Certificate saved!");
    } else {
      const err = await response.json();
      console.error("❌ Certificate save failed:", err);
    }
  } catch (err) {
    console.error("❌ Error saving certificate:", err);
  }
}
