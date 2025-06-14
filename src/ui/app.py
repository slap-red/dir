# app.py
from flask import Flask, request, jsonify, render_template_string, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
import configparser
import threading
import io_handler
from main import main as run_scraper
from logger_config import setup_logger
import os


app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
login_manager = LoginManager()
login_manager.init_app(app)

DATA_FOLDER_FOR_SCRAPER = './data'
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>Slap Red Scraper</title></head>
<body>
    <h1>Slap Red Scraper</h1>
    <form method="post" enctype="multipart/form-data" action="/run_scraper">
        <label>Upload URLs file: <input type="file" name="url_file"></label>
        <button type="submit">Run Scraper</button>
    </form>
    <p>Status: {{ status.message }}</p>
    <p>Progress: {{ status.progress }} / {{ status.total }}</p>
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
        config.read('config.ini')
        username = request.form.get('username')
        password = request.form.get('password')
        if username == config.get('auth', 'username') and password == config.get('auth', 'password'):
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials', 'error')
    return render_template_string("""
    <form method="post">
        <label>Username: <input type="text" name="username"></label>
        <label>Password: <input type="password" name="password"></label>
        <button type="submit">Login</button>
    </form>
    """)

@app.route('/')
@login_required
def index():
    """Renders the main scraper interface."""
    scraper_status["data_file_path"] = io_handler.get_output_path("output_bonuses_batch.json", base_data_dir=DATA_FOLDER_FOR_SCRAPER)
    return render_template_string(INDEX_HTML, status scaper_status)

@app.route('/run_scraper', methods=['POST'])
@login_required
def run_scraper_route():
    """Initiates a batch scraping job with an uploaded URL file."""
    url_file = request.files.get('url_file')
    if not url_file:
        scraper_status.update({"message": "No file uploaded", "progress": 0, "total": 0})
        return jsonify(scraper_status)
    
    logger = setup_logger()
    try:
        urls = url_file.read().decode('utf-8').splitlines()
        scraper_status.update({"message": "Running", "progress": 0, "total": len(urls)})
        
        def run():
            config = configparser.ConfigParser()
            config.read('config.ini')
            config.set('scraper', 'url_list_path', url_file.filename)
            io_handler.write_urls(urls, url_file.filename, logger)
            asyncio.run(run_scraper())
            scraper_status.update({"message": "Completed", "progress": len(urls)})
        
        threading.Thread(target=run, daemon=True).start()
        return jsonify(scraper_status)
    except Exception as e:
        logger.error("scraper_run_fail", {"err": str(e)})
        scraper_status.update({"message": f"Error: {str(e)}", "progress": 0})
        return jsonify(scraper_status), 500

@app.route('/status')
@login_required
def status():
    """Returns the current scraper status."""
    return jsonify(scraper_status)
