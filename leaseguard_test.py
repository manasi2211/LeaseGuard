from google import genai

client = genai.Client(api_key="AIzaSyAPJ46f_k9EHLFCRtZYMC_g1Lbyvk4o7U8")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="You are LeaseGuard, a tenant protection agent for NYC renters. Say hello in Hindi, English, and Spanish and briefly introduce yourself."
)

print(response.text)