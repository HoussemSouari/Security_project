import argparse
import asyncio
import csv
import json
import logging
import os
import random
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

# Configure logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ReconScraper:
    """
    Web scraper for cybersecurity reconnaissance phase.
    Collects information from a target website by searching for specific keywords.
    Respects privacy and site restrictions.
    """
    
    def __init__(self, target_url, keywords=None, depth=1, output_dir="results", max_urls=100, ignore_robots=False):
        """
        Initialize the scraper with basic parameters.
        
        Args:
            target_url (str): Target URL to scrape
            keywords (list): List of keywords to search
            depth (int): Crawling depth
            output_dir (str): Directory to save results
            max_urls (int): Maximum number of URLs to crawl
            ignore_robots (bool): Ignore robots.txt for testing
        """
        self.target_url = target_url
        self.keywords = keywords or []
        self.depth = depth
        self.output_dir = output_dir
        self.max_urls = max_urls
        self.ignore_robots = ignore_robots
        self.visited_urls = set()
        self.results = []
        self.console = Console()
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Configurations to avoid detection
        self.user_agent = UserAgent()
        self.headers = {"User-Agent": self.user_agent.random}
        
        # Parse target URL
        parsed_url = urlparse(target_url)
        self.base_domain = parsed_url.netloc
        self.scheme = parsed_url.scheme
        
        # Initialize robots.txt parser
        self.robot_parser = RobotFileParser()
        if not ignore_robots:
            self._check_robots_txt()
        else:
            logging.info("Ignoring robots.txt as per configuration")

    def _check_robots_txt(self):
        """Check and parse robots.txt for the target site."""
        robots_url = f"{self.scheme}://{self.base_domain}/robots.txt"
        try:
            response = requests.get(robots_url, timeout=5)
            if response.status_code == 200:
                self.robot_parser.parse(response.text.splitlines())
                logging.info(f"Parsed robots.txt from {robots_url}")
            else:
                self.console.print(f"[yellow]No robots.txt found at {robots_url}[/yellow]")
                logging.warning(f"No robots.txt found at {robots_url}")
        except Exception as e:
            self.console.print(f"[yellow]Error accessing robots.txt: {e}[/yellow]")
            logging.error(f"Error accessing robots.txt: {e}")

    async def _request_page(self, url, session):
        """
        Perform an async HTTP request with error handling and retries.
        
        Args:
            url (str): URL to request
            session: aiohttp ClientSession
            
        Returns:
            str: HTML content or None if error
        """
        if not self.ignore_robots and not self.robot_parser.can_fetch(self.headers["User-Agent"], url):
            self.console.print(f"[yellow]URL {url} blocked by robots.txt[/yellow]")
            logging.info(f"Skipped {url} due to robots.txt")
            return None

        for attempt in range(3):  # Retry up to 3 times
            try:
                self.headers["User-Agent"] = self.user_agent.random
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        logging.info(f"Successfully fetched {url}")
                        return content
                    else:
                        self.console.print(f"[red]Error {response.status} for {url}[/red]")
                        logging.error(f"Error {response.status} for {url}")
                        return None
            except Exception as e:
                self.console.print(f"[red]Attempt {attempt+1} failed for {url}: {e}[/red]")
                logging.error(f"Attempt {attempt+1} failed for {url}: {e}")
                if attempt < 2:
                    await asyncio.sleep(random.uniform(1, 3))  # Wait before retry
        return None
    
    def extract_links(self, html, current_url):
        """
        Extract links from HTML content.
        
        Args:
            html (str): HTML content
            current_url (str): Current URL to resolve relative links
            
        Returns:
            list: List of found URLs
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)
            parsed_url = urlparse(full_url)
            
            if parsed_url.netloc == self.base_domain:
                links.append(full_url)
                
        links = list(set(links))
        logging.info(f"Extracted {len(links)} links from {current_url}")
        return links
    
    def search_keywords(self, html, url):
        """
        Search for keywords in HTML content.
        
        Args:
            html (str): HTML content
            url (str): Page URL
            
        Returns:
            list: List of findings
        """
        if not html or not self.keywords:
            logging.info(f"No HTML or keywords for {url}")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        findings = []
        for keyword in self.keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.findall(text)
            
            if matches:
                findings.append({
                    "keyword": keyword,
                    "occurrences": len(matches),
                    "contexts": self._get_contexts(text, keyword, 30)
                })
                logging.info(f"Found {len(matches)} occurrences of '{keyword}' on {url}")
        
        if findings:
            result = {
                "url": url,
                "title": self._get_page_title(soup),
                "findings": findings
            }
            self.results.append(result)
            return findings
        
        logging.info(f"No keyword matches found on {url}")
        return []
    
    def _get_contexts(self, text, keyword, context_size=30):
        """
        Extract context around keyword occurrences.
        
        Args:
            text (str): Full text
            keyword (str): Keyword to search
            context_size (int): Characters before/after for context
            
        Returns:
            list: List of contexts (limited to 5)
        """
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        contexts = []
        
        for match in pattern.finditer(text):
            start = max(0, match.start() - context_size)
            end = min(len(text), match.end() + context_size)
            context = text[start:end].replace('\n', ' ').strip()
            contexts.append(f"...{context}...")
            if len(contexts) >= 5:
                break
                
        return contexts
    
    def _get_page_title(self, soup):
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.text if title_tag else "No title"
        
    async def crawl(self):
        """
        Run the async crawling and scraping process.
        """
        self.console.print(f"[bold green]╔══════════════════════════════════════╗[/bold green]")
        self.console.print(f"[bold green]║    RECONNAISSANCE SCRAPER ACTIF      ║[/bold green]")
        self.console.print(f"[bold green]╚══════════════════════════════════════╝[/bold green]")
        self.console.print(f"[bold blue]Target URL:[/bold blue] {self.target_url}")
        self.console.print(f"[bold blue]Keywords:[/bold blue] {', '.join(self.keywords) if self.keywords else 'None'}")
        self.console.print(f"[bold blue]Depth:[/bold blue] {self.depth}")
        self.console.print(f"[bold blue]Max URLs:[/bold blue] {self.max_urls}")
        self.console.print()
        
        to_crawl = [(self.target_url, 0)]  # (url, depth)
        
        async with aiohttp.ClientSession() as session:
            with Progress() as progress:
                task = progress.add_task("[cyan]Scraping...", total=None)
                
                while to_crawl and len(self.visited_urls) < self.max_urls:
                    current_url, current_depth = to_crawl.pop(0)
                    
                    if current_url in self.visited_urls:
                        continue
                    
                    self.visited_urls.add(current_url)
                    progress.update(task, description=f"[cyan]Scraping {current_url}[/cyan]")
                    
                    html = await self._request_page(current_url, session)
                    if not html:
                        continue
                    
                    findings = self.search_keywords(html, current_url)
                    if findings:
                        progress.console.print(f"[green]✓[/green] Found {len(findings)} result(s) on {current_url}")
                    
                    if current_depth < self.depth:
                        links = self.extract_links(html, current_url)
                        for link in links:
                            if link not in self.visited_urls:
                                to_crawl.append((link, current_depth + 1))
                    
                    await asyncio.sleep(random.uniform(0.5, 1.5))
        
        self.console.print(f"\n[bold green]Scraping completed![/bold green]")
        self.console.print(f"[bold blue]URLs visited:[/bold blue] {len(self.visited_urls)}")
        self.console.print(f"[bold blue]Results found:[/bold blue] {len(self.results)}")
        logging.info(f"Scraping completed: {len(self.visited_urls)} URLs visited, {len(self.results)} results found")
    
    def save_results(self):
        """
        Save results in JSON and CSV formats.
        """
        if not self.results:
            self.console.print("[yellow]No results to save.[/yellow]")
            logging.warning("No results to save")
            return
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_filename = f"recon_{urlparse(self.target_url).netloc}_{timestamp}"
        
        json_path = os.path.join(self.output_dir, f"{base_filename}.json")
        csv_path = os.path.join(self.output_dir, f"{base_filename}.csv")
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=4)
            logging.info(f"Successfully saved JSON to {json_path}")
        except Exception as e:
            self.console.print(f"[red]Failed to save JSON: {e}[/red]")
            logging.error(f"Failed to save JSON to {json_path}: {e}")
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Title', 'Keyword', 'Occurrences', 'Context'])
                
                for result in self.results:
                    url = result['url']
                    title = result['title']
                    
                    for finding in result['findings']:
                        keyword = finding['keyword']
                        occurrences = finding['occurrences']
                        contexts = finding.get('contexts', [])
                        for context in contexts:
                            writer.writerow([url, title, keyword, occurrences, context])
            logging.info(f"Successfully saved CSV to {csv_path}")
        except Exception as e:
            self.console.print(f"[red]Failed to save CSV: {e}[/red]")
            logging.error(f"Failed to save CSV to {csv_path}: {e}")
        
        self.console.print(f"[bold green]Results saved to:[/bold green]")
        self.console.print(f"  - JSON: {json_path}")
        self.console.print(f"  - CSV: {csv_path}")
    
    def display_results(self):
        """
        Display a summary of results.
        """
        if not self.results:
            self.console.print("[yellow]No results to display.[/yellow]")
            logging.warning("No results to display")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("URL")
        table.add_column("Title")
        table.add_column("Keyword")
        table.add_column("Occurrences", justify="right")
        
        for result in self.results:
            url = result['url']
            title = result['title']
            
            for finding in result['findings']:
                keyword = finding['keyword']
                occurrences = finding['occurrences']
                
                table.add_row(
                    url if url else "N/A",
                    title if title else "N/A",
                    keyword if keyword else "N/A",
                    str(occurrences)
                )
        
        self.console.print("\n[bold]Results Summary:[/bold]")
        self.console.print(table)

def main():
    parser = argparse.ArgumentParser(description='ReconScraper - Ethical Web Scraper for Reconnaissance')
    parser.add_argument('--url', '-u', required=True, help='Target URL to scrape')
    parser.add_argument('--keywords', '-k', nargs='+', help='Keywords to search')
    parser.add_argument('--depth', '-d', type=int, default=1, help='Crawling depth (default: 1)')
    parser.add_argument('--output', '-o', default='results', help='Output directory (default: results)')
    parser.add_argument('--max-urls', type=int, default=100, help='Maximum URLs to crawl (default: 100)')
    parser.add_argument('--ignore-robots', action='store_true', help='Ignore robots.txt for testing')
    
    args = parser.parse_args()
    
    scraper = ReconScraper(
        target_url=args.url,
        keywords=args.keywords,
        depth=args.depth,
        output_dir=args.output,
        max_urls=args.max_urls,
        ignore_robots=args.ignore_robots
    )
    
    try:
        asyncio.run(scraper.crawl())
        scraper.display_results()
        scraper.save_results()
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        logging.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        print(f"Scraping failed: {e}")

if __name__ == '__main__':
    import requests
    import sys
    main()