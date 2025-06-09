import pyttsx3
import requests
import os
import trafilatura
from dotenv import load_dotenv
from errHandler import ErrorHandler
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import re
import webbrowser
from bs4 import BeautifulSoup
import time
from datetime import date,timedelta
from infra import LLM
from pypdf import PdfReader
import tweepy
import cv2
from huggingface_hub import InferenceClient
import numpy as np


# ------------------------------ Exact Env file path ------------------------------
load_dotenv('D:\\zara_v1\\.env')

def output_json(success,result,extras=None):
    return {"success":success,"data":result,"extras":extras}


# ------------------------------ Use if you want zara to use TTS ------------------------------
def  speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)     
    engine.setProperty('volume', 1.0)  

    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  

    engine.say(text)
    engine.runAndWait() 
    engine.stop()      



class Weather(ErrorHandler):
    def __init__(self):
        super().__init__()
        self._description = "Fetches current weather and forecast for a given location using WeatherAPI.\n   Parameters:- {location}"
        self._api_key = os.getenv('WEATHER_API_KEY')
        self._url = "http://api.weatherapi.com/v1/forecast.json?key={}&q={}&aqi=no"

    def _fetch_weather(self, location):
        url = self._url.format( self._api_key, location)
        data = requests.get(url)
        if data.status_code == 200:
            return data.json()
        raise RuntimeError(f"Weather Module doesn't work with status code {data.status_code} and content {data.json()['error']}")

    def _format_data(self, data):
        location = data['location']['name']
        
        condition = data['current']['condition']['text']
        temp = data['current']['temp_c']
        feels_like = data['current']['feelslike_c']
        humidity = data['current']['humidity']
        
   
        forecast_today = data['forecast']['forecastday'][0]['day']
        max_temp = forecast_today['maxtemp_c']
        min_temp = forecast_today['mintemp_c']
        chance_of_rain = forecast_today.get('daily_chance_of_rain', 0)
        forecast_condition = forecast_today['condition']['text']

        return (
            f"Currently, it's {condition.lower()} in {location} with {temp}°C (feels like {feels_like}°C) "
            f"and humidity at {humidity}%. "
            f"Today's forecast: {forecast_condition.lower()}, highs of {max_temp}°C and lows of {min_temp}°C. "
            f"Chance of rain is {chance_of_rain}%."
        )


    def main(self, location="india",user_input=""):
        data = self._format_data(self._fetch_weather(location))
        if isinstance(data,dict) and data.get('success') is False:
            return output_json(success=False,result=data.get('error'))
        return output_json(success=True,result=data)
    
    

    
class News(ErrorHandler):
    def __init__(self):
        super().__init__()
        self._description = (
            "Fetches the latest news articles based on a specific topic using NewsAPI.\n   Parameters:- {topic}"
        )
        self._api_url = "https://newsapi.org/v2/everything?q={}&from={}&sortBy=publishedAt&apiKey={}"
        self._api_key = os.getenv('NEWS_API_KEY')

    def _news_format(self, news):
        return f"*{news['source']['name']}*\n{news['description']}\n"

    def _filter_data(self, data):
        articles = data['articles'][:5]
        formatted_articles = list(map(self._news_format, articles))
        links = [article['url'] for article in articles]
        return "\n".join(formatted_articles)+"\nSummarize and explain to the user about each news", links

    def _fetch_news(self, topic):
        url = self._api_url.format(
            topic,
            (date.today() - timedelta(days=1)).isoformat(),
            self._api_key
        )
        response = requests.get(url)
        if response.status_code == 200:
            return self._filter_data(response.json())

        try:
            error_message = response.json().get('message', 'No message provided')
        except Exception:
            error_message = response.content.decode('utf-8')

        raise RuntimeError(
            f"News API Error:\n"
            f"Topic: '{topic}'\n"
            f"Status Code: {response.status_code}\n"
            f"Message: {error_message}"
        )

    def main(self, topic="india",user_input=""):
        data = self._fetch_news(topic)
        if isinstance(data, dict) and data.get('success') is False:
            return output_json(success=False, result=data.get('error'))

        content, links = data
        return output_json(success=True, result=content, extras=links)



