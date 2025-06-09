import agents 
import inspect
from errHandler import ErrorHandler
import time
from tqdm import tqdm
from IPython.display import clear_output
from dotenv import dotenv_values
from infra import LLM,Database
import json
from models import Chat
pattern = r"\{(?:[^{}]|(?=\{[^{}]*\}))*\}"

# ------------------------------ Configs ------------------------------
env=dict(dotenv_values('D:\\zara_v1\\.env'))
config=json.load(open('D:\\zara_v1\\zara_config.json','r'))


# ------------------------------ Classes ------------------------------
class Zara(ErrorHandler):
    def __init__(self):
        
        self.SYSTEM_PROMPT=config['ZARA_FUNCTION_CALLING']
        self.IGNORE_MODULES = list(map(str.lower,['PdfReader', 'ErrorHandler', 'BeautifulSoup','LLM','InferenceClient','datetime','date','timedelta']))
        self.ALL_MODULES =[(item[0].lower(),item[1]) for item in  inspect.getmembers(agents, inspect.isclass) if item[0].lower() not in self.IGNORE_MODULES]
        self.SYSTEM_RESPONDER=config['ZARA_RESPONDER']
        self.function_description="""```\n"""
        for i,(module_name, module_reference) in tqdm(enumerate(self.ALL_MODULES), desc="Loading Medusa"):
            if module_name not in self.IGNORE_MODULES:
                attr_name = module_reference.__name__.lower()
                module_instance = module_reference()
                self.function_description += f"{i}. Function Name: {module_name}\n   Description   : {getattr(module_instance, '_description')}\n"
                setattr(self, attr_name, module_instance)
                print(f"\rLoaded module {module_reference.__name__}", end='', flush=True)
                time.sleep(0.5)
                clear_output(wait=True)
        self.function_description+="\n ```\n"
        self.SYSTEM_PROMPT=self.SYSTEM_PROMPT.replace('<|functions|>',self.function_description)
        self.SYSTEM_RESPONDER=self.SYSTEM_RESPONDER.replace('<|functions|>',self.function_description)
        self.llm=LLM(self.SYSTEM_PROMPT,self.SYSTEM_RESPONDER)
        self.database=Database()
        super().__init__()
        
        
    
    def _call_module(self,tool,user_input=''):
        function=tool['function']
        args=" ".join(tool['keywords'])
        if hasattr(self,function):
            module=getattr(self,function)
            response=getattr(module,'main')(args,user_input)
            return response
        
        else:
            return {"success":False,"data":"unknown function called"}
                
    
    def _extract_json(self, generated_text, user_text=''):
        try:
            tool_str = generated_text
            tool = json.loads(tool_str)
            if not tool or not isinstance(tool, dict) or 'function' not in tool or len(tool['function'])==0:
                return {"success": True, "data": "No tool required, respond with your knowledge"},"No tool is called"
            response = self._call_module(tool, user_text)
            return response,tool['function']

        except Exception as e:
            print("Error in _extract_json:", e)
            return {"success": False, "error": str(e)},"exception"
        
    def gui(self,message):
        output=self.llm.generate_function(message)
        response,plugin=self._extract_json(output,message)
        data=response.get('data',"")
        extras=response.get('extras',"")
        success=response['success']
        response=self.llm.generate_response(f"User query :- {message} Tool Response :- Success - {response['success']} Content - {data if len(data)<=4000 else "The data is too long it is displayed to the user just inform about success"}")            
        context=Chat(plugin=plugin,query=message,response=response,media=extras,success=success)
        self.save_to_chat(context)
        return response+ (f"\n\nAdditional info :- {",".join(extras)}" if extras is not None else "")
    
    def save_to_chat(self,context):
        try:
            self.database.add_message(context)
        except Exception as e:
            print("Error while saving chat :- ",e)
        
    def run(self):
        while True:
            print()
            user_input = input('Chat with Zara >>>')
            if user_input == 'break':
                break
            output=self.llm.generate_function(user_input)
            response,plugin=self._extract_json(output, user_input)
            data=response.get('data',"")
            extras=response.get('extras',"")
            success=response['success']
            if data and len(data)>4000:
                print("Info :-",data[:200])
            if extras is not None:
                print("Extra info :-",extras)
            response=self.llm.generate_response(f"User query :- {user_input} Tool Response :- Success - {response['success']} Content - {data if len(data)<=4000 else "The data is too long it is displayed to the user just inform about success"}")            
            print("Zara >>>",response)
            context=Chat(plugin=plugin,query=user_input,response=response,media=extras,success=success)
            self.save_to_chat(context)
           