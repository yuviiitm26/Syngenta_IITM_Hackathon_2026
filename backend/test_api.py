import google.generativeai as genai

# 1. Insert your actual API key here
genai.configure(api_key="AIzaSyBegpi2xoG7Sv7TywAej31j9s8Aq875_jE")

print("🔍 Searching for available Gemini models attached to this API Key...\n")

try:
    available_models = []
    # 2. Ask Google what models we are legally allowed to use
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            available_models.append(model.name)
            print(f"✅ Found Supported Model: {model.name}")
            
    if not available_models:
        print("❌ ERROR: Your API key is working, but it has ZERO models available. You may be in a restricted region or using a restricted key.")

except Exception as e:
    print(f"❌ CRITICAL ERROR connecting to Google: {e}")