class GoogleSearch(ErrorHandler):
    def __init__(self):
        super().__init__()
        self._description = "Performs a Google search and scrapes Wikipedia content for the search topic. use when the user explcitly asks for google search.\n   Parameters:- {topic}"
        self._api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self._cx = os.getenv("GOOGLE_CSX_ID")
        
        
    def _scrape_webpage(self,data):
        soup=BeautifulSoup(data,'html.parser')
        results = soup.find('div', id='mw-content-text')
        results=results.find_all('p')
        results=list(map(lambda x:x.text ,results))
        return '\n'.join([item for item in results if len(item)>50])
        
    
    def _scrape_with_trafilatura(self,url):
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if result:
                result = result[:3500]
                prompt = f"Summarize the following article:\n\n{result}"
                return prompt
        return "Failed to extract article content."
        
    def _get_webpage(self,link):
        response=requests.get(link)
        return self._scrape_webpage(response.content.decode('utf-8'))
    
    def _do_google_search(self, topic):
        url = f"https://www.googleapis.com/customsearch/v1?key={self._api_key}&cx={self._cx}&q={topic} wikipedia"
        response = requests.get(url)
        if response.status_code==200:
            return self._scrape_with_trafilatura(response.json()['items'][0]['formattedUrl']),url
        else:
            raise RuntimeError(f"Error in Google search with status code : {response.status_code} Message : {response.content.decode('utf-8')}")
    
    def main(self, topic='',user_input=""):
        data,url=self._do_google_search(topic)
        if isinstance(data,dict) and data.get('success') is False:
            return output_json(success=False,result=data.get('error'))
        return output_json(success=True,result=data,extras=[url])


class Youtube(ErrorHandler):
    def __init__(self):
        super().__init__()
        self._description = "Searches for YouTube videos based on a topic and plays the first result.\n   Parameters:- {topic}"
        self._link="https://www.googleapis.com/youtube/v3/search?part=snippet&q={}&key={}"
        self._api_key=os.getenv('YOUTUBE_API_KEY')
        self._watch_link="https://www.youtube.com/watch?v={}"
    
    def _play_video(self,data):
        watch_link=self._watch_link.format(data[0]['id']['videoId'])
        webbrowser.open(watch_link)
        return watch_link
    
    
    def main(self,topic='',user_input=""):
        url=self._link.format(topic,self._api_key)
        response=requests.get(url)
        if response.status_code==200:
            link=self._play_video(response.json()['items'])
            return output_json(success=True,result="Playing",extras=link)
        return output_json(success=False,result="There was an error playing video")
        
class PdfReaderModule(ErrorHandler):
    def __init__(self):
        super().__init__()
        self._description = "Reads and extracts text from a PDF file.\n   Parameters:- {string} Path of the file"

    def _extract_path(self, text):
        match = re.search(r'["\']?([A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]+\.pdf)["\']?', text)
        return match.group(1) if match else None

    def main(self, string='', user_input=''):
        path = self._extract_path(user_input)
        print("Extracted PDF Path:", path)
        
        if path and os.path.exists(path):
            pdf_reader = PdfReader(path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n\n"
            print("Length of Extracted Text:", len(text))
            return output_json(success=True, result=text)
        else:
            return output_json(success=False, result="File not found or invalid path.")



class GenerateImage(ErrorHandler):
    def __init__(self):
        super().__init__()
        self._client = InferenceClient(
       api_key=os.getenv('HF_TOKEN'),
        )
        self._description = "Generates an image from a text prompt. Use when the user says 'generate an image' or provides a specific description like 'Generate a sunset over the ocean.' If no prompt is provided, generate a random landscape or scene.\n   Parameters:- {prompt}"
    def main(self,prompt='',user_input=""):
        output=self._client.text_to_image(prompt,model="black-forest-labs/FLUX.1-dev")
        output.show()
        img_path=f"D:\\zara_v1\\images\\medusa_gen_image_{time.time()}.jpg"
        output.save(img_path)
        return output_json(True,"Image Created and visible to the user inform the user",extras=img_path)
  
    
class X(ErrorHandler):
    def __init__(self):
        super().__init__()

        self._description="""X module posts tweets to Twitter when the user tells Zara to tweet something."""

        self._prompt=(
    "your name is Zara .You are a social media assistant specialized in writing short, engaging tweets. "
    "Your job is to take user input and convert it into a concise, well-written tweet. "
    "Only return the tweet — no explanations, no hashtags unless naturally fitting, no formatting. "
    "Keep it under 280 characters, ideally punchy and clear. Assume the tweet will be posted as-is."
)
        self.llm=LLM('',self._prompt)
        self._x_handle=tweepy.Client(consumer_key=os.getenv('X_API_KEY'),
                                     consumer_secret=os.getenv('X_API_SECRET'),
                                     access_token=os.getenv('X_ACCESS_TOKEN'),
                                     access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'))
        
    def main(self,keywords,user_input=''):
        try:
            tweet=self.llm.generate_response(f"Here the user context genreate a short tweet {user_input}")
            self._x_handle.create_tweet(text=tweet)
            return output_json(True,"Tweet Posted",extras=tweet)
        except Exception as e:
            print('Exception :-',e)
            return output_json(False,"There was an error posting the tweet")    