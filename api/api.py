
import json
import os
import time
from urllib.parse import urlparse

import flask
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Importer notre module ReconScraper
from web_scraper.recon_scraper import ReconScraper

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite à 16MB

# Créer le répertoire de résultats s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    data = request.json
    target_url = data.get('url')
    keywords = data.get('keywords', '').split(',')
    depth = int(data.get('depth', 1))
    delay = float(data.get('delay', 1.0))
    
    # Validation de base
    if not target_url:
        return jsonify({'error': 'URL cible requise'}), 400
    
    # Nettoyage des mots-clés
    keywords = [k.strip() for k in keywords if k.strip()]
    
    try:
        # Initialiser le scraper
        scraper = ReconScraper(
            target_url=target_url,
            keywords=keywords,
            depth=depth,
            delay=delay,
            output_dir=app.config['UPLOAD_FOLDER']
        )
        
        # Lancer le scraping
        scraper.crawl()
        
        # Sauvegarder les résultats
        scraper.save_results()
        
        # Préparer la réponse
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_filename = f"recon_{urlparse(target_url).netloc}_{timestamp}"
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_filename}.json")
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_filename}.csv")
        
        # Lire les résultats JSON pour l'interface
        with open(json_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        return jsonify({
            'status': 'success',
            'message': f'Scraping terminé avec {len(scraper.results)} résultats',
            'visitedUrls': len(scraper.visited_urls),
            'results': results,
            'files': {
                'json': f"{base_filename}.json",
                'csv': f"{base_filename}.csv"
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True
    )

@app.route('/results')
def list_results():
    files = []
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        if file.endswith('.json') or file.endswith('.csv'):
            files.append({
                'name': file,
                'path': f"/downloads/{file}",
                'size': os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], file)),
                'date': time.ctime(os.path.getctime(os.path.join(app.config['UPLOAD_FOLDER'], file)))
            })
    
    return render_template('results.html', files=files)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)