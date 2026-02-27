export function showModal(modal) {
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");
}

export function hideModal(modal) {
  modal.classList.remove("show");
  modal.setAttribute("aria-hidden", "true");
}

window.addEventListener("click", (e) => {
  document.querySelectorAll(".modal").forEach(modal => {
    if (e.target === modal) hideModal(modal);
  });
});
