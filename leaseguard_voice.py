"""
LeaseGuard Voice Agent — Lisa, your friendly neighbourhood guide
Uses Vertex AI with Google Cloud credits.

SETUP:
  gcloud auth application-default login
  gcloud config set project leasegaurd-491606
  pip3 install SpeechRecognition pyttsx3 google-genai requests

USAGE:
  python3 leaseguard_voice.py
"""

import json
import requests
import speech_recognition as sr
import pyttsx3
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
# TEXT-TO-SPEECH
# ============================================================
engine = pyttsx3.init()
engine.setProperty('rate', 180)

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
- Keep responses SHORT for voice — max 4-5 sentences total.
- Be conversational, like talking to a knowledgeable friend.

LANGUAGE RULES:
- Detect the user's language and respond in the SAME language.
- If the user switches language mid-conversation, switch immediately.
- You support: English, Hindi, and Spanish.

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

# ============================================================
# VOICE FUNCTIONS
# ============================================================

def speak(text):
    """Convert text to speech."""
    print(f"\n  🏠 Lisa: {text}\n")
    engine.say(text)
    engine.runAndWait()


def listen():
    """Listen for voice input and return text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("  🎤 Listening... (speak now)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=20)
            print("  ⏳ Processing speech...")
            text = recognizer.recognize_google(audio)
            print(f"  🎤 You said: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"  ❌ Speech recognition error: {e}")
            return None


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("  🏠 LeaseGuard — Meet Lisa!")
    print("  🎤 Speak in English, Hindi, or Spanish!")
    print("  Say 'quit' or 'exit' to stop")
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

    speak("Hi! I'm Lisa, your friendly neighbourhood guide for NYC renters. I can look up building safety records in English, Hindi, or Spanish. Just tell me an address and I'll check it for you!")

    while True:
        user_input = listen()

        if user_input is None:
            speak("I didn't catch that. Could you repeat the address?")
            continue

        if user_input.lower() in ("quit", "exit", "stop", "bye"):
            speak("Stay safe out there! Goodbye!")
            break

        try:
            print("  ⏳ Lisa is looking up the data...")
            response = chat.send_message(user_input)
            speak(response.text)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            speak("Sorry, I had trouble looking that up. Could you try again?")


if __name__ == "__main__":
    main()