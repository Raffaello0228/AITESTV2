import datetime
import json
import requests
from func_timeout import func_set_timeout

class MeetAskApiClient:
    def __init__(self):
        self.base_url = "https://o-test-ai-service.meetsocial.cn"
        self.headers = {
            'accept': '*/*',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        return response

    @func_set_timeout(180)
    def ask_question(self, query, user):
        request_time = datetime.datetime.now()
        first_char_response_time = None
        
        try:
            payload = {
                "llmType": "openai",
                "query": query,
                "user": user
            }
            
            response = self._make_request("/meetask/stream/askQuestion", payload)
            stream = response.iter_content()
            stream_content = b""
            
            for chunk in stream:
                stream_content += chunk
                if len(stream_content) > 0 and not first_char_response_time:
                    first_char_response_time = datetime.datetime.now()
            
            content = stream_content.decode("UTF-8")
            res = content.split("\n\n")[-2].replace("data:", "")
            
        except Exception:
            res = ""
            
        cost = (first_char_response_time - request_time).seconds if first_char_response_time else 0
        return res, cost 