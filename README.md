# ReconScraper

## Overview

`ReconScraper` is a web scraping tool designed for educational purposes as part of a cybersecurity reconnaissance project. It allows users to crawl a target website, search for specific keywords, and save results in JSON and CSV formats. The tool includes features to respect website restrictions (e.g., robots.txt) and provides options to configure crawling depth and URL limits.

## Disclaimer

**This tool is intended for educational purposes only.** It is designed to help students and researchers understand web scraping techniques in a controlled, ethical environment. Any use of `ReconScraper` is at the user's own responsibility. Users must:

- Respect the privacy of individuals and organizations.
- Comply with all applicable website regulations, terms of service, and legal requirements (e.g., robots.txt, GDPR, and local laws).
- Avoid using this tool to harm systems, networks, or websites.

The developers of `ReconScraper` are not liable for any misuse or damage caused by this tool.

## Features

- Crawl a target website up to a specified depth.
- Search for user-defined keywords in web content.
- Respect robots.txt (with an option to ignore for testing purposes).
- Save results in JSON and CSV formats.
- User-friendly web interface built with Flask.
- Asynchronous scraping for improved performance.
- Logging for debugging and monitoring.

## Requirements

- Python 3.8 or higher
- Required Python packages (install via `pip`):
  ```
  flask requests beautifulsoup4 fake-useragent rich aiohttp
  ```
- Optional (for Playwright version to handle JavaScript-rendered content):
  ```
  playwright
  ```
  After installing Playwright, run:
  ```
  playwright install
  ```

## Installation

1. Clone or download the project files:
   ```
   git clone <repository-url>
   cd reconscraper
   ```
2. Install dependencies:
   ```
   pip install flask requests beautifulsoup4 fake-useragent rich aiohttp
   ```
3. Create the `results` directory for saving output files:
   ```
   mkdir results
   chmod -R 755 results
   ```

## Usage

### Via Web Interface
1. Ensure all files (`web_interface.py`, `recon_scraper.py`, `index.html`, `results.html`) are in the same directory.
2. Run the Flask app:
   ```
   python web_interface.py
   ```
3. Open a browser and navigate to `http://localhost:5000`.
4. Fill in the form:
   - **Target URL**: The website to scrape (e.g., `https://www.w3.org`).
   - **Keywords**: Keywords to search (e.g., `html, css`).
   - **Depth**: Crawling depth (e.g., `1`).
   - **Max URLs**: Maximum URLs to crawl (e.g., `10`).
   - **Ignore robots.txt**: Check to bypass robots.txt (use with caution).
5. Click "Lancer la reconnaissance" to start scraping.
6. View results in the table, download JSON/CSV files, or navigate to `/results` to see previous scans.

### Via Command Line
1. Run the scraper directly:
   ```
   python recon_scraper.py --url https://www.w3.org --keywords html css --depth 1 --max-urls 10 --ignore-robots
   ```
2. Results will be saved in the `results` directory as JSON and CSV files.

## Files

- `recon_scraper.py`: Core scraping logic.
- `web_interface.py`: Flask app for the web interface.
- `index.html`: Main page with the scraping form.
- `results.html`: Page to view and download previous results.
- `scraper.log`: Log file for debugging and monitoring.

## Troubleshooting

- **Flask App Hangs**:
  - Check for port conflicts (`lsof -i :5000`) and change the port if needed (e.g., `app.run(debug=True, host='0.0.0.0', port=5001)`).
  - Verify all dependencies are installed.
- **No Results**:
  - Ensure keywords match the site’s content (view source with Ctrl+U).
  - Check `scraper.log` for errors (e.g., HTTP 403/429).
  - Try checking "Ignore robots.txt" if blocked.
- **Download Fails**:
  - Verify the `results` directory contains the expected files.
  - Check `scraper.log` for file-saving errors.
- **Anti-Bot Measures**:
  - If the site uses Cloudflare or similar, use `recon_scraper_playwright.py` (requires Playwright installation).

## Example

### Web Interface
- URL: `https://www.w3.org`
- Keywords: `html`
- Depth: `1`
- Max URLs: `5`
- Ignore robots.txt: Checked
- Result: Table shows matches, and JSON/CSV files are downloadable.

### Command Line
```
python recon_scraper.py --url https://www.example.com --keywords example --depth 1 --max-urls 5
```
- Output: Files like `results/recon_www.example.com_YYYYMMDD-HHMMSS.json`.

## Ethical Guidelines

- **Obtain Permission**: Only scrape websites you own or have explicit permission to access.
- **Respect robots.txt**: Use the `--ignore-robots` flag only for educational testing on sites where you have permission.
- **Limit Impact**: Use low depth and max URLs to avoid overloading servers.
- **Protect Privacy**: Do not collect or store personal data without consent.

## License

This project is for educational use only and is not licensed for commercial purposes. Use at your own risk.

## Contact

For questions or issues, please open an issue on the project repository or contact the maintainers.

---

*Last Updated: May 04, 2025*