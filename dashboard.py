import os
import re
import chartLinkScrapper
from datetime import datetime
from flask import Flask, render_template
import json
import tweeterCraw

import nltk
from nltk.corpus import stopwords

from classificationDemo import is_stockmarket_related

# Download NLTK data
nltk.download('stopwords')
nltk.download('punkt')
# Load English stopwords
stop_words = set(stopwords.words('english'))

app = Flask(__name__)


def clean_tweet(text):
    """Clean tweet by removing URLs, mentions, hashtags, stopwords, and extra punctuation."""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)

    # Remove mentions (@username)
    text = re.sub(r'@\w+', '', text)

    # Remove hashtags but keep the words
    text = re.sub(r'#(\w+)', r'\1', text)

    # Remove multiple spaces or newlines
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove punctuation (including multiple periods, commas, exclamations)
    text = re.sub(r'[^\w\s]', '', text)  # Keep only words and spaces

    # Tokenize text and remove stopwords
    words = text.split()
    cleaned_words = [word for word in words if word.lower() not in stop_words]

    # Join the cleaned words back into a string
    return ' '.join(cleaned_words)
def clean_tweet_data(tweet_data):
    """Apply cleaning to all tweets."""
    cleaned_data = []
    for tweet in tweet_data:
        cleaned_tweet = clean_tweet(tweet["tweet"])
        # Check if the tweet is stock market-related
        is_related = is_stockmarket_related(cleaned_tweet)
        if is_related:
            cleaned_data.append({
                "username": tweet["username"],
                "tweet": cleaned_tweet,
                "published_date": tweet["published_date"]
            })
        else:
            print('rejected tweet', cleaned_tweet)
    return cleaned_data


# 1. Generate a date-wise filename for Doji stocks
today = datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
doji_folder_path = os.path.join("Data", "ChartLink")
dojiFileName = f"dojiStocks_{today}.json"
doji_file_path = os.path.join(doji_folder_path, dojiFileName)

# 2. Generate a date-wise filename for Tweet data
tweet_folder_path = os.path.join("Data", "TweetData")
tweetFileName = f"tweeterData_{today}.json"
tweet_file_path = os.path.join(tweet_folder_path, tweetFileName)

# Ensure the directories exist
os.makedirs(doji_folder_path, exist_ok=True)
os.makedirs(tweet_folder_path, exist_ok=True)

# 3. Get Doji Stocks
def get_doji_stocks():
    if os.path.exists(doji_file_path):
        # If the file exists, read and return the data
        with open(doji_file_path, 'r') as json_file:
            data = json.load(json_file)
            return data
    else:
        # If the file doesn't exist, scrape the data
        doji_stocks = chartLinkScrapper.scrape_data(
            "https://chartink.com/screener/sam-sgreavestonedoji"
        )
        # Save the data to a new file
        with open(doji_file_path, 'w') as json_file:
            json.dump(doji_stocks, json_file, indent=4)
        return doji_stocks

# 4. Load Tweet Data from JSON
def load_tweet_data(json_file):
    with open(json_file, 'r') as f:
        tweet_data = json.load(f)
        cleaned_tweets = clean_tweet_data(tweet_data)
    return cleaned_tweets

# 5. Get or Fetch Tweet Data
def get_tweet_data():
    if os.path.exists(tweet_file_path):
        # If the file exists, load the data
        return load_tweet_data(tweet_file_path)
    else:
        # If the file doesn't exist, scrape the data
        tweet_data = tweeterCraw.getTweetData()
        cleaned_tweets = clean_tweet_data(tweet_data)
        print('before json', cleaned_tweets)
        # Save the data to a new file
        with open(tweet_file_path, 'w') as json_file:
            json.dump(cleaned_tweets, json_file, indent=4)
        return cleaned_tweets

# 6. Define Routes for the Dashboard
@app.route('/')
def dashboard():
    # Get or scrape Doji stocks data
    doji_stocks_data = get_doji_stocks()
    # Get or scrape Tweet data
    tweet_data = get_tweet_data()

    # Render the dashboard template
    return render_template('dashboard.html',
                           doji_stocks=doji_stocks_data,
                           tweets=tweet_data)

# 7. Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
