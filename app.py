"""
LeaseGuard API — Backend for the web UI
Your teammate's frontend calls this API with an address,
and it returns Lisa's building report.

SETUP:
  pip3 install flask flask-cors google-genai requests

USAGE:
  python3 app.py

API ENDPOINT:
  POST http://localhost:5000/api/check-building
  Body: {"address": "725 4th Avenue Brooklyn"}
  Returns: {"response": "Lisa's building report..."}
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)  # Allows your teammate's frontend to call this API

# ============================================================
# CONFIG — Vertex AI
# ============================================================
client = genai.Client(
    vertexai=True,
    project="leasegaurd-491606",
    location="us-central1",
)
MODEL = "gemini-2.5-flash"

# ============================================================
# NYC OPEN DATA FUNCTIONS
# ============================================================

def lookup_hpd_violations(house_number: str, street_name: str, borough: str) -> str:
    """Look up HPD housing violations for a NYC building.

    Args:
        house_number: The building's street number, e.g. '1847'
        street_name: The street name in NYC database format, uppercase, e.g. 'GRAND CONCOURSE'
        borough: The NYC borough - one of 'BRONX', 'BROOKLYN', 'MANHATTAN', 'QUEENS', 'STATEN ISLAND'
    """
    boro_map = {
        "MANHATTAN": "1", "BRONX": "2", "BROOKLYN": "3",
        "QUEENS": "4", "STATEN ISLAND": "5"
    }
    boro_id = boro_map.get(borough.upper(), "1")
    street_upper = street_name.upper().strip()
    house = house_number.strip()

    url = "https://data.cityofnewyork.us/resource/wvxf-dwi5.json"
    params = {
        "$where": f"boroid='{boro_id}' AND housenumber='{house}' AND upper(streetname)='{street_upper}'",
        "$limit": "200"
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return json.dumps({"error": f"Could not fetch HPD data: {str(e)}"})

    if not data:
        return json.dumps({"message": f"No HPD violations found for {house} {street_upper}, {borough}.", "count": 0})

    open_violations = [v for v in data if v.get("currentstatus", "").upper() != "CLOSE"]
    class_counts = {}
    for v in open_violations:
        c = v.get("class", "Unknown")
        class_counts[c] = class_counts.get(c, 0) + 1

    return json.dumps({
        "address": f"{house} {street_upper}, {borough}",
        "total_violations_found": len(data),
        "open_violations": len(open_violations),
        "violation_classes": class_counts,
    }, indent=2)


def lookup_311_complaints(house_number: str, street_name: str, borough: str) -> str:
    """Look up 311 complaints for a NYC building.

    Args:
        house_number: The building's street number, e.g. '1847'
        street_name: The street name in NYC database format, uppercase, e.g. 'GRAND CONCOURSE'
        borough: The NYC borough - one of 'BRONX', 'BROOKLYN', 'MANHATTAN', 'QUEENS', 'STATEN ISLAND'
    """
    street_upper = street_name.upper().strip()
    house = house_number.strip()
    borough_upper = borough.upper().strip()

    url = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
    params = {
        "$where": f"upper(incident_address) LIKE '%{house}%{street_upper}%' AND upper(borough)='{borough_upper}' AND created_date > '2025-01-01T00:00:00'",
        "$limit": "200",
        "$order": "created_date DESC"
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return json.dumps({"error": f"Could not fetch 311 data: {str(e)}"})

    if not data:
        return json.dumps({"message": f"No 311 complaints found for {house} {street_upper}, {borough}.", "count": 0})

    complaint_types = {}
    for c in data:
        ctype = c.get("complaint_type", "Other")
        complaint_types[ctype] = complaint_types.get(ctype, 0) + 1

    return json.dumps({
        "address": f"{house} {street_upper}, {borough}",
        "total_complaints": len(data),
        "complaint_types": dict(sorted(complaint_types.items(), key=lambda x: -x[1])[:5]),
    }, indent=2)


def lookup_building_registration(house_number: str, street_name: str, borough: str) -> str:
    """Look up HPD building registration to find the owner/landlord of a NYC building.

    Args:
        house_number: The building's street number, e.g. '1847'
        street_name: The street name in NYC database format, uppercase, e.g. 'GRAND CONCOURSE'
        borough: The NYC borough - one of 'BRONX', 'BROOKLYN', 'MANHATTAN', 'QUEENS', 'STATEN ISLAND'
    """
    boro_map = {
        "MANHATTAN": "1", "BRONX": "2", "BROOKLYN": "3",
        "QUEENS": "4", "STATEN ISLAND": "5"
    }
    boro_id = boro_map.get(borough.upper(), "1")
    street_upper = street_name.upper().strip()
    house = house_number.strip()

    url = "https://data.cityofnewyork.us/resource/tesw-yqqr.json"
    params = {
        "$where": f"boroid='{boro_id}' AND housenumber='{house}' AND upper(streetname)='{street_upper}'",
        "$limit": "10"
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return json.dumps({"error": f"Could not fetch registration data: {str(e)}"})

    if not data:
        return json.dumps({"message": f"No registration found for {house} {street_upper}, {borough}."})

    reg = data[0]
    return json.dumps({
        "address": f"{house} {street_upper}, {borough}",
        "owner_name": reg.get("ownername", "N/A"),
        "owner_business_name": reg.get("corpname", "N/A"),
        "total_units": reg.get("totalunits", "N/A"),
    }, indent=2)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """You are Lisa, a friendly neighbourhood guide and tenant protection agent for New York City renters. Your app is called LeaseGuard.

