import os
import secrets
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
STATS_FILE = 'url_stats.json'
SHORT_CODE_LENGTH = 6


# Load existing data
def load_data():
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data):
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f)


url_stats = load_data()
url_mappings = {k: v['original_url'] for k, v in url_stats.items()}


# Helper functions
def generate_short_code():
    return secrets.token_urlsafe(SHORT_CODE_LENGTH)[:SHORT_CODE_LENGTH]


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = session.get('last_short_url', None)

    if request.method == 'POST':
        original_url = request.form.get('url')

        if not is_valid_url(original_url):
            flash('Please enter a valid URL (e.g., https://example.com)', 'error')
            return redirect(url_for('index'))

        # Check for existing URL
        for short_code, url in url_mappings.items():
            if url == original_url:
                session['last_short_url'] = request.host_url + short_code
                flash('This URL already has a short code!', 'info')
                return redirect(url_for('index'))

        # Create new short URL
        short_code = generate_short_code()
        url_mappings[short_code] = original_url
        url_stats[short_code] = {'visits': 0, 'original_url': original_url}
        save_data(url_stats)

        session['last_short_url'] = request.host_url + short_code
        return redirect(url_for('index'))

    return render_template('index.html', short_url=short_url)


@app.route('/<short_code>')
def redirect_to_url(short_code):
    if short_code in url_mappings:
        url_stats[short_code]['visits'] += 1
        save_data(url_stats)
        return redirect(url_mappings[short_code])
    flash('Short URL not found', 'error')
    return redirect(url_for('index'))


@app.route('/stats')
def stats():
    sorted_stats = sorted(url_stats.items(),
                          key=lambda x: x[1]['visits'],
                          reverse=True)
    return render_template('stats.html', stats=sorted_stats)


@app.route('/clear')
def clear_short_url():
    session.pop('last_short_url', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
