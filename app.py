import asyncio
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from chartLinkScrapper import scrape_data
from prePareStockData import getPrompt, getMomentomStock
from tweet_utils import get_tweet_data_new, get_top_stocks

app = Flask(__name__)

# Route for the homepage with the master menu
@app.route('/')
def home():
    return render_template('index.html')

# Route for Tweeter Dashboard
@app.route('/tweeter_dashboard')
def tweeter_dashboard():
    # Get or scrape Tweet data
    tweet_data = get_tweet_data_new()
    # Get trending stocks from tweets
    top_stocks = get_top_stocks(tweet_data)

    prompt = asyncio.run(getMomentomStock(top_stocks))  # Run the async function
    print('actual response ', prompt)
    start_index = prompt.find("{")
    end_index = prompt.rfind("}") + 1  # Include the closing brace
    cleaned_response = prompt[start_index:end_index]
    data = json.loads(cleaned_response)

    # Render the dashboard template
    return render_template('dashboard.html',
                           tweets=tweet_data,
                           trending_stocks=top_stocks,
                           ai_analysis=data)

# Route for Screener Stocks
@app.route('/screener_stocks')
def screener_stocks():
    doji_stocks_data = get_doji_stocks()
    return render_template('screener_stocks.html',
                           doji_stocks=doji_stocks_data)

# Route for My Stocks
@app.route('/my_stocks')
def my_stocks():
    return render_template('my_stocks.html')

@app.route('/process_keywords', methods=['POST'])
async def process_keywords():
    # Get the keywords from the request
    data = request.get_json()
    keywords = data.get('keywords', '')

    # Convert the comma-separated string to a list
    keyword_list = [keyword.strip() for keyword in keywords.split(',') if keyword.strip()]

    # Filter stock details based on the input keywords (if applicable)
    top_stocks = [(name, 1) for name in keyword_list]

    prompt = await getMomentomStock(top_stocks)
    print('prompt', prompt)
    start_index = prompt.find("{")
    end_index = prompt.rfind("}") + 1  # Include the closing brace
    cleaned_response = prompt[start_index:end_index]
    data = json.loads(cleaned_response)
    print('data', data)
    # Return the filtered stocks or all stocks if no keywords match
    return jsonify({"stock_details": data})

def get_doji_stocks():
    today = datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
    doji_folder_path = os.path.join("Data", "ChartLink")
    dojiFileName = f"dojiStocks_{today}.json"
    doji_file_path = os.path.join(doji_folder_path, dojiFileName)
    if os.path.exists(doji_file_path):
        # If the file exists, read and return the data
        with open(doji_file_path, 'r') as json_file:
            return json.load(json_file)
    else:
        # If the file doesn't exist, scrape the data
        doji_stocks = scrape_data("https://chartink.com/screener/sam-sgreavestonedoji")
        with open(doji_file_path, 'w') as json_file:
            json.dump(doji_stocks, json_file, indent=4)
        return doji_stocks

if __name__ == '__main__':
    app.run(debug=True)
