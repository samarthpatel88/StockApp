import json
import os
import re
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


def login_twitter(page, username, password):
    url = "https://twitter.com/i/flow/login"
    page.goto(url,timeout=60000, wait_until="load")
    page.fill('input[autocomplete="username"]', username)
    page.keyboard.press('Enter')
    page.wait_for_timeout(3000)
    page.fill('input[name="password"]', password)
    page.keyboard.press('Enter')
    page.wait_for_timeout(4000)  # Allow time for login to complete


def scrape_tweets(page, unique_tweets):
    user_names, published_dates, tweets = get_tweets(page)

    for user_name, published_date, tweet in zip(user_names, published_dates, tweets):
        highlighted_tweet = highlight_hashtags(tweet)
        unique_tweet_key = f"{user_name}-{published_date}-{highlighted_tweet}"

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


def highlight_hashtags(tweet):
    return re.sub(r'#(\w+)', r'<b>#\1</b>', tweet)


def getTweetData():
    twitter_handlers = ["Abhi4Research","AimInvestments","viveksingh2010","AnirbanManna10","dhuperji","SnehaSSR","TradingMarvel","sainaman2","sushilpathiyar","Trading0secrets"]
    ''',"indian_stockss","nilishamantri_","MySoctr", "rdkriplani","Milind4profits","jayneshkasliwal","breakoutsfreak", "adeptmarket","tbportal","beyondtrading07","gogrithekhabri","wealthexpress21","StockInfotech","mystocks_in","saditya10p","KhapreVishal","_ChartWizard_","curious_shubh","marketViewbyPB","Deishma","KommawarSwapnil","Sahilpahwa09","fintech00","sunilgurjar01","CaVivekkhatri","KhapreVishal","itsprekshaBaid","thebigbulldeals","TbPortal","Bnf_unicorn","pahari_trader","darvasboxtrader"]'''
    '''username = "SamStockPicks" '''
    ''' password = "Bond@007" '''
    username = "AtoZKidsApp"
    password = "Atozkids@2020"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        login_twitter(page, username, password)
        unique_tweets = set()

        for target_url in twitter_handlers:
            page.goto(f"https://twitter.com/{target_url}", timeout=100000, wait_until="load")
            time.sleep(20)
            scrape_tweets(page, unique_tweets)

        today = datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
        folder_path = os.path.join("Data", "TweetData")
        filename = f"tweeterData_{today}.json"
        file_path = os.path.join(folder_path, filename)

        # Write tweet objects to JSON file
        with open(file_path, 'w') as json_file:
            json.dump(tweet_objects, json_file, indent=4)

        browser.close()
        return  tweet_objects

