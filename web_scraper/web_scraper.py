import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import logging
import time
import random

# Configure logging (no sensitive data logged)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_robots_txt(url):
    """Check if scraping is allowed by parsing robots.txt."""
    robots_url = f"{url}/robots.txt"
    try:
        response = requests.get(robots_url)
        if "User-agent: *\nDisallow: /" in response.text:
            logging.warning("Scraping is disallowed by robots.txt")
            return False
        return True
    except requests.RequestException as e:
        logging.error(f"Failed to fetch robots.txt: {e}")
        return False

def setup_driver():
    """Set up Selenium WebDriver with headless Chrome and rotated user agents."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def fetch_page(driver, url):
    """Fetch the page using Selenium WebDriver."""
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))  # Random delay to mimic human behavior
        return driver.page_source
    except Exception as e:
        logging.error(f"Failed to fetch page: {e}")
        return None

def parse_jobs(html):
    """Parse job listings from HTML content using BeautifulSoup."""
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    job_listings = soup.select('div.cardOutline')
    for job in job_listings:
        try:
            title = job.select_one('a.jcs-JobTitle span').text
        except AttributeError:
            title = 'N/A'
        try:
            company = job.select_one('span.companyName').text
        except AttributeError:
            company = 'N/A'
        try:
            location = job.select_one('div.companyLocation').text
        except AttributeError:
            location = 'N/A'
        try:
            link = job.select_one('a.jcs-JobTitle')['href']
        except (AttributeError, KeyError):
            link = 'N/A'
        jobs.append({'title': title, 'company': company, 'location': location, 'link': link})
    return jobs

def handle_pagination(driver, base_url, pages=3):
    """Handle pagination and scrape multiple pages."""
    all_jobs = []
    for page in range(1, pages + 1):
        url = f"{base_url}&start={(page-1)*10}"
        logging.info(f"Scraping page {page}")
        html = fetch_page(driver, url)
        if html:
            jobs = parse_jobs(html)
            all_jobs.extend(jobs)
            time.sleep(random.uniform(1, 3))  # Delay between pages
    return all_jobs

def save_to_csv(jobs, filename='jobs.csv'):
    """Save scraped data to a CSV file."""
    df = pd.DataFrame(jobs)
    df.to_csv(filename, index=False)
    logging.info(f"Data saved to {filename}")

def main():
    base_url = 'https://www.indeed.com/jobs?q=software+engineer'
    if not check_robots_txt('https://www.indeed.com'):
        logging.error("Scraping not allowed by robots.txt. Exiting.")
        return
    
    logging.info(f"Starting scrape of {base_url}")
    driver = setup_driver()
    try:
        all_jobs = handle_pagination(driver, base_url, pages=3)
        if all_jobs:
            save_to_csv(all_jobs)
            logging.info(f"Scraped {len(all_jobs)} jobs")
        else:
            logging.warning("No jobs found")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()