"""
Web Crawler Application

This Flask application provides a web interface to run and configure web crawling operations
using the crawler.py script. It offers a simple way to visualize and interact with the 
web crawler functionality.
"""

import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Create necessary directories
os.makedirs('static/results', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Create a basic template if it doesn't exist
if not os.path.exists('templates/index.html'):
    with open('templates/index.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Crawler</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
</head>
<body>
    <div class="container mt-5">
        <h1 class="mb-4">Web Crawler</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <div class="card">
            <div class="card-header">
                <h5>Configure Crawler</h5>
            </div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('run_crawler') }}">
                    <div class="mb-3">
                        <label for="url" class="form-label">URL to Crawl</label>
                        <input type="url" class="form-control" id="url" name="url" required
                               placeholder="https://example.com">
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="depth" class="form-label">Crawl Depth</label>
                                <input type="number" class="form-control" id="depth" name="depth" 
                                       value="1" min="1" max="5">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="max_pages" class="form-label">Max Pages</label>
                                <input type="number" class="form-control" id="max_pages" name="max_pages" 
                                       value="10" min="1" max="100">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="format" class="form-label">Output Format</label>
                                <select class="form-select" id="format" name="format">
                                    <option value="json">JSON</option>
                                    <option value="markdown">Markdown</option>
                                    <option value="text">Text</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="extract_images" name="extract_images">
                            <label class="form-check-label" for="extract_images">
                                Extract Images
                            </label>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="extract_links" name="extract_links" checked>
                            <label class="form-check-label" for="extract_links">
                                Extract Links
                            </label>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Run Crawler</button>
                </form>
            </div>
        </div>

        {% if results %}
        <div class="card mt-4">
            <div class="card-header">
                <h5>Crawling Results</h5>
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between mb-3">
                    <span>{{ results.url }}</span>
                    <a href="{{ url_for('download_result', filename=results.filename) }}" class="btn btn-sm btn-success">
                        Download Results
                    </a>
                </div>
                <div class="results-preview">
                    {% if results.format == 'json' %}
                        <pre class="bg-dark text-light p-3">{{ results.preview }}</pre>
                    {% elif results.format == 'markdown' %}
                        <div class="bg-dark text-light p-3">{{ results.preview | safe }}</div>
                    {% else %}
                        <pre class="bg-dark text-light p-3">{{ results.preview }}</pre>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """)

@app.route('/')
def index():
    """Render the main page of the application."""
    return render_template('index.html')

@app.route('/run-crawler', methods=['POST'])
def run_crawler():
    """Run the crawler with the provided parameters."""
    try:
        # Extract form data
        url = request.form.get('url')
        depth = request.form.get('depth', 1)
        max_pages = request.form.get('max_pages', 10)
        output_format = request.form.get('format', 'json')
        extract_images = 'extract_images' in request.form
        extract_links = 'extract_links' in request.form
        
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"crawl_{timestamp}_{unique_id}.{output_format}"
        output_path = os.path.join('static', 'results', filename)
        
        # Build command to run crawler.py
        cmd = [
            sys.executable, 'crawler.py',
            '--url', url,
            '--depth', str(depth),
            '--max-pages', str(max_pages),
            '--format', output_format,
            '--output', output_path
        ]
        
        if extract_images:
            cmd.append('--extract-images')
        
        if extract_links:
            cmd.append('--extract-links')
        
        # Run the crawler process
        logger.info(f"Running crawler with command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        # Check if the crawler was successful
        if result.returncode != 0:
            logger.error(f"Crawler failed: {result.stderr}")
            flash(f"Crawler failed: {result.stderr}", "danger")
            return redirect(url_for('index'))
        
        # Read and prepare result preview
        preview = "No preview available"
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                if output_format == 'json':
                    data = json.load(f)
                    preview = json.dumps(data[:3] if isinstance(data, list) else data, indent=2)
                else:
                    # For text and markdown, just show the first 1000 chars
                    preview = f.read(1000)
                    if len(preview) >= 1000:
                        preview += "\n... (truncated)"
        
        # Pass results to template
        return render_template('index.html', results={
            'url': url,
            'filename': filename,
            'format': output_format,
            'preview': preview
        })
        
    except Exception as e:
        logger.exception("Error running crawler")
        flash(f"Error running crawler: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_result(filename):
    """Download a crawling result file."""
    return send_from_directory('static/results', filename, as_attachment=True)

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    """API endpoint to run the crawler and return results."""
    try:
        # Extract JSON request data
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
            
        url = data['url']
        depth = data.get('depth', 1)
        max_pages = data.get('max_pages', 10)
        output_format = data.get('format', 'json')
        extract_images = data.get('extract_images', False)
        extract_links = data.get('extract_links', True)
        
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as temp:
            output_path = temp.name
        
        # Build command
        cmd = [
            sys.executable, 'crawler.py',
            '--url', url,
            '--depth', str(depth),
            '--max-pages', str(max_pages),
            '--format', output_format,
            '--output', output_path
        ]
        
        if extract_images:
            cmd.append('--extract-images')
        
        if extract_links:
            cmd.append('--extract-links')
        
        # Run crawler
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        # Handle errors
        if result.returncode != 0:
            return jsonify({
                'error': 'Crawler process failed',
                'details': result.stderr
            }), 500
        
        # Read results
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                if output_format == 'json':
                    content = json.load(f)
                else:
                    content = f.read()
            
            # Clean up temporary file
            os.unlink(output_path)
            
            return jsonify({
                'url': url,
                'results': content,
                'format': output_format
            })
        else:
            return jsonify({
                'error': 'Output file not found',
                'details': 'The crawler did not produce any output'
            }), 500
            
    except Exception as e:
        logger.exception("API error running crawler")
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)