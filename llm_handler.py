# llm_handler.py
import os
import json
from datetime import date
from groq import Groq

# We will set this Key in Railway later
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_intent_and_entities(user_message):
    today_str = date.today().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are an entity extractor. Current Date: {today_str}.
    Extract INTENT (check_slots, find_centres, get_address, count_academies), 
    DATE (YYYY-MM-DD), TIME (HH:MM), TARGET_NAME, and LIMIT (int).
    User Query: "{user_message}"
    Return JSON only.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"AI Error: {e}")
        return {"intent": "find_centres", "limit": 5}