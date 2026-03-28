"""
LeaseGuard API Server — Connects the web frontend to Gemini + NYC Open Data

SETUP:
  pip3 install flask flask-cors google-genai requests

USAGE:
  python3 leaseguard_api.py

Then open index.html in your browser.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
from google import genai
from google.genai import types

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
CORS(app)  # Allow frontend to call this

# ============================================================
# GEMINI CONFIG — Vertex AI with your credits
# ============================================================
client = genai.Client(
    vertexai=True,
    project="leasegaurd-491606",
    location="us-central1",
)
MODEL = "gemini-2.5-flash"

# Store chat sessions per user
chat_sessions = {}

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
    closed_violations = [v for v in data if v.get("currentstatus", "").upper() == "CLOSE"]

    categories = {}
    for v in open_violations:
        cat = v.get("novdescription", "Other")[:80]
        categories[cat] = categories.get(cat, 0) + 1

    class_counts = {}
    for v in open_violations:
        c = v.get("class", "Unknown")
        class_counts[c] = class_counts.get(c, 0) + 1

    return json.dumps({
        "address": f"{house} {street_upper}, {borough}",
        "total_violations_found": len(data),
        "open_violations": len(open_violations),
        "closed_violations": len(closed_violations),
        "violation_classes": class_counts,
        "top_violation_types": dict(sorted(categories.items(), key=lambda x: -x[1])[:10]),
        "sample_violations": [
            {
                "date": v.get("inspectiondate", "N/A")[:10],
                "class": v.get("class", "N/A"),
                "description": v.get("novdescription", "N/A")[:120],
                "status": v.get("currentstatus", "N/A")
            }
            for v in open_violations[:5]
        ]
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
        "complaint_types": dict(sorted(complaint_types.items(), key=lambda x: -x[1])[:10]),
        "recent_complaints": [
            {
                "date": c.get("created_date", "N/A")[:10],
                "type": c.get("complaint_type", "N/A"),
                "descriptor": c.get("descriptor", "N/A"),
                "status": c.get("status", "N/A")
            }
            for c in data[:5]
        ]
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
        "registration_id": reg.get("registrationid", "N/A"),
        "building_id": reg.get("buildingid", "N/A"),
        "owner_name": reg.get("ownername", "N/A"),
        "owner_business_name": reg.get("corpname", "N/A"),
        "registration_end_date": reg.get("registrationenddate", "N/A")[:10] if reg.get("registrationenddate") else "N/A",
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
- Be conversational, like talking to a knowledgeable friend.

LANGUAGE RULES:
- Detect the user's language and respond in the SAME language.
- Support: English, Hindi, and Spanish.

CONVERSATION FLOW:
- Always end by asking: "Would you like to know anything else, or check a different address?"

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

SYSTEM_PROMPT_VOICE = SYSTEM_PROMPT + """

VOICE MODE RULES:
- Keep responses SHORT — max 4-5 sentences total.
- No bullet points or lists — speak naturally.
- No special characters or markdown formatting.
"""

# ============================================================
# ROUTES
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for frontend."""
    return jsonify({"status": "ok", "agent": "Lisa", "app": "LeaseGuard"})


@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint. Creates or reuses a session per session_id."""
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    is_voice = data.get("is_voice", False)

    if not message:
        return jsonify({"error": "No message provided"}), 400

    # Get or create chat session
    if session_id not in chat_sessions:
        prompt = SYSTEM_PROMPT_VOICE if is_voice else SYSTEM_PROMPT
        chat_sessions[session_id] = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                tools=[
                    lookup_hpd_violations,
                    lookup_311_complaints,
                    lookup_building_registration,
                ],
                temperature=0.7,
            ),
        )

    try:
        session = chat_sessions[session_id]
        response = session.send_message(message)
        return jsonify({"reply": response.text})
    except Exception as e:
        # If session is broken, remove it so next request creates fresh one
        chat_sessions.pop(session_id, None)
        return jsonify({"error": str(e)}), 500


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  🏠 LeaseGuard API Server")
    print("  Backend running at http://localhost:8080")
    print("  Open index.html in your browser!")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8080, debug=True)