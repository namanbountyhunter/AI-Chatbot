import requests
from requests.exceptions import RequestException
import json


class OllamaClient:
    def __init__(self, model="phi3"):
        self.model = model
        self.base_url = "http://localhost:11434/api"   # ✅ FIXED

    # 🔥 NORMAL CHAT
    def chat(self, messages):
        payload = {
            "model": self.model,
            "messages": messages,   # ✅ FIXED
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat",   # ✅ FIXED
                json=payload,
                timeout=180
            )
            response.raise_for_status()

        except RequestException as e:
            raise Exception(f"Ollama connection failed: {str(e)}")

        try:
            data = response.json()
            return data["message"]["content"]   # ✅ FIXED
        except (KeyError, ValueError):
            raise Exception("Invalid response format from Ollama")

    # 🔥 STREAMING CHAT
    def chat_stream(self, messages):
        payload = {
            "model": self.model,
            "messages": messages,   # ✅ FIXED
            "stream": True
        }

        response = requests.post(
            f"{self.base_url}/chat",   # ✅ FIXED
            json=payload,
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "message" in data:
                    yield data["message"]["content"]