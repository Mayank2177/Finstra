from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from serpapi import search as GoogleSearch

gemini_api_key = os.getenv('GEMINI_API_KEY')
SERPAPI_KEY = os.getenv('Serpapi_api_key')

if not gemini_api_key:
    print("WARNING: GEMINI_API_KEY not found in environment variables!")
else:
    print("API key loaded successfully")

genai.configure(api_key=gemini_api_key)

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def search_web(query: str) -> str:
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "answer_box" in results and "snippet" in results["answer_box"]:
            return results["answer_box"]["snippet"]
        elif "organic_results" in results and len(results["organic_results"]) > 0:
            return results["organic_results"][0].get("snippet", "No snippet found.")
        else:
            return "I searched the web but couldn't find a clear answer."

    except Exception as e:
        return f"Web search failed: {e}"
        
class VoiceQuery(BaseModel):
    text: str

@app.post("/search")
async def search(query: VoiceQuery):
    input_text = query.text
    
    realtime_keywords = ["today", "current", "latest", "now", "rate", "price", "update", "news"]
    if any(word in input_text.lower() for word in realtime_keywords):
        web_snippet = search_web(input_text)

        prompt = (
            "You are Finstra, a financial strategist. Use the following real-time web result to answer the user's question:\n\n"
            f"Web Search Result:\n{web_snippet}\n\n"
            f"User Question:\n{input_text}\n\n"
            "Reply in the same language and be clear and strategic."
        )

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            return {"response": response.text}
        except Exception as e:
            return {"response": f"Gemini API error: {str(e)}"}
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = (
            f"You are Finstra, a multilingual financial strategist. Respond in the same language and be clear, relevant and strategic: {input_text}"
        )
        response = model.generate_content(prompt)

        if response.text:
            return {"response": response.text}
        else:
            return {"response": "Sorry, Gemini did not return a valid response."}

    except Exception as e:
        return {"response": f"Error from Gemini API: {str(e)}"}
