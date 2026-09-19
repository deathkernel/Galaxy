const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const results = document.getElementById("results");
const status = document.getElementById("status");

function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function label(key) {
  return key.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
}

function render(data) {
  if (!data.matches?.length) {
    results.innerHTML = `<div class="empty"><h2>Nothing found</h2><p>${esc(data.message)}</p></div>`;
    return;
  }

  results.innerHTML = data.matches.map(match => {
    const d = match.details || {};
    const image = d.thumbnail || d.hdurl || (d.media_type === "image" ? d.url : null);
    const description = d.extract || d.description || d.explanation;
    const rows = Object.entries(d)
      .filter(([key, value]) => value !== null && value !== undefined && value !== "" && !["thumbnail", "extract", "explanation", "url", "hdurl", "description"].includes(key))
      .map(([key, value]) => `<div class="row"><span>${esc(label(key))}</span><strong>${esc(value)}</strong></div>`).join("");

    return `<article class="result-card">
      ${image ? `<img class="object-image" src="${esc(image)}" alt="${esc(match.name)}" loading="lazy">` : ""}
      <div class="badge">${esc(match.type)}</div>
      <h2>${esc(match.name)}</h2>
      ${description ? `<p class="description">${esc(description)}</p>` : ""}
      <div class="facts">${rows}</div>
      ${d.url ? `<a class="source-link" href="${esc(d.url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>` : ""}
    </article>`;
  }).join("");
}

async function search(q) {
  queryInput.value = q;
  status.textContent = "Scanning public space databases…";
  results.innerHTML = "";
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Search failed");
    status.textContent = data.matches?.length ? `${data.matches.length} data source${data.matches.length === 1 ? "" : "s"} returned results.` : "";
    render(data);
  } catch (error) {
    status.textContent = "";
    results.innerHTML = `<div class="empty error"><h2>Search error</h2><p>${esc(error.message)}</p></div>`;
  }
}

form.addEventListener("submit", e => { e.preventDefault(); search(queryInput.value.trim()); });
document.querySelectorAll("[data-query]").forEach(button => button.addEventListener("click", () => search(button.dataset.query)));
