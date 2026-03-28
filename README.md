# 🛡️ LeaseGuard

**Tenant Protection Voice Agent**

> GDG Build With AI Hackathon NYC 2026

---

## 👥 Team

- [Pratap Gurav](https://www.linkedin.com/in/pratapgurav/)
- [Manasi Shah](https://www.linkedin.com/in/shah-manasi/)
- [Rohit Shegokar](https://www.linkedin.com/in/rohit-shegokar/)
- [Shagun Sharma](https://www.linkedin.com/in/shagun/)

---

## 🚨 The Problem

**Information asymmetry is destroying NYC renters.**

- **15,000 NYC families** were evicted last year. Most never knew their building had dozens of violations before they signed their lease.
- **Landlords have:** lawyers, property management systems, violation history databases, and legal teams
- **Tenants have:** Google searches and hope
- **200,000+ Hindi speakers** in NYC have zero civic tech tools in their language
- **2M+ Spanish speakers** are underserved by existing resources
- **Immigrant renters** face language barriers on top of information asymmetry — bad landlords exploit this

---

## 💡 The Solution

**LeaseGuard** is a multilingual voice agent that gives NYC renters the same information power that landlords have.

### Core Capability: INVESTIGATE Mode (MVP)

Ask about any NYC building by voice → get real violations, complaints, landlord history, and risk assessment — in **English**, **Hindi**, or **Spanish**.

---

## 🎯 Example Interactions
 
### 🇺🇸 English
 
**User:**
> "Tell me about 705 West 170th Street in Manhattan"
 
**LeaseGuard:**
> This building has significant issues you should know about.
>
> **Violations:** 347 open HPD violations — 89 are Class C, meaning immediately hazardous. These include lead paint, rodent infestations, mold, and heat outages.
>
> **Landlord:** The owner is Daniel Ohebshalom, operating through Belmont Ventures LLC. He owns 5 other buildings with a total of 3,293 open violations across his portfolio.
>
> **Litigation:** The landlord was criminally indicted in May 2024 for tenant harassment and falsifying records. He served 60 days at Rikers Island in March 2024 for failing to comply with court-ordered repairs.
>
> **Rent Status:** This building is rent stabilized.
>
> **Risk Assessment:** HIGH RISK. I strongly recommend looking elsewhere.
 
---
 
### 🇮🇳 Hindi
 
**User:**
> "मुझे 919 Prospect Avenue, Bronx के बारे में बताओ"
 
**LeaseGuard:**
> इस बिल्डिंग में कई गंभीर समस्याएं हैं जो आपको जाननी चाहिए।
>
> **उल्लंघन:** 293 HPD उल्लंघन खुले हैं, साथ ही 7 DOB उल्लंघन। इनमें खराब बिजली व्यवस्था, टूटी हुई फायर एस्केप, लेड पेंट, और चूहों की समस्या शामिल है।
>
> **मकान मालिक:** मालिक Seth Miller हैं। वे Public Advocate की "Worst Landlords Watchlist" पर हैं।
>
> **कानूनी कार्रवाई:** मार्च 2026 में कोर्ट ने $2.1 मिलियन का फैसला सुनाया, जिसमें मरम्मत और जुर्माना शामिल है।
>
> **किराया स्थिति:** यह बिल्डिंग rent stabilized है।
>
> **जोखिम मूल्यांकन:** बहुत उच्च जोखिम। मैं दूसरी जगह देखने की सलाह दूंगा।
 
---
 
### 🇪🇸 Spanish
 
**User:**
> "Dime sobre 725 4th Avenue en Brooklyn"
 
**LeaseGuard:**
> Este edificio tiene algunos problemas que debes conocer.
>
> **Violaciones:** 49 violaciones abiertas de HPD — 9 son Clase C (peligro inmediato), 30 son Clase B (peligrosas), y 10 son Clase A. Los problemas incluyen roedores, cucarachas, moho, y calefacción inadecuada.
>
> **Propietario:** El dueño es Samuel Kurtz, operando a través de 725 4th Realty LLC. Este es su único edificio con 164 unidades.
>
> **Historial financiero:** El edificio está en la lista de aviso de venta de gravámenes fiscales de 2025, lo que indica posible estrés financiero.
>
> **Estado de alquiler:** Este edificio tiene renta estabilizada y protección de Good Cause Eviction.
>
> **Evaluación de riesgo:** RIESGO MODERADO. El edificio tiene menos violaciones que el promedio de NYC, pero hay señales de advertencia financieras.
 
---
## 📊 Data Sources

LeaseGuard aggregates data from NYC public records including:

- HPD (Housing Preservation & Development) violations
- DOB (Department of Buildings) complaints
- 311 service requests
- Landlord ownership records
- Rent stabilization status
- Litigation history

---

## 🚀 Setup & Run
### Prerequisites
- Python 3.10+
- Mac (for voice agent's `say` command) or any OS (for web version)
- Google Cloud account with Vertex AI enabled
### Step 1: Clone the repo
```bash
git clone https://github.com/YOUR_REPO_HERE/LeaseGuard.git
cd LeaseGuard
```
### Step 2: Install dependencies
```bash
# Mac only — needed for voice agent microphone
brew install portaudio

# Python packages
pip3 install -r requirements.txt
```
### Step 3: Authenticate with Google Cloud
```bash
gcloud auth application-default login
gcloud config set project leasegaurd-491606
gcloud auth application-default set-quota-project leasegaurd-491606
```
### Step 4: Enable APIs (one time)
- Enable **Vertex AI API**: https://console.cloud.google.com/apis/api/aiplatform.googleapis.com
- Enable **Generative Language API**: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com
### Step 5: Run
**Option A — Web App (recommended for demo):**
```bash
python3 leaseguard_api.py
```
Then open http://localhost:5000 in your browser.
**Option B — Voice Agent (terminal):**
```bash
python3 leaseguard_voice.py
```
Say "Hello" and then ask about any NYC building address.
**Option C — Text Agent (terminal):**
```bash
python3 leaseguard_agent.py
```
Type any NYC building address to get a safety report.
---
## 🎤 Demo Script
1. Open http://localhost:5000
2. Type: **"Tell me about 725 4th Avenue in Brooklyn"** → see violations, complaints, risk assessment
3. Switch to Voice mode → say: **"Who owns this building?"**
4. Ask in Hindi: **"क्या यह बिल्डिंग सुरक्षित है?"**
5. Ask in Spanish: **"¿Hay quejas de cucarachas?"**
---
## 🛠️ Tech Stack
- **Gemini 2.5 Flash** via Vertex AI — language understanding + function calling
- **Google Cloud** — authentication and credits
- **NYC Open Data APIs** — live building data (HPD, 311, registrations)
- **Flask** — Python web server
- **Web Speech API** — browser-based voice recognition
- **Google Speech Recognition** — terminal voice input

<p align="center">
  <strong>Built with ❤️ at GDG Build With AI Hackathon NYC 2026</strong>
</p>
# LeaseGuard
