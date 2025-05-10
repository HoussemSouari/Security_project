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

# Set absolute path for the upload folder
current_dir = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(current_dir, 'results')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Log the absolute path
logging.info(f"Upload folder absolute path: {app.config['UPLOAD_FOLDER']}")

# Create the results directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Create static directory if it doesn't exist
os.makedirs('static', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

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
            output_dir=app.config['UPLOAD_FOLDER'],  # Use the absolute path from app.config
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
        logging.info(f"Upload folder path: {app.config['UPLOAD_FOLDER']}")
        
        # Check if file exists in the configured upload folder
        direct_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logging.info(f"Full file path: {direct_path}")
        logging.info(f"File exists: {os.path.exists(direct_path)}")
        
        if os.path.exists(direct_path) and os.path.isfile(direct_path):
            logging.info(f"File found at path: {direct_path}")
            return flask.send_file(
                direct_path,
                as_attachment=True,
                download_name=filename
            )
        
        # If the file wasn't found in the configured path, try the root results folder
        project_root = os.path.dirname(current_dir)  # Go up one level from recon_scraper dir
        root_results_dir = os.path.join(project_root, 'results')
        alt_path = os.path.join(root_results_dir, filename)
        logging.info(f"Trying alternative path: {alt_path}")
        logging.info(f"Alternative path exists: {os.path.exists(alt_path)}")
        
        if os.path.exists(alt_path) and os.path.isfile(alt_path):
            logging.info(f"File found at alternative path: {alt_path}")
            return flask.send_file(
                alt_path,
                as_attachment=True,
                download_name=filename
            )
        
        # For debugging purposes, list all files in both directories
        logging.info("Listing all files in upload folder:")
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                logging.info(f"  - {f}")
        
        logging.info("Listing all files in root results folder:")
        if os.path.exists(root_results_dir):
            for f in os.listdir(root_results_dir):
                logging.info(f"  - {f}")
        
        # File not found in either location
        logging.error(f"File not found: {filename}")
        return jsonify({'error': f'File {filename} not found in either results folder'}), 404
        
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