# app.py
from flask import Flask, request, jsonify, render_template_string, flash, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import configparser
import threading
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    import src.io.io_handler as io_handler
    import src.log.logger_config as logger_config
except ImportError:
    # Fallback for when modules don't exist yet
    io_handler = None
    logger_config = None

# Import main scraper function if available
try:
    from main import main as run_scraper
except ImportError:
    def run_scraper():
        pass  # Placeholder function


app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
login_manager = LoginManager()
login_manager.init_app(app)

DATA_FOLDER_FOR_SCRAPER = './out'
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Slap Red Scraper</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .status { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .progress { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; overflow: hidden; }
        .progress-bar { background: #28a745; height: 20px; transition: width 0.3s; }
        .logout { float: right; }
        .results { margin-top: 20px; }
        .results a { display: inline-block; margin: 5px; padding: 8px 15px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; }
    </style>
    <script>
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status-message').textContent = data.message;
                    document.getElementById('progress-text').textContent = data.progress + ' / ' + data.total;
                    if (data.total > 0) {
                        const percent = (data.progress / data.total) * 100;
                        document.getElementById('progress-bar').style.width = percent + '%';
                    }
                    if (data.message === 'Running') {
                        setTimeout(updateStatus, 2000);
                    }
                });
        }
        setInterval(updateStatus, 5000);
    </script>
</head>
<body>
    <div class="header">
        <h1>🔍 Slap Red Scraper</h1>
        <p>Web scraping tool for bonus data extraction</p>
        <a href="/logout" class="logout btn">Logout</a>
    </div>
    
    <div class="form-group">
        <h2>Upload URLs</h2>
        <form method="post" enctype="multipart/form-data" action="/run_scraper">
            <div class="form-group">
                <label for="url_file">Upload URLs file (one URL per line):</label>
                <input type="file" name="url_file" id="url_file" accept=".txt,.csv">
            </div>
            <button type="submit" class="btn">🚀 Start Scraping</button>
        </form>
    </div>
    
    <div class="form-group">
        <h2>Or Enter URLs Manually</h2>
        <form method="post" action="/run_scraper_manual">
            <div class="form-group">
                <label for="urls">Enter URLs (one per line):</label>
                <textarea name="urls" id="urls" rows="5" placeholder="https://example1.com&#10;https://example2.com"></textarea>
            </div>
            <button type="submit" class="btn">🚀 Start Scraping</button>
        </form>
    </div>
    
    <div class="status">
        <h3>Status</h3>
        <p><strong>Current Status:</strong> <span id="status-message">{{ status.message }}</span></p>
        <p><strong>Progress:</strong> <span id="progress-text">{{ status.progress }} / {{ status.total }}</span></p>
        <div class="progress">
            <div class="progress-bar" id="progress-bar" style="width: {% if status.total > 0 %}{{ (status.progress / status.total * 100)|round }}{% else %}0{% endif %}%"></div>
        </div>
    </div>
    
    <div class="results">
        <h3>Download Results</h3>
        <a href="/download/csv">📊 Download CSV</a>
        <a href="/download/json">📄 Download JSON</a>
        <a href="/logs">📋 View Logs</a>
    </div>
