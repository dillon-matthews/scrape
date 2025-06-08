A crawler & scraper to find and download videos from any website.

---

## Features

- Starts crawling from a **BASE_URL** you define in the config  
- Follows **internal links** (same domain) up to a configurable depth or page limit  
- Extracts video URLs by:
  - Scanning all `src`/`href` attributes for patterns like `/video/... .mp4` or `.webm`  
  - Using a regex to match common video file extensions  
- Deduplicates found URLs to avoid repeats  
- Downloads all videos into a local `videos/` folder  
- Reports total run time and number of videos found/downloaded

---

## Requirements

- Python 3.6+  
- [requests](https://pypi.org/project/requests/)  
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)  

```bash
pip install requests beautifulsoup4
