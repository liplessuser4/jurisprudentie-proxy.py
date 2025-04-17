from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from bert_loader import load_ner_pipeline

app = Flask(__name__)
nlp = load_ner_pipeline()

# 🔎 Endpoint 1 – Zoek jurisprudentie op basis van zoekterm
@app.route("/jurisprudentie/zoek", methods=["POST"])
def zoek_jurisprudentie():
    data = request.json
    zoekterm = data.get("zoekterm")

    if not zoekterm:
        return jsonify({"error": "Zoekterm is verplicht"}), 400

    try:
        RSS_FEED_URL = "https://data.rechtspraak.nl/uitspraken.rss"
        response = requests.get(RSS_FEED_URL, params={"q": zoekterm})
        response.raise_for_status()
        root = ET.fromstring(response.content)

        results = []
        for item in root.findall(".//item")[:10]:
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

# 🔎 Endpoint 2 – Analyseer ECLI met Legal BERT
@app.route("/jurisprudentie/analyse", methods=["POST"])
def analyseer_ecli():
    data = request.json
    ecli = data.get("ecli")

    if not ecli:
        return jsonify({"error": "ECLI is verplicht"}), 400

    try:
        url = f"https://uitspraken.rechtspraak.nl/#!/details?id={ecli}"
        html = requests.get(url).text
        soup = BeautifulSoup(html, "html.parser")

        tekst = ""
        for div in soup.find_all("div"):
            if div.get("class") and "uitspraak" in " ".join(div.get("class")):
                tekst += div.get_text(separator=" ", strip=True)

        if not tekst:
            return jsonify({"error": "Geen uitspraaktekst gevonden"}), 404

        ner_resultaten = nlp(tekst[:2000])  # Beperk analyse voor snelheid

        return jsonify({
            "ecli": ecli,
            "samenvatting": tekst[:1000] + "...",
            "entiteiten": ner_resultaten
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return "Jurisprudentie-proxy draait!", 200

if __name__ == "__main__":
    app.run(debug=True, port=8080)
