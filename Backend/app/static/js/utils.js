export function parseFloatOrNull(v) {
  if (!v || v.trim() === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function setTableLoading(tb, colspan = 5, message = "Loading…") {
  tb.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;padding:10px;color:#555;">${message}</td></tr>`;
}
