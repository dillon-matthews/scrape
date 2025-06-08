#!/usr/bin/env python3
"""
download_videos.py

A crawler + scraper that:

1. Starts at your BASE_URL defined in CONFIG section
2. Crawls internal pages (same domain), up to a configurable limit
3. Parses each page for video URLs by:
     - Extracting <video> → <source> tags
     - Scanning all src/href attributes for “/video/… .mp4/.webm” via regex
4. Deduplicates and downloads each video into a local `videos/` folder
5. Reports total elapsed time and number of videos found/downloaded

Requirements:
    pip install requests beautifulsoup4

Usage:
    python download_videos.py
"""

import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# — CONFIG — #
BASE_URL    = "https://enterawebsite.com/"
VIDEO_DIR   = "videos"
MAX_PAGES   =1000    # max pages to crawl
# — END CONFIG — #

def is_internal_link(href):
    """Return True if href is an internal link to our domain."""
    if not href:
        return False
    parsed = urlparse(urljoin(BASE_URL, href))
    return parsed.netloc == urlparse(BASE_URL).netloc

def gather_page_urls(html, base):
    """Extract all internal page URLs from anchors in html."""
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#",1)[0]
        if is_internal_link(href):
            abs_url = urljoin(base, href)
            urls.add(abs_url)
    return urls

def find_video_urls(html, base):
    """Parse the page HTML and return a deduped set of absolute video URLs."""
    urls = set()
    soup = BeautifulSoup(html, "html.parser")

    # 1) <video> / <source> tags
    for video in soup.find_all("video"):
        for src in video.find_all("source"):
            raw = src.get("src")
            if raw:
                urls.add(urljoin(base, raw))

    # 2) Regex scan for any /video/...mp4 or .webm in src/href strings
    for match in re.findall(r'src=["\'](/video/[^"\']+\.(?:mp4|webm))', html):
        urls.add(urljoin(base, match))

    for match in re.findall(r'href=["\'](/video/[^"\']+\.(?:mp4|webm))', html):
        urls.add(urljoin(base, match))

    return urls

def download_file(url, dest_folder):
    """Stream-download a file from `url` into `dest_folder`."""
    os.makedirs(dest_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path)
    out_path = os.path.join(dest_folder, filename)
    if os.path.exists(out_path):
        print(f"[skip]     {filename} already exists.")
        return
    print(f"[download] {filename}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
    mb = total / 1024**2
    print(f"[saved]    {filename} ({mb:.1f} MB)")

def main():
    visited_pages = set()
    to_crawl = {BASE_URL}
    found_videos = set()

    print("Starting crawl & scrape…")
    start_time = time.perf_counter()

    while to_crawl and len(visited_pages) < MAX_PAGES:
        url = to_crawl.pop()
        if url in visited_pages:
            continue
        print(f"\n[fetching] {url}")
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"[error]    failed to fetch {url}: {e}")
            visited_pages.add(url)
            continue

        html = resp.text
        visited_pages.add(url)

        # find videos on this page
        vids = find_video_urls(html, url)
        if vids:
            print(f"           → found {len(vids)} video(s) here")
        found_videos.update(vids)

        # discover new internal pages to crawl
        pages = gather_page_urls(html, url)
        new_pages = pages - visited_pages
        to_crawl.update(new_pages)

    # report & download
    total_pages = len(visited_pages)
    total_videos = len(found_videos)
    print(f"\nCrawled {total_pages} page(s), found {total_videos} unique video(s).")
    if not found_videos:
        print("No videos to download. Exiting.")
        return

    for vid_url in sorted(found_videos):
        download_file(vid_url, VIDEO_DIR)

    elapsed = time.perf_counter() - start_time
    print(f"\nDone in {elapsed:.1f} seconds.")

if __name__ == "__main__":
    main()
