import json
import re

from transformers import pipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model_name = "bhadresh-savani/bert-base-uncased-emotion"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
# Load a pre-trained pipeline for text classification
classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")
# Example usage
tweets = [
    "SIEZE THE SHIP ACC Limited ipo ACEINTEG",
    "Breaking Trump announced potential 100 tariff countries backing alternatives US dollar like BRICS margin",
]

with open('data.json', 'r') as file:
    stock_codes = json.load(file)

# Keywords to identify stock market-related tweets
stock_keywords = {"averages", "bear", "bearish", "book", "breakout", "breakouts", "broker", "bull", "bullish",
                     "capital", "capitalization", "candlestick", "cash", "chart", "corporate", "debt", "derivative",
                     "dividend", "dividends", "earnings", "ema", "equity", "eps", "etf", "financial", "flow",
                     "factors", "fund", "fundamental", "growth", "hedge", "high", "index", "indicators", "institutions",
                     "invest", "invested", "investing", "ipo", "leverage", "lines", "long", "low", "margin",
                     "market", "moving", "mutual", "options", "patterns", "pe", "peg", "portfolio", "profit",
                     "ratios", "revenue", "risk", "roe", "securities", "shares", "short", "sl", "stoploss",
                     "stock", "stocks", "support", "swing", "target", "technical", "trade", "trading", "trends",
                     "valuation", "venture", "volume", "volatility","expiry", "nifty","nifty50", "sensex","techno","funda","Stockmarket",
                     "sector", "banking","buying","holding","midcap","smallcap"
                     }


def is_stockmarket_related(tweet):
    # Convert tweet to lowercase
    tweet_lower = tweet.lower()

    # Check for keywords
    words = set(tweet_lower.split())
    matching_keywords = stock_keywords.intersection(words)

    # Check for stock symbols and company names
    matching_codes = []
    matching_stockNames = []
    for stock in stock_codes:
        symbol = stock["SYMBOL"].lower()
        company_name = stock["NAME OF COMPANY"].lower()

        # Match whole words for symbols and company names
        if re.search(rf"\b{re.escape(symbol)}\b", tweet_lower) or re.search(rf"\b{re.escape(company_name)}\b",
                                                                            tweet_lower):
            matching_codes.append(stock['SYMBOL'])
            matching_stockNames.append(stock['NAME OF COMPANY'])

    # Return tuple: (bool, list of matching symbols)
    return bool(matching_keywords or matching_codes), matching_codes,matching_stockNames


# Classify the tweets
'''results = [
    {
        "tweet": tweet,
        "category": "stockmarket" if is_stockmarket_related(tweet)[0] else "nonstockmarket",
        "matching_symbols": is_stockmarket_related(tweet)[2]
    }
    for tweet in tweets
]

# Print the results
for result in results:
    print(f"Tweet: {result['tweet']}\nCategory: {result['category']}\nMatching Symbols: {result['matching_symbols']}\n")
'''