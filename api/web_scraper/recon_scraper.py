
import argparse
import csv
import json
import os
import random
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

class ReconScraper:
    """
    Scraper web pour la phase de reconnaissance en cybersécurité.
    Permet de collecter des informations à partir d'un site web cible
    en recherchant des mots-clés spécifiques.
    """
    
    def __init__(self, target_url, keywords=None, depth=1, delay=1, output_dir="results"):
        """
        Initialise le scraper avec les paramètres de base.
        
        Args:
            target_url (str): URL cible à scraper
            keywords (list): Liste de mots-clés à rechercher
            depth (int): Profondeur de crawling (nombre de niveaux à traverser)
            delay (float): Délai entre les requêtes en secondes
            output_dir (str): Répertoire pour enregistrer les résultats
        """
        self.target_url = target_url
        self.keywords = keywords or []
        self.depth = depth
        self.delay = delay
        self.output_dir = output_dir
        self.visited_urls = set()
        self.results = []
        self.console = Console()
        
        # Vérifier et créer le répertoire de sortie
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Configurations pour éviter la détection
        self.user_agent = UserAgent()
        self.headers = {"User-Agent": self.user_agent.random}
        
        # Analyse de l'URL cible
        parsed_url = urlparse(target_url)
        self.base_domain = parsed_url.netloc
        self.scheme = parsed_url.scheme
        
    def _get_random_user_agent(self):
        """Retourne un User-Agent aléatoire pour éviter la détection."""
        return self.user_agent.random
    
    def _request_page(self, url):
        """
        Effectue une requête HTTP avec gestion des erreurs.
        
        Args:
            url (str): URL à requêter
            
        Returns:
            str: Contenu HTML de la page ou None en cas d'erreur
        """
        try:
            # Rotation du User-Agent pour éviter la détection
            self.headers["User-Agent"] = self._get_random_user_agent()
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.console.print(f"[bold red]Erreur lors de la requête à {url}: {e}[/bold red]")
            return None
        except Exception as e:
            self.console.print(f"[bold red]Erreur inattendue: {e}[/bold red]")
            return None
    
    def extract_links(self, html, current_url):
        """
        Extrait les liens d'une page HTML.
        
        Args:
            html (str): Contenu HTML
            current_url (str): URL actuelle pour résoudre les liens relatifs
            
        Returns:
            list: Liste des URLs trouvées
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Résoudre les URLs relatives
            full_url = urljoin(current_url, href)
            parsed_url = urlparse(full_url)
            
            # Ne garder que les liens du même domaine
            if parsed_url.netloc == self.base_domain:
                links.append(full_url)
                
        return list(set(links))  # Éliminer les doublons
    
    def search_keywords(self, html, url):
        """
        Recherche les mots-clés dans le contenu HTML.
        
        Args:
            html (str): Contenu HTML
            url (str): URL de la page
            
        Returns:
            list: Liste des correspondances trouvées
        """
        if not html or not self.keywords:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        # Obtenir le texte visible de la page
        text = soup.get_text()
        
        findings = []
        for keyword in self.keywords:
            # Recherche insensible à la casse
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            matches = pattern.findall(text)
            
            if matches:
                findings.append({
                    "keyword": keyword,
                    "occurrences": len(matches),
                    "contexts": self._get_contexts(text, keyword, 30)
                })
                
        # Collecter les emails
        emails = self._extract_emails(text)
        if emails:
            findings.append({
                "keyword": "EMAIL",
                "occurrences": len(emails),
                "contexts": emails
            })
            
        # Collecter les numéros de téléphone
        phones = self._extract_phones(text)
        if phones:
            findings.append({
                "keyword": "PHONE",
                "occurrences": len(phones),
                "contexts": phones
            })
        
        if findings:
            result = {
                "url": url,
                "title": self._get_page_title(soup),
                "findings": findings
            }
            self.results.append(result)
            return findings
        
        return []
    
    def _get_contexts(self, text, keyword, context_size=30):
        """
        Extrait le contexte autour des occurrences d'un mot-clé.
        
        Args:
            text (str): Texte complet
            keyword (str): Mot-clé à rechercher
            context_size (int): Nombre de caractères avant/après pour le contexte
            
        Returns:
            list: Liste des contextes trouvés (limités à 5 pour éviter les résultats trop volumineux)
        """
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        contexts = []
        
        for match in pattern.finditer(text):
            start = max(0, match.start() - context_size)
            end = min(len(text), match.end() + context_size)
            context = text[start:end].replace('\n', ' ').strip()
            contexts.append(f"...{context}...")
            
            # Limiter à 5 contextes par mot-clé
            if len(contexts) >= 5:
                break
                
        return contexts
    
    def _extract_emails(self, text):
        """Extrait les adresses e-mail du texte."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    def _extract_phones(self, text):
        """Extrait les numéros de téléphone du texte (format international)."""
        # Pattern simple pour les numéros internationaux
        phone_pattern = r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        return re.findall(phone_pattern, text)
    
    def _get_page_title(self, soup):
        """Extrait le titre de la page."""
        title_tag = soup.find('title')
        return title_tag.text if title_tag else "Sans titre"
        
    def crawl(self):
        """
        Lance le processus de crawling et de scraping.
        """
        # Affichage des informations de démarrage
        self.console.print(f"[bold green]╔══════════════════════════════════════╗[/bold green]")
        self.console.print(f"[bold green]║    RECONNAISSANCE SCRAPER ACTIF      ║[/bold green]")
        self.console.print(f"[bold green]╚══════════════════════════════════════╝[/bold green]")
        self.console.print(f"[bold blue]Target URL:[/bold blue] {self.target_url}")
        self.console.print(f"[bold blue]Keywords:[/bold blue] {', '.join(self.keywords) if self.keywords else 'Aucun'}")
        self.console.print(f"[bold blue]Depth:[/bold blue] {self.depth}")
        self.console.print()
        
        # Initialisation de la file de crawling
        to_crawl = [(self.target_url, 0)]  # (url, profondeur)
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Scraping en cours...", total=None)
            
            while to_crawl:
                current_url, current_depth = to_crawl.pop(0)
                
                # Vérifier si l'URL a déjà été visitée
                if current_url in self.visited_urls:
                    continue
                
                # Marquer comme visitée
                self.visited_urls.add(current_url)
                
                # Mise à jour de la progression
                progress.update(task, description=f"[cyan]Scraping de {current_url}[/cyan]")
                
                # Récupérer le contenu de la page
                html = self._request_page(current_url)
                if not html:
                    continue
                
                # Rechercher les mots-clés
                findings = self.search_keywords(html, current_url)
                if findings:
                    progress.console.print(f"[green]✓[/green] Trouvé {len(findings)} résultat(s) sur {current_url}")
                
                # Si on n'a pas atteint la profondeur maximale, extraire les liens
                if current_depth < self.depth:
                    links = self.extract_links(html, current_url)
                    
                    # Ajouter les nouveaux liens à la file d'attente
                    for link in links:
                        if link not in self.visited_urls:
                            to_crawl.append((link, current_depth + 1))
                
                # Délai pour éviter de surcharger le serveur
                time.sleep(self.delay)
        
        self.console.print(f"\n[bold green]Scraping terminé![/bold green]")
        self.console.print(f"[bold blue]URLs visitées:[/bold blue] {len(self.visited_urls)}")
        self.console.print(f"[bold blue]Résultats trouvés:[/bold blue] {len(self.results)}")
    
    def save_results(self):
        """
        Enregistre les résultats dans différents formats.
        """
        if not self.results:
            self.console.print("[yellow]Aucun résultat à enregistrer.[/yellow]")
            return
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_filename = f"recon_{urlparse(self.target_url).netloc}_{timestamp}"
        
        # Enregistrer en JSON
        json_path = os.path.join(self.output_dir, f"{base_filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        
        # Enregistrer en CSV (version simplifiée)
        csv_path = os.path.join(self.output_dir, f"{base_filename}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Titre', 'Mot-clé', 'Occurrences', 'Contexte'])
            
            for result in self.results:
                url = result['url']
                title = result['title']
                
                for finding in result['findings']:
                    keyword = finding['keyword']
                    occurrences = finding['occurrences']
                    
                    if 'contexts' in finding and finding['contexts']:
                        for context in finding['contexts']:
                            writer.writerow([url, title, keyword, occurrences, context])
                    else:
                        writer.writerow([url, title, keyword, occurrences, ''])
        
        self.console.print(f"[bold green]Résultats sauvegardés dans:[/bold green]")
        self.console.print(f"  - JSON: {json_path}")
        self.console.print(f"  - CSV: {csv_path}")
    
    def display_results(self):
        """
        Affiche un résumé des résultats.
        """
        if not self.results:
            self.console.print("[yellow]Aucun résultat à afficher.[/yellow]")
            return
        
        # Créer un tableau pour afficher les résultats
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("URL")
        table.add_column("Titre")
        table.add_column("Mot-clé")
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
        
        self.console.print("\n[bold]Résumé des résultats:[/bold]")
        self.console.print(table)

def main():
    parser = argparse.ArgumentParser(description='ReconScraper - Web Scraper pour la phase de reconnaissance')
    parser.add_argument('--url', '-u', required=True, help='URL cible à scraper')
    parser.add_argument('--keywords', '-k', nargs='+', help='Mots-clés à rechercher')
    parser.add_argument('--depth', '-d', type=int, default=1, help='Profondeur de crawling (défaut: 1)')
    parser.add_argument('--delay', type=float, default=1.0, help='Délai entre les requêtes en secondes (défaut: 1.0)')
    parser.add_argument('--output', '-o', default='results', help='Répertoire pour enregistrer les résultats (défaut: results)')
    
    args = parser.parse_args()
    
    scraper = ReconScraper(
        target_url=args.url,
        keywords=args.keywords,
        depth=args.depth,
        delay=args.delay,
        output_dir=args.output
    )
    
    try:
        scraper.crawl()
        scraper.display_results()
        scraper.save_results()
    except KeyboardInterrupt:
        print("\nOpération interrompue par l'utilisateur.")
        sys.exit(1)

if __name__ == '__main__':
    main()