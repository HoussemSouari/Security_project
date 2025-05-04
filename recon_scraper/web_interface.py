import asyncio
import json
import os
import time
import logging
from urllib.parse import urlparse

import flask
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Import the updated ReconScraper
from recon_scraper import ReconScraper

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create the results directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    logging.info("Serving index page")
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    logging.info("Received scrape request")
    data = request.json
    target_url = data.get('url')
    keywords = data.get('keywords', '').split(',')
    depth = int(data.get('depth', 1))
    max_urls = int(data.get('max_urls', 100))
    ignore_robots = data.get('ignore_robots', False)
    
    if not target_url:
        logging.error("Target URL required")
        return jsonify({'error': 'Target URL required', 'log': 'Check scraper.log for details'}), 400
    
    keywords = [k.strip() for k in keywords if k.strip()]
    
    try:
        logging.info(f"Initializing scraper for {target_url}")
        scraper = ReconScraper(
            target_url=target_url,
            keywords=keywords,
            depth=depth,
            output_dir=app.config['UPLOAD_FOLDER'],
            max_urls=max_urls,
            ignore_robots=ignore_robots
        )
        
        logging.info("Running scraper crawl")
        asyncio.run(scraper.crawl())
        
        logging.info("Saving scraper results")
        scraper.save_results()
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_filename = f"recon_{urlparse(target_url).netloc}_{timestamp}"
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_filename}.json")
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_filename}.csv")
        
        results = []
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            logging.warning(f"JSON file not found: {json_path}")
        
        logging.info(f"Scrape completed with {len(scraper.results)} results")
        return jsonify({
            'status': 'success',
            'message': f'Scraping completed with {len(scraper.results)} results',
            'visitedUrls': len(scraper.visited_urls),
            'results': results,
            'files': {
                'json': f"{base_filename}.json" if os.path.exists(json_path) else '',
                'csv': f"{base_filename}.csv" if os.path.exists(csv_path) else ''
            },
            'log': 'Check scraper.log for detailed request and error information'
        })
        
    except Exception as e:
        logging.error(f"Scrape failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Scraping failed: {str(e)}',
            'log': 'Check scraper.log for detailed error information'
        }), 500

@app.route('/downloads/<path:filename>')
def download_file(filename):
    try:
        logging.info(f"Attempting to serve file download: {filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return jsonify({'error': f'File {filename} not found'}), 404
        logging.info(f"Serving file: {file_path}")
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            filename, 
            as_attachment=True
        )
    except FileNotFoundError:
        logging.error(f"File not found error for: {filename}")
        return jsonify({'error': f'File {filename} not found'}), 404
    except Exception as e:
        logging.error(f"Download failed: {str(e)}", exc_info=True)
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/results')
def list_results():
    logging.info("Serving results page")
    files = []
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        if file.endswith('.json') or file.endswith('.csv'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            files.append({
                'name': file,
                'path': f"/downloads/{file}",
                'size': os.path.getsize(file_path),
                'date': time.ctime(os.path.getctime(file_path))
            })
    
    return render_template('results.html', files=files)

if __name__ == '__main__':
    logging.info("Starting Flask app")
    app.run(debug=True, host='0.0.0.0', port=5000)