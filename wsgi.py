import json
import os
from datetime import datetime

from bson import ObjectId
from flask import Flask, render_template, request, jsonify, url_for, flash
from werkzeug.utils import redirect

from chartLinkScrapper import scrape_data
from prePareStockData import get_momentum_stock, get_tweet_summary,get_tweet_newsLetter
from telegramMessage import send_message_to_telegram
from tweet_utils import get_tweet_data_new, get_top_stocks
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["trading_journal"]
trades_collection = db["trades"]
app.secret_key = "e8b7a2c9d1f03e5b7a9c1d4f2e638a01"

# Folder to store uploaded images
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for the homepage with the master menu
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/add_trade", methods=["GET", "POST"])
def add_trade():
    if request.method == "POST":
        trade_id = str(ObjectId())  # Generate a unique trade ID
        print('trade_id',trade_id)


        # Retrieve and convert price fields
        # Retrieve and convert price and quantity fields
        entry_price = float(request.form["entry_price"])
        trade_quantity = int(request.form["trade_quantity"])
        stop_loss = float(request.form["stop_loss"])
        target_price = float(request.form["target_price"])

        # Calculate the investment value automatically
        investment_value = entry_price * trade_quantity

        risk = entry_price - stop_loss

        reward = target_price - entry_price
        ratio_value = reward / risk
        risk_reward_ratio = f"{ratio_value:.2f}:1"  # Format as X.XX:1

        data = {
            "_id": trade_id,  # Store trade ID in MongoDB
            "stock_symbol": request.form["stock_symbol"],
            "stock_name": request.form["stock_name"],
            "trade_style": request.form["trade_style"],
            "market_trend": request.form["market_trend"],
            "trade_setup": request.form["trade_setup"],
            "entry_price": entry_price,
            "trade_quantity": int(request.form["trade_quantity"]),
            "entry_datetime": datetime.now(),
            "stop_loss": stop_loss,
            "target_price": target_price,
            "risk_reward_ratio": risk_reward_ratio,
            "investment_value": investment_value,
         }

        # Handle Entry Chart Image
        if "entry_chart_image" in request.files:
            file = request.files["entry_chart_image"]
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"{trade_id}_entry.{ext}"  # Save using trade ID
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                data["entry_chart_image"] = f"uploads/{filename}"

        trades_collection.insert_one(data)  # Insert into MongoDB
        flash("Trade added successfully!", "success")
        return redirect(url_for("trade_list"))

    return render_template("add_trade.html")

@app.route("/trade_list")
def trade_list():
    trades = list(trades_collection.find())
    return render_template("trade_list.html", trades=trades)

@app.route("/edit_trade/<trade_id>", methods=["GET", "POST"])
def edit_trade(trade_id):
    print('trades_collection', trades_collection)
    trade = trades_collection.find_one({"_id": trade_id})
    print('trade', trade)
    if request.method == "POST":

        # Retrieve the required fields
        entry_price = trade['entry_price']
        trade_quantity = trade['trade_quantity']

        # Retrieve the exit price if provided
        exit_price_input = request.form.get("exit_price")

        if exit_price_input:
            exit_price = float(exit_price_input)
            profit_loss_amount = (exit_price - entry_price) * trade_quantity
            profit_loss_percentage = ((exit_price - entry_price) / entry_price) * 100
        else:
            exit_price = None
            profit_loss_amount = None
            profit_loss_percentage = None
        update_data = {
            "exit_price": float(request.form["exit_price"]) if request.form["exit_price"] else None,
            "exit_datetime": datetime.now(),
            "profit_loss_amount": profit_loss_amount,
            "profit_loss_percentage": profit_loss_percentage,
            "exit_trigger": request.form["exit_trigger"],
            "notes": request.form["notes"]
        }

        # Handle Exit Chart Image
        if "exit_chart_image" in request.files:
            file = request.files["exit_chart_image"]
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"{trade_id}_exit.{ext}"  # Save using trade_id
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                update_data["exit_chart_image"] = f"uploads/{filename}"

        print('update_data',update_data)
        trades_collection.update_one({"_id": trade_id}, {"$set": update_data})
        flash("Trade updated successfully!", "success")
        return redirect(url_for("trade_list"))

    return render_template("edit_trade.html", trade=trade)

@app.route("/view_trade/<trade_id>")
def view_trade(trade_id):
    trade = trades_collection.find_one({"_id": trade_id})
    if trade:
        # Convert _id to string if needed
        trade['_id'] = str(trade['_id'])
        return render_template("view_trade.html", trade=trade)
    else:
        flash("Trade not found", "error")
        return redirect(url_for("trade_list"))

@app.route("/delete_trade/<trade_id>")
def delete_trade(trade_id):
    result = trades_collection.delete_one({"_id": trade_id})
    if result.deleted_count:
        flash("Trade deleted successfully", "success")
    else:
        flash("Trade not found", "error")
    return redirect(url_for("trade_list"))

@app.route('/send_message_telegram', methods=['POST'])
def send_message():
    tweet_data = get_tweet_data_new()
    stockSummary = get_tweet_newsLetter(tweet_data)
    result = send_message_to_telegram(stockSummary)
    return jsonify(result)


# Route for Tweeter Dashboard
@app.route('/tweeter_dashboard')
def tweeter_dashboard():
    # Get or scrape Tweet data
    tweet_data = get_tweet_data_new()
    # Get trending stocks from tweets
    top_stocks = get_top_stocks(tweet_data)

    stockSummary = get_tweet_summary(tweet_data)

    print('stockSummary', stockSummary)
    # Render the dashboard template
    return render_template('dashboard.html',
                           tweets=tweet_data,
                           trending_stocks=top_stocks,
                           stock_summary= stockSummary,
                           )

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

    prompt = await get_momentum_stock(top_stocks)
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