PERSONALITY:
- Friendly, warm, and approachable — like a helpful neighbor.
- You're on the tenant's side.
- Use plain language. Explain any jargon.
- Keep responses concise — max 4-5 sentences total.

LANGUAGE RULES:
- Detect the user's language and respond in the SAME language.
- Support: English, Hindi, and Spanish.

CRITICAL — ADDRESS FORMATTING FOR TOOL CALLS:
When calling any lookup tool, format the address for NYC Open Data:
- Convert: "4th Ave" → "4 AVENUE", "5th Avenue" → "5 AVENUE"
- "163rd Street" → "EAST 163 STREET" or "WEST 163 STREET"
- Remove suffixes: no "st", "nd", "rd", "th"
- Spell out STREET, AVENUE, PLACE, BOULEVARD
- house_number = just the number, e.g. "725"
- borough = BRONX, BROOKLYN, MANHATTAN, QUEENS, or STATEN ISLAND

WHAT YOU DO:
- Use ALL THREE lookup tools for every building query.
- Cite sources: "According to HPD records..."
- Give risk assessment: HIGH (15+ violations/Class C), MEDIUM (5-15), LOW (under 5)

WHAT YOU DON'T DO:
- Never speculate about legal outcomes.
- Never make up data.
- Recommend calling 311 or a tenant attorney for legal questions.
"""

# ============================================================
# API ENDPOINTS
# ============================================================

# Store chat sessions per user (simple in-memory for hackathon)
chat_sessions = {}

def get_chat(session_id="default"):
    """Get or create a chat session."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[
                    lookup_hpd_violations,
                    lookup_311_complaints,
                    lookup_building_registration,
                ],
                temperature=0.7,
            ),
        )
    return chat_sessions[session_id]


@app.route("/api/check-building", methods=["POST"])
def check_building():
    """Main endpoint — send an address, get Lisa's report back."""
    data = request.json
    address = data.get("address", "")
    session_id = data.get("session_id", "default")

    if not address:
        return jsonify({"error": "No address provided"}), 400

    try:
        chat = get_chat(session_id)
        response = chat.send_message(address)
        return jsonify({
            "response": response.text,
            "address": address,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat_message():
    """General chat endpoint — for follow-up questions."""
    data = request.json
    message = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        chat = get_chat(session_id)
        response = chat.send_message(message)
        return jsonify({
            "response": response.text,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return jsonify({
        "name": "LeaseGuard API — Lisa",
        "endpoints": {
            "POST /api/check-building": "Send {address: '725 4th Ave Brooklyn'} to get a building report",
            "POST /api/chat": "Send {message: 'who owns this building?'} for follow-up questions",
        }
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  🏠 LeaseGuard API — Lisa is ready!")
    print("  📡 Running at http://localhost:8080")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8080, debug=True)