const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const template = document.getElementById("book-card-template");
const clientCache = new Map();

function setStatus(text, isError = false) {
  statusEl.textContent = text || "";
  statusEl.style.color = isError ? "#ff5555" : "var(--text-dim)";
}

function clearResults() {
  resultsEl.innerHTML = "";
}

function createCard(book) {
  const node = template.content.cloneNode(true);
  const coverLink = node.querySelector(".cover-link");
  const cover = node.querySelector(".cover");
  const title = node.querySelector(".title");
  const author = node.querySelector(".author");
  const rating = node.querySelector(".rating");
  const cta = node.querySelector(".cta");

  const href = book.link || "#";
  coverLink.href = href;
  cta.href = href;
  cta.textContent = "View on Goodreads";

  if (book.cover) {
    cover.style.backgroundImage = `url('${book.cover}')`;
  }

  title.textContent = book.title || "Untitled";
  author.textContent = book.author ? `by ${book.author}` : "Author unknown";
  rating.textContent = book.rating
    ? `★ ${book.rating.toFixed(2)} • ${book.ratings_count ?? "?"} ratings`
    : book.rating_text || "No rating data";

  return node;
}

function showResults(payload, statusText) {
  clearResults();
  payload.results.forEach((book) => {
    resultsEl.appendChild(createCard(book));
  });
  setStatus(statusText);
}

async function runSearch(query, { preferCache = true } = {}) {
  const normalized = query.toLowerCase().trim();

  // Serve instantly from client cache if available.
  if (preferCache && clientCache.has(normalized)) {
    const cached = clientCache.get(normalized);
    showResults(
      cached,
      `Showing cached ${cached.count} result(s) for “${cached.query}”… refreshing`
    );
  } else {
    clearResults();
    setStatus("Scraping Goodreads…");
  }

  const params = new URLSearchParams({ q: query });

  let resp;
  try {
    resp = await fetch(`/api/search?${params.toString()}`);
  } catch (err) {
    setStatus("Network error. Check connection and try again.", true);
    return;
  }

  if (!resp.ok) {
    setStatus(`Server error (${resp.status}). Try again later.`, true);
    return;
  }

  const payload = await resp.json();
  if (payload.error) {
    setStatus(payload.error, true);
    return;
  }

  if (!payload.results || payload.results.length === 0) {
    setStatus("No books found. Try a different query.");
    clearResults();
    return;
  }

  clientCache.set(normalized, payload);
  showResults(payload, `Showing ${payload.count} result(s) for “${payload.query}”.`);
}

form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const q = queryInput.value.trim();
  if (!q) {
    setStatus("Enter a search term first.", true);
    return;
  }
  runSearch(q, { preferCache: false });
});
// Run an initial search for quick feedback.
runSearch("The Hobbit");

