# -*- coding: utf-8 -*-
"""
Created on Wed May 18 14:32:23 2022

@author: Lenovo
"""
##############################################################################
# Libraries
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests, lxml, re, json
from datetime import datetime
from textblob import TextBlob 
import googletrans
from googletrans import Translator

##############################################################################
# Functions
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# Web Scrape function
def scrape_google_store_app():
    html = requests.get("https://play.google.com/store/apps/details", params=params, headers=headers, timeout=10).text
    soup = BeautifulSoup(html, "lxml")

    # where all app data will be stored
    app_data = []

    # <script> position is not changing that's why [12] index being selected. Other <script> tags position are changing.
    # [12] index is a basic app information
    # https://regex101.com/r/DrK0ih/1
    basic_app_info = json.loads(re.findall(r"<script nonce=\".*\" type=\"application/ld\+json\">(.*?)</script>",str(soup.select("script")[12]), re.DOTALL)[0])

    app_name = basic_app_info["name"]
    app_type = basic_app_info["@type"]
    app_url = basic_app_info["url"]
    app_description = basic_app_info["description"].replace("\n", "")  # replace new line character to nothing
    app_category = basic_app_info["applicationCategory"]
    app_operating_system = basic_app_info["operatingSystem"]
    app_main_thumbnail = basic_app_info["image"]

    app_content_rating = basic_app_info["contentRating"]
    app_rating = round(float(basic_app_info["aggregateRating"]["ratingValue"]), 1)  # 4.287856 -> 4.3
    app_reviews = basic_app_info["aggregateRating"]["ratingCount"]

    app_author = basic_app_info["author"]["name"]
    app_author_url = basic_app_info["author"]["url"]

    # https://regex101.com/r/VX8E7U/1
    app_images_data = re.findall(r",\[\d{3,4},\d{3,4}\],.*?(https.*?)\"", str(soup.select("script")))
    # delete duplicates from app_images_data
    app_images = [item for item in app_images_data if app_images_data.count(item) == 1]

    # User comments
    app_user_comments = []

    # https://regex101.com/r/SrP5DS/1
    app_user_reviews_data = re.findall(r"(\[\"gp.*?);</script>",
                                       str(soup.select("script")), re.DOTALL)

    for review in app_user_reviews_data:
        # https://regex101.com/r/M24tiM/1
        user_name = re.findall(r"\"gp:.*?\",\s?\[\"(.*?)\",", str(review))
        # https://regex101.com/r/TGgR45/1
        user_avatar = [avatar.replace('"', "") for avatar in re.findall(r"\"gp:.*?\"(https.*?\")", str(review))]

        # replace single/double quotes at the start/end of a string
        # https://regex101.com/r/iHPOrI/1
        user_comments = [comment.replace('"', "").replace("'", "") for comment in
                        re.findall(r"gp:.*?https:.*?]]],\s?\d+?,.*?,\s?(.*?),\s?\[\d+,", str(review))]

        # comment utc timestamp
        # use datetime.utcfromtimestamp(int(date)).date() to have only a date
        user_comment_date = [str(datetime.utcfromtimestamp(int(date))) for date in re.findall(r"\[(\d+),", str(review))]

        # https://regex101.com/r/GrbH9A/1
        user_comment_id = [ids.replace('"', "") for ids in re.findall(r"\[\"(gp.*?),", str(review))]
        # https://regex101.com/r/jRaaQg/1
        user_comment_likes = re.findall(r",?\d+\],?(\d+),?", str(review))
        # https://regex101.com/r/Z7vFqa/1
        user_comment_app_rating = re.findall(r"\"gp.*?https.*?\],(.*?)?,", str(review))

        for name, avatar, comment, date, comment_id, likes, user_app_rating in zip(user_name,user_avatar,user_comments,user_comment_date,user_comment_id,user_comment_likes,user_comment_app_rating):
            app_user_comments.append({
                "user_name": name,
                #"user_avatar": avatar,
                "comment": comment,
                #"user_app_rating": user_app_rating,
                #"user__comment_likes": likes,
                #"user_comment_published_at": date,
                #"user_comment_id": comment_id
            })

        app_data.append({
            "app_name": app_name,
            "app_type": app_type,
            "app_url": app_url,
            "app_main_thumbnail": app_main_thumbnail,
            "app_description": app_description,
            "app_content_rating": app_content_rating,
            "app_category": app_category,
            "app_operating_system": app_operating_system,
            "app_rating": app_rating,
            "app_reviews": app_reviews,
            "app_author": app_author,
            "app_author_url": app_author_url,
            "app_screenshots": app_images
        })

        #return {"app_data": app_data, "app_user_comments": app_user_comments}
        return {"app_user_comments": app_user_comments}

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# Data cleaning and filtering function
def clean_tweet(tweet):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        '''
        new_string = re.sub(r"[^a-zA-Z0-9]"," ",tweet)
        return new_string

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# Translate and sentiment function
def get_tweet_sentiment(tweet):
    translator = Translator()
    analysis = clean_tweet(tweet)
    analysis_ready = translator.translate(analysis, dest='en')
    analysis_ready1 = TextBlob(analysis_ready.text)     
    if analysis_ready1.sentiment.polarity > 0: 
        return 'positive'
    elif analysis_ready1.sentiment.polarity == 0: 
        return 'neutral'
    else: 
        return 'negative'

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# Hearts generator
def hearts_gen(tweet):
    translator = Translator()
    analysis = clean_tweet(tweet)
    analysis_ready = translator.translate(analysis, dest='en')
    analysis_ready1 = TextBlob(analysis_ready.text)   
    coefficient = analysis_ready1.sentiment.polarity       
    if (-1<=coefficient<=-0.5): 
        heart = 0
    if (-0.5<coefficient<=-0.2): 
        heart = 1
    if (-0.2<coefficient<=0.1): 
        heart = 2
    if (0.1<coefficient<=0.4): 
        heart = 3
    if (0.4<coefficient<=0.7): 
        heart = 4
    if (0.7<coefficient<=1): 
        heart = 5
    return heart, coefficient

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

##############################################################################
# User-agent headers to act as a "real" user visit
headers = {
    "user-agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
}

# search query params
params = {
    "id": "com.nintendo.zara",  # app name
    "gl": "US"                  # country
}

##############################################################################
# Data Structuration 
data_dict = json.dumps(scrape_google_store_app(), indent=2)
data_items = pd.read_json(data_dict)

df3 = pd.DataFrame()
df4 = pd.DataFrame()
df5 = pd.DataFrame()
df6 = pd.DataFrame()

for i in range(0,len(data_items)):
    df = data_items['app_user_comments'][i]
    df1 = str(df)
    df2 = df1.split("comment")
    df3 = df3.append(df2)
df3['col'] = df3 
df4 = df3['col'][0] 
df4 = df4.reset_index()
df5 = df3['col'][1] 
df5 = df5.reset_index()
df6['username'] = df4['col']
df6['comment'] = df5['col']

##############################################################################
# Weighing of opinions

df7 = []
for i in range(0,len(df6)):
    a = get_tweet_sentiment(df6['comment'][i])
    df7.append(a)
df6['opinion rating'] = pd.DataFrame(df7)
#print(df6)

##############################################################################
# Hearts generator

df8 = []
for i in range(0,len(df6)):
    b = hearts_gen(df6['comment'][i])
    df8.append(b[0])
df6['hearts'] = pd.DataFrame(df8)
print(df6)

##############################################################################
















