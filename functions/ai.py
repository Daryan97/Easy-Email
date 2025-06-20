import requests

class WorkersAI:
    def __init__(self, api_key = None, base_url = None, model = None):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        
    def chat(self, messages):
        input = [
            {
            "provider": "workers-ai",
            "endpoint": self.model,
            "headers": {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            "query": {
                "messages": messages,
            },
            },
            ]
        
        
        response = requests.post(
            f"{self.base_url}",
            headers={
                "Content-Type": "application/json",
            },
            json=input,
        )
        
        return response.json()