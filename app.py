from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def fetch_news(keyword, allowed_domains):
    url = f"https://www.bing.com/news/search?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []

        for item in soup.select('a[href^="http"]'):
            title = item.get_text(strip=True)
            url = item.get('href')
            if not title or not url or not url.startswith("http"):
                continue

            domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
            domain = domain_match.group(1) if domain_match else ""

            if "microsoft.com" in domain:
                continue
            if "bing.com" in domain:
                continue
            if allowed_domains and not any(allowed in domain for allowed in allowed_domains):
                continue

            parent = item.find_parent()
            source = parent.find_next_sibling("div") if parent else None
            time_tag = parent.find_next("time") if parent else None
            news_items.append({
                "title": title,
                "url": url,
                "source": source.get_text(strip=True) if source else "Unknown",
                "domain": domain,
                "timestamp": time_tag.get("datetime") if time_tag and time_tag.has_attr("datetime") else time_tag.get_text(strip=True) if time_tag else "Unknown"
            })

            if len(news_items) >= 1000:
                break

        return news_items or [{"title": "", "url": "#", "domain": "", "timestamp": "Unknown"}]

    except Exception as e:
        print(f"Scraping error: {e}")
        return [{"title": "Error fetching news", "url": "#", "domain": "", "timestamp": "Unknown"}]
@app.route("/")
def index():
    return render_template('index.html')
@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json(force=True)
        print(f"Payload received: {data}")

        keywords = data.get('keywords', [])
        allowed_domains = data.get('allowed_domains', [])

        if not keywords or not isinstance(keywords, list):
            return jsonify({'error': 'Keywords must be a non-empty list'}), 400

        all_news = []
        for keyword in keywords:
            news = fetch_news(keyword.strip(), allowed_domains)
            all_news.extend(news)

        return jsonify(all_news)
    except Exception as e:
        print(f"Critical backend error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)