from dotenv import dotenv_values
import json
from models import Chat
from pymongo import MongoClient
from datetime import datetime
import requests
from errHandler import ErrorHandler
# ------------------------------ Reading configs and environments ------------------------------
env=dict(dotenv_values('D:\\zara_v1\\.env'))
config=json.load(open('D:\\zara_v1\\zara_config.json','r'))

# ------------------------------ Llm class ------------------------------


class Stm(ErrorHandler):
    def __init__(self, messages=None, responder=""):
        super().__init__()
        self._messages = messages if messages else []  
        self._max_length = 6000
        self.system_prompt = responder

    def get_new_context(self, user_query: str):
        query_length = len(user_query) + len(self.system_prompt)
        current_context_length = query_length

        history = []
        
        for message in self._messages:
            query = message.get('query', '')
            response = message.get('response', '')
            total_length = len(query) + len(response)

            if current_context_length + total_length >= self._max_length:
                break

            current_context_length += total_length
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})

        new_context = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": user_query}]
        return new_context

    def save_to_message(self, query="", response=""):

        self._messages.insert(0,{"query": query, "response": response})

class Database(ErrorHandler):
    def __init__(self):
        super().__init__()
        self._client=MongoClient(env['MONGO_DB_URL'])
        self._database=self._client['zara']
        self._collection=self._database['context']
    
    
    def add_message(self,context:Chat):
        self._collection.insert_one(context.dict())
        
    def get_older_messages(self, limit: int = 10):
        pipeline = [
            {"$sort": {"timestamp": -1}},  
            {"$limit": limit},    
            {"$project": {
                "_id":0,
                "query": 1,
                "response": 1
            }}
        ]
        return list(self._collection.aggregate(pipeline))



class LLM:
    def __init__(self,funtionsCallingPrompt,responder):
        self._API_KEY=env['SARWAM_API_KEY']
        self._API_URL=env['SARWAM_API_URL']
        self._FUNCTION_CALLING=funtionsCallingPrompt
        self._RESPONDER=responder
        self._prompt_creator= "You are a prompt engineer for an AI image generation system.\n\nYour task is to take in a list of keywords provided by the user and craft a detailed, vivid, and imaginative prompt suitable for a text-to-image model.\n\nGuidelines:\n- Combine the keywords into a single coherent scene or visual description.\n- Use descriptive language, including colors, setting, mood, lighting, and style (e.g., 'digital art', 'hyper-realistic', 'fantasy', 'cyberpunk', etc.) when appropriate.\n- Avoid using the exact keyword list as-is. Expand it into a natural, visually rich sentence.\n- Output only the final prompt. Do not include explanations, formatting, or extra metadata."
        self._old_message=Database().get_older_messages()
        self._memory=Stm(self._old_message,self._RESPONDER)
        
    def generate_prompt(self,keywords=''):
        headers = {
            "Authorization": f"Bearer {self._API_KEY}",  
            "Content-Type": "application/json"
        }
        data = {
            "messages": [
                {
                    "content":self._prompt_creator,
                    "role": "system"
                },
                {"role":"user","content":f"Here are keywords :- {keywords}"}
            ],
            "model": "sarvam-m"
        }

        response = requests.post(self._API_URL, headers=headers, json=data).json()
        return response['choices'][0]['message']['content']
    
    def _get_response_from_api(self,messages=[]):             
        headers = {
            "Authorization": f"Bearer {self._API_KEY}",  
            "Content-Type": "application/json"
        }
        data = {
            "messages": messages,
            "model": "sarvam-m"
        }

        response = requests.post(self._API_URL, headers=headers, json=data).json()
        try:
            return response['choices'][0]['message']['content']
        except Exception as e:
            print("Response :-",response)
    def generate_function(self,message):
        messages=[
                {
                    "content":self._FUNCTION_CALLING,
                    "role": "system"
                },
                {"role":"user","content":message}
            ]
        return self._get_response_from_api(messages)
        
    def generate_response(self,message):
        new_context=self._memory.get_new_context(message)
        response=self._get_response_from_api(new_context)
        self._memory.save_to_message(message,response)
        return response

