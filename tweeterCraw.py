import json
import os
import time
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
tweet_objects = []


def scroll_down_slowly(page):
    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def get_tweets(page):
    articles = page.query_selector_all("article[data-testid='tweet']")
    user_names, time_stamps, tweets, published_dates = [], [], [], []

    for article in articles:
        time_element = article.query_selector("[datetime]")

        if time_element:
            datetime_value = time_element.get_attribute("datetime")

            # Extract user name
            user_name_element = article.query_selector("div[data-testid='User-Name']")
            if user_name_element:
                user_name = user_name_element.text_content().split('\n')[0]
                cleaned_user_name = user_name.split('@')[0].strip()

                time_stamp = datetime.strptime(datetime_value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(microsecond=0)
                formatted_date = time_stamp.strftime("%d %b,%Y")

                # Extract tweet text
                tweet_element = article.query_selector("div[data-testid='tweetText']")
                tweet = tweet_element.text_content() if tweet_element else ""

                date_to_compare = (datetime.utcnow() - timedelta(days=2)).replace(microsecond=0)
                if time_stamp > date_to_compare:
                    published_dates.append(formatted_date)
                    tweets.append(tweet)
                    user_names.append(cleaned_user_name)

    return user_names, published_dates, tweets

def scrape_tweets(page, unique_tweets):
    user_names, published_dates, tweets = get_tweets(page)

    for user_name, published_date, tweet in zip(user_names, published_dates, tweets):
        # Combine user_name, published_date, and a hash of the tweet content for a unique key
        tweet_hash = hash(tweet)  # Create a hash for the tweet content
        unique_tweet_key = f"{user_name}-{published_date}-{tweet_hash}"

        if unique_tweet_key not in unique_tweets:
            print('tweet', tweet)
            unique_tweets.add(unique_tweet_key)
            tweet_obj = {
                "username": user_name,
                "tweet": tweet,
                "published_date": published_date,
            }

            tweet_objects.append(tweet_obj)

    scroll_down_slowly(page)

def login_twitter(page, username, password):
    url = "https://twitter.com/i/flow/login"
    page.goto(url,timeout=60000, wait_until="load")
    page.fill('input[autocomplete="username"]', username)
    page.keyboard.press('Enter')
    page.wait_for_timeout(3000)
    page.fill('input[name="password"]', password)
    page.keyboard.press('Enter')
    page.wait_for_timeout(4000)  # Allow time for login to complete



def getTweetData():
    twitter_handlers = ["Abhi4Research", "AimInvestments", "AnirbanManna10","SnehaSSR", "TradingMarvel","Trading0secrets",
                            "indian_stockss","MySoctr", "rdkriplani","Milind4profits","jayneshkasliwal","tbportal","beyondtrading07","mystocks_in","KhapreVishal","_ChartWizard_","curious_shubh","marketViewbyPB","Deishma","KommawarSwapnil","Sahilpahwa09","fintech00",
                        "thebigbulldeals","pahari_trader","darvasboxtrader"]

    # Divide handlers into two groups
    handlers_user1 = twitter_handlers[:len(twitter_handlers) // 2]
    handlers_user2 = twitter_handlers[len(twitter_handlers) // 2:]

    # User credentials
    accounts = [
        {"username": "SamStockPicks", "password": "Bond@007", "handlers": handlers_user1},
        {"username": "AtoZKidsApp", "password": "Atozkids@2020", "handlers": handlers_user2}
    ]

    unique_tweets = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for account in accounts:
            username = account["username"]
            password = account["password"]
            handlers = account["handlers"]

            page = browser.new_page()
            login_twitter(page, username, password)

            for target_url in handlers:
                page.goto(f"https://twitter.com/{target_url}", timeout=100000, wait_until="load")
                time.sleep(20)
                scrape_tweets(page, unique_tweets)

            page.close()

        today = datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
        folder_path = os.path.join("Data", "TweetData")
        os.makedirs(folder_path, exist_ok=True)
        filename = f"tweeterData_{today}.json"
        file_path = os.path.join(folder_path, filename)

        # Write tweet objects to JSON file
        append_or_create_json(file_path, tweet_objects)

        browser.close()

    return tweet_objects


def append_or_create_json(file_path, tweet_objects):
    """
    Appends tweet_objects to an existing JSON file if it exists,
    or creates a new file and writes tweet_objects if the file does not exist.

    Args:
    - file_path (str): Path to the JSON file.
    - tweet_objects (list): List of tweet objects to be written or appended to the file.
    """
    # Check if the file already exists
    if os.path.exists(file_path):
        # If the file exists, read the existing content
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)
        # Append new data to the existing content
        existing_data.extend(tweet_objects)
        # Write the updated content back to the file
        with open(file_path, 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)
    else:
        # If the file doesn't exist, create a new one and write the data
        with open(file_path, 'w') as json_file:
            json.dump(tweet_objects, json_file, indent=4)
