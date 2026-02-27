import { loadTanks, initTankEvents, initAddForm, initEditForm } from "./tank.js";
import { initTabs } from "./tabs.js";
import { initRegulationTab } from "./regulations.js";
import { initCargoTab } from "./cargo.js";
import { initCertificateTab } from "./certificate.js";

window.addEventListener("DOMContentLoaded", async () => {
  await loadTanks();
  initTankEvents();
  initAddForm();
  initEditForm();
  initTabs();
  initRegulationTab();
  initCargoTab();
  initCertificateTab();
});
(async function init() {
  await loadTanks();
  initTankEvents();
})();
// Auto Logout on App Close / Tab Close
window.addEventListener("beforeunload", () => {
  const token = localStorage.getItem("access_token");

  if (token) {
    // Use Blob to ensure application/json Content-Type for sendBeacon
    const data = JSON.stringify({ token: token });
    const blob = new Blob([data], { type: 'application/json' });
    navigator.sendBeacon("/api/auth/logout", blob);
  }

  // Clear all cached data
  localStorage.clear();
  sessionStorage.clear();
});
