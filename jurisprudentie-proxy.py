from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

# RSS-feed van Rechtspraak
RSS_FEED_URL = "https://data.rechtspraak.nl/uitspraken.rss"

@app.route("/jurisprudentie/zoek", methods=["POST"])
def zoek_jurisprudentie():
    data = request.json
    zoekterm = data.get("zoekterm")

    if not zoekterm:
        return jsonify({"error": "Zoekterm is verplicht"}), 400

    try:
        # Voeg zoekterm toe aan RSS-query
        response = requests.get(RSS_FEED_URL, params={"q": zoekterm})
        response.raise_for_status()

        # Parse XML naar JSON
        root = ET.fromstring(response.content)
        results = []

        for item in root.findall(".//item")[:10]:  # max 10 uitspraken
            titel = item.findtext("title")
            link = item.findtext("link")
            pubDate = item.findtext("pubDate")
            samenvatting = item.findtext("description")

            results.append({
                "titel": titel,
                "link": link,
                "datum": pubDate,
                "samenvatting": samenvatting
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return "Jurisprudentiezoeker actief!", 200

if __name__ == "__main__":
    app.run(debug=True, port=8080)
