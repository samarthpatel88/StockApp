import os
import re
import json
from collections import defaultdict
from datetime import datetime

from nltk.corpus import stopwords
from classificationDemo import is_stockmarket_related
from tweeterCrawlernew import get_tweet_data

# Load NLTK stopwords
stop_words = set(stopwords.words('english'))

# File paths
today = datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
tweet_folder_path = os.path.join("Data", "TweetData")
tweetFileName = f"tweeterData_{today}.json"
tweet_file_path = os.path.join(tweet_folder_path, tweetFileName)

os.makedirs(tweet_folder_path, exist_ok=True)


def clean_tweet(text):
    """Clean tweet by removing URLs, mentions, hashtags, stopwords, and extra punctuation."""
    text = re.sub(r'http\S+', '', text)  # Remove URLs
    text = re.sub(r'@\w+', '', text)  # Remove mentions
    text = re.sub(r'#(\w+)', r'\1', text)  # Remove hashtags but keep words
    text = re.sub(r'\s+', ' ', text).strip()  # Remove multiple spaces
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation

    # Remove stopwords
    words = text.split()
    cleaned_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(cleaned_words)


def clean_tweet_data(tweet_data):
    """Apply cleaning to all tweets."""
    cleaned_data = []
    for tweet in tweet_data:
        cleaned_tweet = clean_tweet(tweet["tweet"])
        # Check if the tweet is stock market-related
        result = is_stockmarket_related(cleaned_tweet)
        if result[0]:
            cleaned_data.append({
                "username": tweet["username"],
                "tweet": cleaned_tweet,
                "published_date": tweet["published_date"],
                "stockCode": result[1],
                "stockName": result[2],
            })
        else:
            print('rejected tweet:', cleaned_tweet)
    return cleaned_data


def load_tweet_data(json_file):
    """Load tweet data from a JSON file and clean it."""
    with open(json_file, 'r') as f:
        tweet_data = json.load(f)
    return clean_tweet_data(tweet_data)


def get_tweet_data_new():
    """Fetch or load tweet data."""
    if os.path.exists(tweet_file_path):
        # If the file exists, load the data
        return load_tweet_data(tweet_file_path)
    else:
        # If the file doesn't exist, scrape the data
        tweet_data = get_tweet_data()
        cleaned_tweets = clean_tweet_data(tweet_data)
        with open(tweet_file_path, 'w') as json_file:
            json.dump(cleaned_tweets, json_file, indent=4)
        return cleaned_tweets


def get_top_stocks(tweet_data, top_n=4):
    """
    Extract the top `top_n` most talked-about stocks from tweet data.

    Args:
        tweet_data (list): List of dictionaries containing tweet information.
        top_n (int): Number of top stocks to return.

    Returns:
        list: A list of strings formatted as 'SYMBOL - Full Name (count)'.
    """
    stock_count = defaultdict(int)
    for tweet in tweet_data:
        for tag in tweet.get("stockCode", []):
            stock_count[tag] += 1

    top_stocks = sorted(stock_count.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [f"{stock}" for stock, count in top_stocks]
