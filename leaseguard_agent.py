"""
LeaseGuard Text Agent — Vertex AI Version
Uses your Google Cloud $25 credits.

SETUP:
  gcloud auth application-default login
  gcloud config set project leasegaurd-491606
  pip3 install google-genai requests

USAGE:
  python3 leaseguard_agent.py
"""

import json
import requests
from google import genai
from google.genai import types

# ============================================================
# CONFIG — Uses Vertex AI with your Google Cloud credits
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
    closed_violations = [v for v in data if v.get("currentstatus", "").upper() == "CLOSE"]

    categories = {}
    for v in open_violations:
        cat = v.get("novdescription", "Other")[:80]
        categories[cat] = categories.get(cat, 0) + 1

    class_counts = {}
    for v in open_violations:
        c = v.get("class", "Unknown")
        class_counts[c] = class_counts.get(c, 0) + 1

    summary = {
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
    }
    return json.dumps(summary, indent=2)


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

    summary = {
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
    }
    return json.dumps(summary, indent=2)


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
    summary = {
        "address": f"{house} {street_upper}, {borough}",
        "registration_id": reg.get("registrationid", "N/A"),
        "building_id": reg.get("buildingid", "N/A"),
        "owner_name": reg.get("ownername", "N/A"),
        "owner_business_name": reg.get("corpname", "N/A"),
        "registration_end_date": reg.get("registrationenddate", "N/A")[:10] if reg.get("registrationenddate") else "N/A",
        "total_units": reg.get("totalunits", "N/A"),
    }
    return json.dumps(summary, indent=2)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """You are LeaseGuard, an AI tenant protection agent for New York City renters.

PERSONALITY:
- Warm but direct. You're on the tenant's side.
- Use plain language. Explain any jargon.
- Be empathetic — renting in NYC is stressful.

LANGUAGE RULES:
- Detect the user's language and respond in the SAME language.
- If the user switches language mid-conversation, switch immediately.
- You support: English, Hindi (हिंदी), and Spanish (Español).
- For Hindi, use Devanagari script naturally.

CRITICAL — ADDRESS FORMATTING FOR TOOL CALLS:
When calling any lookup tool, you MUST format the address the way NYC Open Data expects:
- street_name must be in NYC database format, ALL UPPERCASE
- Convert numbered streets/avenues like this:
  "4th Ave" → "4 AVENUE"
  "5th Avenue" → "5 AVENUE"
  "163rd Street" → "EAST 163 STREET" or "WEST 163 STREET"
  "1st Street" → "1 STREET"
  "2nd Ave" → "2 AVENUE"
  "Grand Concourse" → "GRAND CONCOURSE"
  "Flatbush Ave" → "FLATBUSH AVENUE"
- Remove suffixes: no "st", "nd", "rd", "th" on numbers
- Spell out "STREET", "AVENUE", "PLACE", "BOULEVARD", "DRIVE", "ROAD" fully
- Include directional prefix if applicable: "EAST", "WEST", "NORTH", "SOUTH"
- house_number is just the number, e.g. "725"
- borough must be one of: BRONX, BROOKLYN, MANHATTAN, QUEENS, STATEN ISLAND

Examples:
  User says "725 4th ave brooklyn" → house_number="725", street_name="4 AVENUE", borough="BROOKLYN"
  User says "510 East 163rd St, Bronx" → house_number="510", street_name="EAST 163 STREET", borough="BRONX"
  User says "1847 Grand Concourse" → house_number="1847", street_name="GRAND CONCOURSE", borough="BRONX"
  User says "100 W 93rd Street Manhattan" → house_number="100", street_name="WEST 93 STREET", borough="MANHATTAN"

WHAT YOU DO:
- When a user asks about a building, use the lookup tools to fetch REAL data.
- Call ALL THREE tools: HPD violations, 311 complaints, AND building registration.
- Present the data clearly with a risk assessment.
- Always cite the source: "According to HPD records..." or "Based on 311 complaint data..."

RISK ASSESSMENT (provide after gathering data):
- HIGH RISK: 15+ open violations, or Class C violations, or active pest/lead issues
- MEDIUM RISK: 5-15 open violations, some complaints
- LOW RISK: Under 5 open violations, few complaints

WHAT YOU DON'T DO:
- Never speculate about legal outcomes.
- Never make up data. If a tool returns no results, say so honestly.
- Always recommend consulting a tenant attorney or calling 311 for legal questions.
- If asked about a topic outside NYC tenant rights, politely redirect.

CONVERSATION STARTERS (if the user just says hi):
- Ask what building address they'd like to check
- Mention you can help in English, Hindi, or Spanish
"""

# ============================================================
# CHAT LOOP
# ============================================================

def main():
    print("=" * 60)
    print("  🏠 LeaseGuard — NYC Tenant Protection Agent")
    print("  Type in English, Hindi, or Spanish!")
    print("  Type 'quit' to exit")
    print("=" * 60)
    print()

    chat = client.chats.create(
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

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nLeaseGuard: Stay safe out there! 🏠")
            break

        try:
            response = chat.send_message(user_input)
            print(f"\nLeaseGuard: {response.text}\n")
        except Exception as e:
            print(f"\n[Error: {e}]\n")


if __name__ == "__main__":
    main()