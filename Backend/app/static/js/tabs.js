export function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const mainFooter = document.querySelector(".footer-actions:last-child"); // the bottom Save/Cancel area

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;

      // Remove previous active states
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((tab) => tab.classList.remove("active"));

      // Activate selected tab
      btn.classList.add("active");
      document.getElementById(targetId)?.classList.add("active");

      // ✅ Hide bottom "Save" footer when not on Tank tab
      if (mainFooter) {
        if (targetId === "tab-tank") {
          mainFooter.style.display = "flex"; // Show for Tank tab
        } else {
          mainFooter.style.display = "none"; // Hide for Regulations, Cargo, etc.
        }
      }
    });
  });

  // ✅ Make sure correct footer is shown on load
  const activeTab = document.querySelector(".tab-btn.active")?.dataset.tab;
  if (mainFooter) {
    mainFooter.style.display = activeTab === "tab-tank" ? "flex" : "none";
  }
}
