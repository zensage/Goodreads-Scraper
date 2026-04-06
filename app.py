import re
import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

GOODREADS_BASE = "https://www.goodreads.com"
SEARCH_PATH = "/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = (5, 15)
CACHE_TTL_SECONDS = 300
MAX_RESULTS = 20

session = requests.Session()
session.headers.update(HEADERS)


def _rating_tuple(minirating: str) -> Tuple[Optional[float], Optional[int]]:
    """
    Extract rating value and count from Goodreads mini rating string.
    Example input: '4.12 avg rating — 81,953 ratings'
    """
    rating_match = re.search(r"([0-9]\.\d{1,2})", minirating)
    count_match = re.search(r"([\d,]+)\s+ratings", minirating)
    rating = float(rating_match.group(1)) if rating_match else None
    count = int(count_match.group(1).replace(",", "")) if count_match else None
    return rating, count


def _parse_results(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.tableList")
    if not table:
        return []

    books = []
    for row in table.select("tr")[:MAX_RESULTS]:
        title_tag = row.select_one("a.bookTitle")
        author_tag = row.select_one("a.authorName")
        rating_tag = row.select_one("span.minirating")
        cover_tag = row.select_one("img.bookCover")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = urljoin(GOODREADS_BASE, title_tag.get("href", ""))
        author = author_tag.get_text(strip=True) if author_tag else None
        rating_text = rating_tag.get_text(strip=True) if rating_tag else ""
        rating_value, rating_count = _rating_tuple(rating_text)
        cover_raw = cover_tag.get("src", None) if cover_tag else None
        cover = _better_cover(cover_raw)

        books.append(
            {
                "title": title,
                "author": author,
                "rating": rating_value,
                "ratings_count": rating_count,
                "rating_text": rating_text,
                "link": link,
                "cover": cover,
            }
        )
    return books


def _search_url(query: str, page: int) -> str:
    return f"{GOODREADS_BASE}{SEARCH_PATH}?q={quote(query)}&page={page}"


def _cached_key(query: str, page: int) -> str:
    return f"{query.lower().strip()}::{page}"


_cache: Dict[str, Tuple[float, List[Dict]]] = {}


def _better_cover(url: Optional[str]) -> Optional[str]:
    """
    Goodreads search returns tiny thumbnails; upsize to a clearer image by
    replacing size tokens with larger dimensions when present.
    """
    if not url:
        return url

    # Aim for larger assets; Goodreads uses size tokens like _SX50_, _SY75_,
    # sometimes combined with crop tokens (CRx,y,w,h).
    target_w = 600
    target_h = 900
    url = re.sub(
        r"\._SX\d+_SY\d+_CR\d+,\d+,\d+,\d+_",
        f"._SX{target_w}_SY{target_h}_",
        url,
    )
    url = re.sub(r"\._SX\d+_SY\d+_", f"._SX{target_w}_SY{target_h}_", url)
    url = re.sub(r"\._SX\d+_", f"._SX{target_w}_", url)
    url = re.sub(r"\._SY\d+_", f"._SY{target_h}_", url)
    return url


def search_goodreads(query: str, page: int = 1) -> List[Dict]:
    key = _cached_key(query, page)
    now = time.time()
    if key in _cache:
        timestamp, data = _cache[key]
        if now - timestamp < CACHE_TTL_SECONDS:
            return data

    url = _search_url(query, page)
    resp = session.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    books = _parse_results(resp.text)
    _cache[key] = (now, books)
    return books


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    page_raw = request.args.get("page", "1")
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    try:
        page = max(1, int(page_raw))
    except ValueError:
        return jsonify({"error": "Page must be an integer"}), 400

    try:
        books = search_goodreads(query, page=page)
    except requests.HTTPError as exc:
        return jsonify({"error": f"Goodreads returned HTTP {exc.response.status_code}"}), 502
    except requests.RequestException:
        return jsonify({"error": "Network error talking to Goodreads"}), 504

    return jsonify(
        {
            "query": query,
            "page": page,
            "count": len(books),
            "results": books,
            "source": "goodreads.com",
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