</body>
</html>
"""

scraper_status = {"message": "Idle", "progress": 0, "total": 0, "data_file_path": ""}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login for the web interface."""
    if request.method == 'POST':
        config = configparser.ConfigParser()
        config.read('In/config.ini')
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            if username == config.get('auth', 'username') and password == config.get('auth', 'password'):
                user = User(username)
                login_user(user)
                return redirect(url_for('index'))
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass
        flash('Invalid credentials', 'error')
    
    login_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Slap Red Scraper</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
            .login-form { background: #f8f9fa; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            .btn { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; }
            .btn:hover { background: #0056b3; }
            .error { color: red; margin-bottom: 15px; }
            h1 { text-align: center; color: #333; }
        </style>
    </head>
    <body>
        <div class="login-form">
            <h1>🔍 Slap Red Scraper</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="error">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" name="username" id="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" name="password" id="password" required>
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(login_html)

@app.route('/')
@login_required
def index():
    """Renders the main scraper interface."""
    try:
        if io_handler:
            scraper_status["data_file_path"] = io_handler.get_output_path("output_bonuses_batch.json", base_data_dir=DATA_FOLDER_FOR_SCRAPER)
        else:
            scraper_status["data_file_path"] = ""
    except:
        scraper_status["data_file_path"] = ""
    return render_template_string(INDEX_HTML, status=scraper_status)

@app.route('/logout')
@login_required
def logout():
    """Logs out the current user."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/run_scraper', methods=['POST'])
@login_required
def run_scraper_route():
    """Initiates a batch scraping job with an uploaded URL file."""
    url_file = request.files.get('url_file')
    if not url_file:
        scraper_status.update({"message": "No file uploaded", "progress": 0, "total": 0})
        return redirect(url_for('index'))
    
    logger = logger_config.setup_logger() if logger_config else None
    try:
        urls = url_file.read().decode('utf-8').splitlines()
        urls = [url.strip() for url in urls if url.strip()]  # Clean up URLs
        scraper_status.update({"message": "Running", "progress": 0, "total": len(urls)})
        
        def run():
            try:
                # Write URLs to a temporary file
                url_file_path = os.path.join('In', 'temp_urls.txt')
                with open(url_file_path, 'w') as f:
                    for url in urls:
                        f.write(url + '\n')
                
                # Update config to use the temporary file
                config = configparser.ConfigParser()
                config.read('In/config.ini')
                config.set('scraper', 'url_list_path', url_file_path)
                
                # Run the scraper
                asyncio.run(run_scraper())
                scraper_status.update({"message": "Completed", "progress": len(urls)})
            except Exception as e:
                logger.error("scraper_run_fail", {"err": str(e)})
                scraper_status.update({"message": f"Error: {str(e)}", "progress": 0})
        
        threading.Thread(target=run, daemon=True).start()
        return redirect(url_for('index'))
    except Exception as e:
        logger.error("scraper_run_fail", {"err": str(e)})
        scraper_status.update({"message": f"Error: {str(e)}", "progress": 0})
        return redirect(url_for('index'))

@app.route('/run_scraper_manual', methods=['POST'])
@login_required
def run_scraper_manual():
    """Initiates a batch scraping job with manually entered URLs."""
    urls_text = request.form.get('urls', '').strip()
    if not urls_text:
        scraper_status.update({"message": "No URLs provided", "progress": 0, "total": 0})
        return redirect(url_for('index'))
    
    logger = logger_config.setup_logger()
    try:
        urls = [url.strip() for url in urls_text.splitlines() if url.strip()]
        scraper_status.update({"message": "Running", "progress": 0, "total": len(urls)})
        
        def run():
            try:
                # Write URLs to a temporary file
                url_file_path = os.path.join('In', 'temp_urls.txt')
                with open(url_file_path, 'w') as f:
                    for url in urls:
                        f.write(url + '\n')
                
                # Update config to use the temporary file
                config = configparser.ConfigParser()
                config.read('In/config.ini')
                config.set('scraper', 'url_list_path', url_file_path)
                
                # Run the scraper
                asyncio.run(run_scraper())
                scraper_status.update({"message": "Completed", "progress": len(urls)})
            except Exception as e:
                logger.error("scraper_run_fail", {"err": str(e)})
                scraper_status.update({"message": f"Error: {str(e)}", "progress": 0})
        
        threading.Thread(target=run, daemon=True).start()
        return redirect(url_for('index'))
    except Exception as e:
        logger.error("scraper_run_fail", {"err": str(e)})
        scraper_status.update({"message": f"Error: {str(e)}", "progress": 0})
        return redirect(url_for('index'))

@app.route('/status')
@login_required
def status():
    """Returns the current scraper status."""
    return jsonify(scraper_status)

@app.route('/download/<format_type>')
@login_required
def download_results(format_type):
    """Download results in specified format."""
    try:
        if format_type == 'csv':
            file_path = os.path.join('out', 'output_bonuses_batch.csv')
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True, download_name='scraper_results.csv')
        elif format_type == 'json':
            file_path = os.path.join('out', 'output_bonuses_batch.json')
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True, download_name='scraper_results.json')
        
        flash('No results file found', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/logs')
@login_required
def view_logs():
    """Display recent log entries."""
    try:
        log_content = ""
        log_files = ['out/scraper.log', 'scraper.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Get last 100 lines
                    log_content = ''.join(lines[-100:])
                break
        
        if not log_content:
            log_content = "No log file found."
        
        logs_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Logs - Slap Red Scraper</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .logs {{ background: #000; color: #0f0; padding: 20px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; max-height: 600px; overflow-y: auto; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Scraper Logs</h1>
                <a href="/" class="btn">← Back to Dashboard</a>
            </div>
            <div class="logs">{log_content}</div>
        </body>
        </html>
        """
        return render_template_string(logs_html)
    except Exception as e:
        flash(f'Error reading logs: {str(e)}', 'error')
        return redirect(url_for('index'))

# Set login manager properties
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

if __name__ == '__main__':
    # Ensure output directory exists
    os.makedirs('out', exist_ok=True)
    os.makedirs('In', exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=12000, debug=True)
