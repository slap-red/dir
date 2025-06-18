# web_app.py - Flask Web Interface for Slap Red Scraper v0.5.4
from flask import Flask, request, jsonify, render_template_string, flash, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import configparser
import threading
import asyncio
import os
import sys
import json
from datetime import datetime
import glob

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Global status tracking
scraper_status = {
    "message": "Idle", 
    "progress": 0, 
    "total": 0, 
    "is_running": False,
    "start_time": None,
    "last_update": None
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Enhanced HTML templates
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slap Red Scraper - Login</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; background: #f5f5f5; }
        .login-card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; }
        button:hover { background: #0056b3; }
        .error { color: #dc3545; margin-top: 10px; padding: 10px; background: #f8d7da; border-radius: 4px; }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .version { text-align: center; color: #666; font-size: 14px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>Slap Red Scraper</h1>
        <div class="version">v0.5.4</div>
        <form method="post">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="error">{{ messages[0] }}</div>
                {% endif %}
            {% endwith %}
        </form>
    </div>
</body>
</html>
"""

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slap Red Scraper v0.5.4</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-bar { padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .status-idle { background: #e3f2fd; border-left: 4px solid #2196f3; }
        .status-running { background: #fff3e0; border-left: 4px solid #ff9800; }
        .status-completed { background: #e8f5e8; border-left: 4px solid #4caf50; }
        .status-error { background: #ffebee; border-left: 4px solid #f44336; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="file"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; background: #4caf50; transition: width 0.3s ease; }
        .logout { float: right; background: #dc3545; }
        .logout:hover { background: #c82333; }
        .file-list { max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 4px; }
        .file-item { padding: 5px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .download-btn { background: #28a745; padding: 5px 10px; font-size: 12px; }
        .download-btn:hover { background: #218838; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .feature { padding: 15px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid #007bff; }
        .feature h4 { margin: 0 0 10px 0; color: #007bff; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px; }
        .stat-number { font-size: 24px; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Slap Red Scraper v0.5.4</h1>
        <p>Professional-grade data intelligence tool for promotional bonus analysis</p>
        <a href="/logout" class="logout button">Logout</a>
        <div style="clear: both;"></div>
    </div>

    <div class="status-bar status-{{ status.css_class }}">
        <h3>Status: {{ status.message }}</h3>
        {% if status.progress > 0 %}
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ (status.progress / status.total * 100) if status.total > 0 else 0 }}%"></div>
            </div>
            <p>Progress: {{ status.progress }} / {{ status.total }} URLs processed 
               ({{ "%.1f"|format((status.progress / status.total * 100) if status.total > 0 else 0) }}%)</p>
        {% endif %}
        {% if status.start_time %}
            <p><strong>Started:</strong> {{ status.start_time }}</p>
        {% endif %}
        {% if status.last_update %}
            <p><strong>Last Update:</strong> {{ status.last_update }}</p>
        {% endif %}
    </div>

    {% if not status.is_running %}
    <div class="card">
        <h2>📊 Quick Stats</h2>
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{{ output_files|length }}</div>
                <div class="stat-label">Output Files</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ status.total }}</div>
                <div class="stat-label">Last Run URLs</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ status.progress }}</div>
                <div class="stat-label">URLs Processed</div>
            </div>
        </div>
    </div>
    {% endif %}

    <div class="card">
        <h2>🚀 Run Scraper</h2>
        <form method="post" enctype="multipart/form-data" action="/run_scraper" id="scraperForm">
            <div class="form-group">
                <label for="url_file">📁 Upload URLs file (one URL per line):</label>
                <input type="file" id="url_file" name="url_file" accept=".txt,.csv" required>
                <small style="color: #666;">Supported formats: .txt, .csv</small>
            </div>
            <button type="submit" id="runBtn" {{ 'disabled' if status.is_running else '' }}>
                {{ '⏳ Running...' if status.is_running else '▶️ Run Scraper' }}
            </button>
        </form>
    </div>

    <div class="card">
        <h2>📁 Output Files</h2>
        <div class="file-list">
            {% for file in output_files %}
                <div class="file-item">
                    <span><strong>{{ file.name }}</strong> ({{ file.size }})</span>
                    <a href="/download/{{ file.name }}" class="download-btn button">⬇️ Download</a>
                </div>
            {% else %}
                <p style="text-align: center; color: #666; padding: 20px;">
                    📄 No output files available yet. Run the scraper to generate data files.
                </p>
            {% endfor %}
        </div>
    </div>

    <div class="card">
        <h2>✨ Key Features</h2>
        <div class="features">
            <div class="feature">
                <h4>🔄 Automated Scraping</h4>
                <p>Process hundreds of URLs with robust error handling and session management.</p>
            </div>
            <div class="feature">
                <h4>📈 Historical Analysis</h4>
                <p>Time-series analysis with daily comparison reports and Excel archiving.</p>
            </div>
            <div class="feature">
                <h4>🎯 Smart Categorization</h4>
                <p>Advanced analysis of bonus attributes and claim configurations.</p>
            </div>
            <div class="feature">
                <h4>📊 Multiple Outputs</h4>
                <p>CSV files, Excel workbooks, and JSON logs for comprehensive data analysis.</p>
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh status every 3 seconds when running
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    if (data.is_running) {
                        setTimeout(updateStatus, 3000);
                        // Refresh page if status changed significantly
                        if (window.lastProgress !== data.progress) {
                            window.lastProgress = data.progress;
                            location.reload();
                        }
                    }
                })
                .catch(error => console.log('Status update failed:', error));
        }

        // Start status updates if scraper is running
        if ({{ 'true' if status.is_running else 'false' }}) {
            updateStatus();
        }

        // Handle form submission
        document.getElementById('scraperForm').addEventListener('submit', function(e) {
            const fileInput = document.getElementById('url_file');
            if (!fileInput.files.length) {
                e.preventDefault();
                alert('Please select a file to upload.');
                return;
            }
            
            document.getElementById('runBtn').disabled = true;
            document.getElementById('runBtn').innerHTML = '⏳ Starting...';
        });

        // File input validation
        document.getElementById('url_file').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const validTypes = ['text/plain', 'text/csv', 'application/csv'];
                if (!validTypes.includes(file.type) && !file.name.endsWith('.txt') && !file.name.endsWith('.csv')) {
                    alert('Please select a valid text or CSV file.');
                    e.target.value = '';
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login for the web interface."""
    if request.method == 'POST':
        try:
            config = configparser.ConfigParser()
            config.read('In/config.ini')
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Check credentials from config
            config_username = config.get('credentials', 'mobile', fallback='admin')
            config_password = config.get('credentials', 'password', fallback='password')
            
            if username == config_username and password == config_password:
                user = User(username)
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials. Please check your username and password.', 'error')
        except Exception as e:
            flash(f'Configuration error: {str(e)}', 'error')
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

def get_output_files():
    """Get list of output files with metadata."""
    files = []
    patterns = ['*.csv', '*.xlsx', '*.json', '*.log']
    
    # Check current directory
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                size_str = format_file_size(size)
                files.append({
                    'name': os.path.basename(filepath),
                    'size': size_str,
                    'path': filepath
                })
    
    # Check common output directories
    for directory in ['data', 'out', 'logs', 'cache']:
        if os.path.exists(directory):
            for pattern in patterns:
                for filepath in glob.glob(f'{directory}/{pattern}'):
                    if os.path.isfile(filepath):
                        size = os.path.getsize(filepath)
                        size_str = format_file_size(size)
                        files.append({
                            'name': os.path.basename(filepath),
                            'size': size_str,
                            'path': filepath
                        })
    
    return sorted(files, key=lambda x: x['name'])

def format_file_size(size):
    """Format file size in human readable format."""
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.1f} MB"
    else:
        return f"{size/(1024*1024*1024):.1f} GB"

@app.route('/')
@login_required
def index():
    """Renders the main scraper interface."""
    # Determine CSS class for status
    css_class = 'idle'
    if scraper_status['is_running']:
        css_class = 'running'
    elif scraper_status['message'].startswith('Error'):
        css_class = 'error'
    elif scraper_status['message'] == 'Completed':
        css_class = 'completed'
    
    scraper_status['css_class'] = css_class
    output_files = get_output_files()
    
    return render_template_string(INDEX_HTML, status=scraper_status, output_files=output_files)

@app.route('/run_scraper', methods=['POST'])
@login_required
def run_scraper_route():
    """Initiates a batch scraping job with an uploaded URL file."""
    if scraper_status['is_running']:
        flash('Scraper is already running. Please wait for it to complete.', 'error')
        return redirect(url_for('index'))
    
    url_file = request.files.get('url_file')
    if not url_file or url_file.filename == '':
        flash('No file uploaded. Please select a file.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Read and validate URLs
        content = url_file.read().decode('utf-8')
        urls = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith('#')]
        
        if not urls:
            flash('No valid URLs found in file. Please check the file format.', 'error')
            return redirect(url_for('index'))
        
        # Create necessary directories
        os.makedirs('temp', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        
        # Save URLs to file
        urls_file_path = 'temp/uploaded_urls.txt'
        with open(urls_file_path, 'w') as f:
            f.write('\n'.join(urls))
        
        # Update status
        scraper_status.update({
            "message": "Starting...",
            "progress": 0,
            "total": len(urls),
            "is_running": True,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        def run():
            try:
                scraper_status.update({
                    "message": "Running",
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Simulate scraper process (replace with actual scraper call)
                import time
                for i in range(len(urls)):
                    time.sleep(2)  # Simulate processing time
                    scraper_status.update({
                        "progress": i + 1,
                        "message": f"Processing URL {i + 1} of {len(urls)}",
                        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                # Create sample output file
                output_file = f"data/bonuses_{datetime.now().strftime('%Y-%m-%d')}.csv"
                with open(output_file, 'w') as f:
                    f.write("url,bonus_count,status,timestamp\n")
                    for i, url in enumerate(urls):
                        f.write(f"{url},{i % 5 + 1},success,{datetime.now().isoformat()}\n")
                
                scraper_status.update({
                    "message": "Completed",
                    "is_running": False,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
            except Exception as e:
                scraper_status.update({
                    "message": f"Error: {str(e)}",
                    "is_running": False,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Start scraper in background thread
        threading.Thread(target=run, daemon=True).start()
        flash(f'Scraper started successfully with {len(urls)} URLs!', 'success')
        
    except Exception as e:
        scraper_status.update({
            "message": f"Error: {str(e)}",
            "is_running": False,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        flash(f'Error starting scraper: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/status')
@login_required
def status():
    """Returns the current scraper status as JSON."""
    return jsonify(scraper_status)

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download output files."""
    # Security: only allow downloading from safe locations
    safe_paths = ['.', 'data', 'out', 'logs', 'cache', 'temp']
    
    for path in safe_paths:
        filepath = os.path.join(path, filename)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            return send_file(filepath, as_attachment=True)
    
    flash('File not found or access denied.', 'error')
    return redirect(url_for('index'))

@app.route('/api/files')
@login_required
def api_files():
    """API endpoint to get list of output files."""
    return jsonify(get_output_files())

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('cache', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    
    print("🚀 Starting Slap Red Scraper Web Interface v0.5.4")
    print("📍 Access the application at: http://localhost:12000")
    print("🔐 Use credentials from In/config.ini to login")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=12000, debug=True)