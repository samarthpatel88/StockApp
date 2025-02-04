import json
import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

tweet_objects = []


def scroll_down_slowly(page):
    """Scrolls down the page to load more tweets dynamically."""
    for _ in range(3):  # Scroll multiple times for better coverage
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)


def get_tweets(page):
    """Extracts tweets from the current Twitter page."""
    articles = page.query_selector_all("article[data-testid='tweet']")
    user_names, time_stamps, tweets, published_dates = [], [], [], []

    for article in articles:
        time_element = article.query_selector("[datetime]")

        if time_element:
            datetime_value = time_element.get_attribute("datetime")

            user_name_element = article.query_selector("div[data-testid='User-Name']")
            if user_name_element:
                user_name = user_name_element.text_content().split('\n')[0]
                cleaned_user_name = user_name.split('@')[0].strip()

                time_stamp = datetime.strptime(datetime_value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(microsecond=0)
                formatted_date = time_stamp.strftime("%d %b, %Y")

                tweet_element = article.query_selector("div[data-testid='tweetText']")
                tweet = tweet_element.text_content() if tweet_element else ""

                # Ensure tweet is recent (within last 2 days)
                date_to_compare = (datetime.utcnow() - timedelta(days=2)).replace(microsecond=0)
                if time_stamp > date_to_compare:
                    published_dates.append(formatted_date)
                    tweets.append(tweet)
                    user_names.append(cleaned_user_name)

    return user_names, published_dates, tweets


def scrape_tweets(page, unique_tweets):
    """Scrapes tweets while avoiding duplicates."""
    user_names, published_dates, tweets = get_tweets(page)

    for user_name, published_date, tweet in zip(user_names, published_dates, tweets):
        tweet_hash = hash(tweet)
        unique_tweet_key = f"{user_name}-{published_date}-{tweet_hash}"

        if unique_tweet_key not in unique_tweets:
            print('tweet:', tweet)
            unique_tweets.add(unique_tweet_key)
            tweet_objects.append({
                "username": user_name,
                "tweet": tweet,
                "published_date": published_date,
            })

    scroll_down_slowly(page)


def login_twitter(page, username, password):
    """Logs into Twitter using provided credentials."""
    page.goto("https://twitter.com/i/flow/login", timeout=60000, wait_until="load")

    page.fill('input[autocomplete="username"]', username)
    page.keyboard.press('Enter')
    page.wait_for_selector('input[name="password"]', timeout=60000)  # Wait until password field appears
    page.fill('input[name="password"]', password)
    page.keyboard.press('Enter')
    page.wait_for_selector("nav[aria-label='Primary']", timeout=60000)  # Wait for homepage to load


def get_tweet_data():
    """Fetches tweets from multiple Twitter accounts and saves them."""
    twitter_handlers = ["Abhi4Research", "AimInvestments", "viveksingh2010", "AnirbanManna10", "dhuperji", "SnehaSSR", "TradingMarvel", "sainaman2", "sushilpathiyar", "Trading0secrets",
                        "indian_stockss","nilishamantri_","MySoctr", "rdkriplani"]

    handlers_user1 = twitter_handlers[:len(twitter_handlers) // 2]
    handlers_user2 = twitter_handlers[len(twitter_handlers) // 2:]

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
                page.wait_for_selector("article[data-testid='tweet']", timeout=100000)  # Ensure tweets load
                scrape_tweets(page, unique_tweets)

            page.close()

        browser.close()

    save_tweets_to_json()
    return tweet_objects


def save_tweets_to_json():
    """Saves tweet objects to a JSON file."""
    today = datetime.today().strftime('%Y-%m-%d')
    folder_path = os.path.join("Data", "TweetData")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"tweeterData_{today}.json")

    append_or_create_json(file_path, tweet_objects)


def append_or_create_json(file_path, tweet_objects):
    """Appends tweets to an existing JSON file or creates a new one if it does not exist."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)

        existing_data.extend(tweet_objects)

        with open(file_path, 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)
    else:
        with open(file_path, 'w') as json_file:
            json.dump(tweet_objects, json_file, indent=4)


if __name__ == "__main__":
    get_tweet_data()
