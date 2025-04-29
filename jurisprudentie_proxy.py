from flask import Flask, request, jsonify
import requests
from bert_loader import load_legalbert_embedding_pipeline  # alleen embeddings

app = Flask(__name__)

# Configuratie
API_INDEX_URL    = "https://api.rechtspraak.nl/v1/index"
API_DOCUMENT_URL = "https://api.rechtspraak.nl/v1/document"
# URI voor bestuurs- & omgevingsrecht
RECHTSGEBIED_URI = "http://psi.rechtspraak.nl/rechtsgebied#bestuursrecht_omgevingsrecht"

# Embedding model laden bij opstart
embed = load_legalbert_embedding_pipeline()

# 🔎 Endpoint 1 – Zoek jurisprudentie op basis van zoekterm
@app.route("/jurisprudentie/zoek", methods=["POST"])
def zoek_jurisprudentie():
    data = request.json or {}
    zoekterm = data.get("zoekterm", "").strip()

    if not zoekterm:
        return jsonify({"error": "Zoekterm is verplicht"}), 400

    # Stap 1: vraag lijst van ECLI’s op via index-endpoint
    payload = {
        "criteria": {
            "rechtsgebied": [RECHTSGEBIED_URI],
            "searchterm": zoekterm,
            "maxRecords": 10
        }
    }
    idx_resp = requests.post(API_INDEX_URL, json=payload)
    if idx_resp.status_code != 200:
        return jsonify({"error": "Index-opvraag mislukt", "details": idx_resp.text}), 500

    eclis = [item.get("ecli") for item in idx_resp.json().get("results", [])]
    results = []

    # Stap 2: per ECLI metadata ophalen en filteren
    for ecli in eclis:
        doc_resp = requests.get(f"{API_DOCUMENT_URL}?ecli={ecli}")
        if doc_resp.status_code != 200:
            continue
        doc = doc_resp.json()
        # Controle op omgevingsrecht
        gebieden = [g.get("uri") for g in doc.get("inRechtsgebied", [])]
        if RECHTSGEBIED_URI not in gebieden:
            continue

        results.append({
            "ecli": doc.get("ecli"),
            "titel": doc.get("title"),
            "datum": doc.get("decisionDate"),
            "link": doc.get("documentUrl"),
            "samenvatting": (doc.get("berichttekst") or doc.get("summary", ""))[:200] + "..."
        })

    return jsonify(results), 200

# 🔎 Endpoint 2 – Analyseer ECLI met Legal BERT embeddings
@app.route("/jurisprudentie/analyse", methods=["POST"])
def analyseer_ecli():
    data = request.json or {}
    ecli = data.get("ecli")

    if not ecli:
        return jsonify({"error": "ECLI is verplicht"}), 400

    # Ophalen volledige tekst via Open Data API
    doc_resp = requests.get(f"{API_DOCUMENT_URL}?ecli={ecli}")
    if doc_resp.status_code != 200:
        return jsonify({"error": "Document niet gevonden", "details": doc_resp.text}), 404

    doc = doc_resp.json()
    tekst = doc.get("berichttekst", "")
    if not tekst:
        return jsonify({"error": "Geen uitspraaktekst gevonden"}), 404

    # Embed tekst (max 2000 chars)
    tekst_kort = tekst[:2000]
    embedding = embed(tekst_kort)

    return jsonify({
        "ecli": ecli,
        "titel": doc.get("title"),
        "samenvatting": tekst[:1000] + "...",
        "embedding": embedding
    }), 200

# Health-check
@app.route("/", methods=["GET"])
def health_check():
    return "Jurisprudentie-proxy draait!", 200

if __name__ == "__main__":
    app.run(debug=True, port=8080)
