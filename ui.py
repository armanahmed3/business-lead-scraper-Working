"""
Flask web UI for business lead scraper.

Beautiful, production-ready interface with real-time progress tracking.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
from datetime import datetime
from pathlib import Path
import logging

from selenium_scraper import SeleniumScraper
from exporter import DataExporter
from dedupe import Deduplicator
from config import Config

app = Flask(__name__)
CORS(app)

# Global variable to track scraping status
scraping_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'results': None,
    'error': None
}

@app.route('/')
def index():
    """Render main page with beautiful UI."""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Lead Scraper - Powered by Selenium</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            width: 100%;
            max-width: 900px;
            background: white;
            border-radius: 20px;
            padding: 50px;
            box-shadow: 0 30px 90px rgba(0, 0, 0, 0.3);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            color: #333;
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header .subtitle {
            color: #666;
            font-size: 16px;
            margin-top: 10px;
        }
        
        .header .icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin: 25px 0;
        }
        
        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #444;
            font-size: 15px;
        }
        
        input[type="text"],
        input[type="number"] {
            width: 100%;
            padding: 15px;
            font-size: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        input[type="text"]:focus,
        input[type="number"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }
        
        .example {
            font-size: 13px;
            color: #999;
            margin-top: 8px;
            font-style: italic;
        }
        
        .checkbox-group {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .checkbox-item input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .checkbox-item label {
            margin: 0;
            cursor: pointer;
            font-weight: 500;
        }
        
        button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 18px;
            font-weight: 600;
            transition: all 0.3s;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            margin-top: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            display: none;
        }
        
        .status.show {
            display: block;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .status h3 {
            margin-bottom: 20px;
            color: #333;
            font-size: 20px;
        }
        
        .progress-bar {
            width: 100%;
            height: 40px;
            background: #e0e0e0;
            border-radius: 20px;
            overflow: hidden;
            margin: 20px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
        }
        
        .message {
            padding: 18px;
            border-radius: 10px;
            margin: 15px 0;
            font-size: 15px;
            animation: slideIn 0.3s;
        }
        
        @keyframes slideIn {
            from { transform: translateX(-10px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #f5c6cb;
        }
        
        .message.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 2px solid #bee5eb;
        }
        
        .results {
            margin-top: 25px;
            padding: 25px;
            background: white;
            border-radius: 12px;
            border: 2px solid #e0e0e0;
        }
        
        .results h4 {
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .results p {
            color: #666;
            margin: 10px 0;
            font-size: 15px;
        }
        
        .download-links {
            margin-top: 25px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .download-links a {
            flex: 1;
            min-width: 150px;
            padding: 15px 25px;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            text-align: center;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
        }
        
        .download-links a:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(40, 167, 69, 0.4);
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 30px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            color: white;
            text-align: center;
        }
        
        .stat-card .label {
            font-size: 13px;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        
        .stat-card .value {
            font-size: 32px;
            font-weight: 700;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 13px;
        }
        
        .required {
            color: red;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">🔍</div>
            <h1>Business Lead Scraper</h1>
            <p class="subtitle">Powered by Selenium - Extract business leads from Google Maps</p>
        </div>
        
        <div>
            <div class="form-group">
                <label for="query">Business Type <span class="required">*</span></label>
                <input type="text" id="query" placeholder="e.g., dentist, coffee shop, restaurant" required>
                <div class="example">Examples: "restaurants", "hotels", "dentists", "gyms", "salons"</div>
            </div>
            
            <div class="form-group">
                <label for="location">Location <span class="required">*</span></label>
                <input type="text" id="location" placeholder="e.g., Birmingham, Alabama, US" required>
                <div class="example">Format: City, State/Province, Country</div>
            </div>
            
            <div class="form-group">
                <label for="max">Maximum Results</label>
                <input type="number" id="max" value="50" min="1" max="500">
                <div class="example">Recommended: 10-100 for faster results</div>
            </div>
            
            <div class="form-group">
                <label>Export Formats</label>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="csv" value="csv" checked>
                        <label for="csv">CSV</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="json" value="json" checked>
                        <label for="json">JSON</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="sqlite" value="sqlite" checked>
                        <label for="sqlite">SQLite</label>
                    </div>
                </div>
            </div>
            
            <button type="button" id="submitBtn">🚀 Start Scraping</button>
        </div>
        
        <div id="status" class="status">
            <h3>Scraping Status</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%;">0%</div>
            </div>
            <div id="messageContainer"></div>
            <div id="resultsContainer"></div>
        </div>
        
        <div class="footer">
            © 2025 Business Lead Scraper | For educational purposes only
        </div>
    </div>

    <script>
        const statusDiv = document.getElementById('status');
        const progressFill = document.getElementById('progressFill');
        const messageContainer = document.getElementById('messageContainer');
        const resultsContainer = document.getElementById('resultsContainer');
        const submitBtn = document.getElementById('submitBtn');

        submitBtn.addEventListener('click', startScraping);

        async function startScraping() {
            console.log('Starting scraping...');
            
            const query = document.getElementById('query').value.trim();
            const location = document.getElementById('location').value.trim();
            const max = parseInt(document.getElementById('max').value);
            
            if (!query) {
                alert('Please enter a business type!');
                return;
            }
            
            if (!location) {
                alert('Please enter a location!');
                return;
            }
            
            const formats = [];
            if (document.getElementById('csv').checked) formats.push('csv');
            if (document.getElementById('json').checked) formats.push('json');
            if (document.getElementById('sqlite').checked) formats.push('sqlite');
            
            if (formats.length === 0) {
                alert('Please select at least one export format!');
                return;
            }
            
            console.log('Data:', {query, location, max, formats});
            
            statusDiv.classList.add('show');
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Scraping in progress...';
            
            messageContainer.innerHTML = '<div class="spinner"></div><p style="text-align: center; color: #666; margin-top: 20px;">Initializing Chrome browser...</p>';
            resultsContainer.innerHTML = '';
            progressFill.style.width = '5%';
            progressFill.textContent = '5%';
            
            try {
                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query, location, max, formats})
                });
                
                const result = await response.json();
                console.log('Response:', result);
                
                if (result.status === 'started') {
                    pollProgress();
                } else {
                    showError(result.message || 'Failed to start scraping');
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 Start Scraping';
                }
                
            } catch (error) {
                console.error('Error:', error);
                showError('Network error: ' + error.message);
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Start Scraping';
            }
        }

        async function pollProgress() {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch('/status');
                    const status = await response.json();
                    
                    progressFill.style.width = status.progress + '%';
                    progressFill.textContent = status.progress + '%';
                    
                    if (status.message) {
                        messageContainer.innerHTML = '<div class="message info">📊 ' + status.message + '</div>';
                    }
                    
                    if (!status.running) {
                        clearInterval(interval);
                        
                        if (status.error) {
                            showError(status.error);
                        } else if (status.results) {
                            showResults(status.results);
                        }
                        
                        submitBtn.disabled = false;
                        submitBtn.textContent = '🚀 Start Scraping';
                    }
                    
                } catch (error) {
                    clearInterval(interval);
                    showError('Error: ' + error.message);
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 Start Scraping';
                }
            }, 2000);
        }

        function showResults(results) {
            progressFill.style.width = '100%';
            progressFill.textContent = '100% Complete ✓';
            
            messageContainer.innerHTML = '<div class="message success">✓ Scraping completed successfully!</div>';
            
            let html = '<div class="results">';
            html += '<h4>📊 Results Summary</h4>';
            html += '<div class="stats-grid">';
            html += '<div class="stat-card"><div class="label">Total Leads</div><div class="value">' + results.count + '</div></div>';
            html += '<div class="stat-card"><div class="label">Unique Leads</div><div class="value">' + results.unique + '</div></div>';
            html += '<div class="stat-card"><div class="label">Time Taken</div><div class="value">' + results.duration + '</div></div>';
            html += '</div>';
            
            if (results.files && results.files.length > 0) {
                html += '<div class="download-links">';
                results.files.forEach(file => {
                    const parts = file.replace(/\\\\/g, '/').split('/');
                    const filename = parts[parts.length - 1];
                    const ext = filename.split('.').pop().toUpperCase();
                    html += '<a href="/download/' + filename + '" download>📥 Download ' + ext + '</a>';
                });
                html += '</div>';
            }
            
            html += '</div>';
            resultsContainer.innerHTML = html;
        }

        function showError(message) {
            messageContainer.innerHTML = '<div class="message error">✗ ' + message + '</div>';
            progressFill.style.width = '0%';
            progressFill.textContent = 'Error';
        }
        
        console.log('UI initialized');
    </script>
</body>
</html>
    '''

@app.route('/scrape', methods=['POST'])
def scrape():
    """Start scraping in background thread."""
    global scraping_status
    
    if scraping_status['running']:
        return jsonify({
            'status': 'error',
            'message': 'Scraping already in progress'
        }), 400
    
    data = request.json
    query = data.get('query')
    location = data.get('location')
    max_results = int(data.get('max', 50))
    formats = data.get('formats', ['csv', 'json', 'sqlite'])
    
    scraping_status = {
        'running': True,
        'progress': 0,
        'message': 'Starting scraper...',
        'results': None,
        'error': None
    }
    
    thread = threading.Thread(
        target=run_scraper,
        args=(query, location, max_results, formats)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': f'Scraping {query} in {location}'
    })

@app.route('/status')
def status():
    """Get current scraping status."""
    return jsonify(scraping_status)

@app.route('/download/<filename>')
def download(filename):
    """Download result file."""
    file_path = Path('data') / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

def run_scraper(query, location, max_results, formats):
    """Run the scraper (background task)."""
    global scraping_status
    
    try:
        start_time = datetime.now()
        
        scraping_status['message'] = 'Initializing Chrome browser...'
        scraping_status['progress'] = 10
        
        config = Config()
        
        scraper = SeleniumScraper(
            config=config,
            headless=False,
            guest_mode=True,
            delay=1.5
        )
        
        scraping_status['message'] = f'Searching Google Maps for "{query}" in {location}...'
        scraping_status['progress'] = 20
        
        leads = scraper.scrape_google_maps(
            query=query,
            location=location,
            max_results=max_results
        )
        
        scraper.close()
        
        scraping_status['message'] = 'Deduplicating results...'
        scraping_status['progress'] = 70
        
        deduplicator = Deduplicator(config)
        unique_leads = deduplicator.deduplicate(leads)
        
        scraping_status['message'] = 'Exporting data...'
        scraping_status['progress'] = 85
        
        exporter = DataExporter(config, output_dir='./data')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"leads_{timestamp}"
        
        exported_files = exporter.export(
            data=unique_leads,
            formats=formats,
            filename=base_filename
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        scraping_status['running'] = False
        scraping_status['progress'] = 100
        scraping_status['message'] = 'Scraping completed!'
        scraping_status['results'] = {
            'count': len(leads),
            'unique': len(unique_leads),
            'duration': f'{duration:.1f}s',
            'files': exported_files
        }
        
    except Exception as e:
        logging.error(f"Scraping error: {e}", exc_info=True)
        scraping_status['running'] = False
        scraping_status['error'] = str(e)
        scraping_status['progress'] = 0

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Business Lead Scraper Web UI")
    print("=" * 70)
    print("\n📱 Open your browser to: http://localhost:5000")
    print("\n✓ All CSS styles loaded")
    print("✓ No page refresh issue")
    print("✓ Email extraction enabled")
    print("✓ Beautiful gradient purple UI")
    print("=" * 70)
    print()
    app.run(debug=True, port=5000, use_reloader=False)
