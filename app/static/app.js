const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const results = document.getElementById("results");
const status = document.getElementById("status");

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function render(data) {
  if (!data.matches?.length) {
    results.innerHTML = `
      <div class="empty">
        <h2>No direct match</h2>
        <p>${esc(data.message)}</p>
      </div>`;
    return;
  }

  results.innerHTML = data.matches.map(match => {
    const details = match.details || {};
    const rows = Object.entries(details)
      .filter(([, value]) => value !== null && value !== undefined && value !== "")
      .map(([key, value]) => `
        <div class="row">
          <span>${esc(key.replaceAll("_", " "))}</span>
          <strong>${esc(value)}</strong>
        </div>`
      ).join("");

    return `
      <article class="result-card">
        <div class="badge">${esc(match.type)}</div>
        <h2>${esc(match.name)}</h2>
        ${rows}
      </article>`;
  }).join("");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const q = queryInput.value.trim();
  if (!q) return;

  status.textContent = "Searching the public space databases…";
  results.innerHTML = "";

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Search failed");
    }

    status.textContent = "";
    render(data);
  } catch (error) {
    status.textContent = "";
    results.innerHTML = `
      <div class="empty error">
        <h2>Search error</h2>
        <p>${esc(error.message)}</p>
      </div>`;
  }
});
