import asyncio
import json
from typing import List
import google.generativeai as genai
import os
from StockDetails import StockData
from tradeline import fetch_stock_data  # Ensure this uses Async API
from tweet_utils import get_tweet_data, get_top_stocks

async def main():
    print('In Main')

async def getPrompt():
    # Fetch tweet data (non-async function, no await needed)
    tweet_data = get_tweet_data()
    # Extract top stocks from tweets
    top_stocks = get_top_stocks(tweet_data)
    return get_momentum_stock(top_stocks)

def configure_genai():
    os.environ["API_KEY"] = 'AIzaSyCTDCN5PyIgLzJE8cqW-7zuekZH1b9dwT8'
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash-latest')

# Async function to fetch stock data and generate momentum stock summary
async def get_momentum_stock(top_stocks):
    stock_urls = load_stock_urls('stocklist.json')

    if not top_stocks:
        print("Empty stock list provided")
        return None

    # Determine stock URL mapping based on input format
    if isinstance(top_stocks[0], tuple):
        urls_for_stocks = {code: stock_urls.get(code, "URL not found") for code, _ in top_stocks}
    elif isinstance(top_stocks[0], str):
        urls_for_stocks = {code: stock_urls.get(code, "URL not found") for code in top_stocks}
    else:
        print("Unsupported top_stocks format")
        return None

    valid_urls = [url for url in urls_for_stocks.values() if url != "URL not found"]
    print('Valid URLs:', valid_urls)

    # Fetch data concurrently
    tasks = [fetch_stock_data(url) for url in valid_urls]
    stock_data_list: List[StockData] = await asyncio.gather(*tasks)
    print('Stock Data List:', stock_data_list)

    # Generate prompt and AI response
    prompt_text = create_combined_prompt_text_new(stock_data_list)
    return generate_ai_response(prompt_text)

def get_tweet_summary(tweetdata: str):
    prompt = generate_tweet_summary_prompt(tweetdata)
    return generate_ai_response(prompt)


def get_tweet_newsLetter(tweetdata: str):
    prompt = generate_tweet_newsLetter_prompt(tweetdata)
    return generate_ai_response(prompt)

# Function to generate AI response
def generate_ai_response(prompt: str) -> str:
    model = configure_genai()
    response = model.generate_content(prompt)
    return response.text

def load_stock_urls(file_path: str) -> dict:
    """Load stock URLs from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)


# Function to generate prompt text for tweet summary
def generate_tweet_summary_prompt(tweetdata: str) -> str:
    return f"""
    From the given list of tweet data:
    {tweetdata}

    Identify the top three most discussed stocks along with a brief summary of their sentiment and key reason.
    Present the result in the following format:

    Stocks to watch:
    1. RVNL (Positive) – Received an order from the railway department.
    2. Apple (Negative) – Promoters sold a significant stake.
    3. Microsoft (Neutral) – Chart analysis indicates stability.

    Since Twitter has a 280-character limit, ensure the tweet does not exceed this limit, including spaces.

    Don't add any disclaimer, as this is just for personal and educational purposes only.
    """

def generate_tweet_newsLetter_prompt(tweetdata: str) -> str:
    return f"""
    Given the following stock market-related tweets, generate a concise yet informative newsletter-style summary. The newsletter should include:

    1. **Headlines:** Extract key stock-related updates from the tweets and format them as engaging headlines.
    2. **Trending Stocks:** Identify the most frequently mentioned stocks and list them under a 'Trending Stocks' section.
    3. **Market Sentiment:** Provide a brief analysis of the market sentiment based on tweet content (e.g., positive, negative, or neutral outlook).
    4. **Key Insights:** Summarize important takeaways from the tweets, highlighting any new developments, agreements, or upcoming market movements.

    ### Input Data:
    {tweetdata}

    ### Output Format Example:

    **📢 Daily Stock Market Update – [Date]**

    🔹 **Top Headlines:**
    - Servotech Renewable signs an agreement with France-based Watt Well SAS to manufacture EV charger components in India.
    - IREDA and Tata Technologies focus on new developments, as per NSE release.

    📈 **Trending Stocks:**
    - Focus Lighting and Fixtures Limited (FOCUS)
    - Indian Renewable Energy Development Agency Limited (IREDA)
    - Servotech Power Systems Limited (SERVOTECH)

    📊 **Market Sentiment:** 
    - Mostly neutral with discussions on market reversals and Nifty’s possible movement.
    - Some optimism around renewable energy and EV sector developments.

    💡 **Key Insights:**
    - A new stock screener is being discussed for market reversals.
    - Traders are speculating on whether Nifty will open green, red, or flat tomorrow.

    Generate a well-structured and engaging newsletter based on the provided data.
    """

def generate_swing_trade_prompt(stock_data: str) -> str:
    return f"""
    From the given stock data:
    {stock_data}

    Identify the best bullish stock for a high-probability swing trade based on the following criteria:
    - EMA alignment: EMA20 > EMA50 > EMA100 (indicating a strong uptrend)
    - Price above key EMAs (EMA20 and EMA50) confirming bullish strength
    - Price closed above the previous day's high
    - RSI between 55 and 75 (showing bullish momentum but not overbought)
    - MACD line above the signal line (confirming upward momentum)
    - Volume higher than the 20-day average (indicating accumulation)
    - ATR suggests medium to high volatility (ensuring enough price movement)
    - No major resistance nearby
    - Strong support level for stop-loss placement
    - Risk-reward ratio of at least 1:2

    Present the result in the following format:

    Stock to Trade:
    - **Stock Symbol:** RVNL
    - **Trend Strength:** Strong
    - **Price Above Key EMAs:** Yes
    - **Price Above Previous Day High:** Yes
    - **RSI Between 55 and 75:** Yes
    - **MACD Bullish:** Yes
    - **Volume Surge:** Yes
    - **ATR Level:** High
    - **Major Resistance Nearby:** No
    - **Support Level:** 250
    - **Target:** 280
    - **Stop Loss:** 240
    - **Risk-Reward Ratio:** 1:3
    - **Expected Return:** 10%
    - **Momentum Score:** 6/6

    Ensure the output remains concise and formatted clearly for easy decision-making.
    Do not add any disclaimer, as this is just for personal and educational purposes only.
    """

def create_combined_prompt_text(stocks_data_list):
    combined_prompt = (
        "Please analyze the below stocks and choose only one best stock among them.\n"
        "Consider the following criteria to identify bullish stocks:\n"
        "- Prioritize stocks where EMA is in the sequence EMA10 > EMA20 > EMA50\n"
        "- Current price is greater than the previous day's price\n"
        "- Daily volume average is greater than weekly and monthly volume\n"
        "- No major resistance nearby, and RSI is above 60\n\n"
        "Provide the analysis in the following structured format:\n"
        "{\n"
        '  "stockToTrade": "StockName",\n'
        '  "stockTrend": "Bullish" or "NotBullish",\n'
        '  "priceAbovePreviousDayHigh": "Yes" or "No",\n'
        '  "volume": "Yes" or "No",\n'
        '  "rsiAbove60": "Yes" or "No",\n'
        '  "majorResistanceNearby": "Yes" or "No",\n'
        '  "target": "TargetValue",\n'
        '  "stopLoss": "StopLossValue",\n'
        '  "resistance": "ResistanceValue",\n'
        '  "support": "SupportValue",\n'
        '  "riskReward": "RiskRewardValue",\n'
        '  "momentumScore": "Score from 1 to 6"\n'
        "}\n\n"
        "Please update the respective value in above format."
    )

    for stock_data in stocks_data_list:  # stock_data is a StockData instance
        # Stock Price Analysis
        stock_price_analysis = stock_data.stock_price_analysis
        price_analysis_summary = (
            f"Day Range: High {getattr(stock_price_analysis.day_price_range, 'high', 'N/A')}, "
            f"Low {getattr(stock_price_analysis.day_price_range, 'low', 'N/A')}\n"
            f"Week Range: High {getattr(stock_price_analysis.week_price_range, 'high', 'N/A')}, "
            f"Low {getattr(stock_price_analysis.week_price_range, 'low', 'N/A')}\n"
            f"Month Range: High {getattr(stock_price_analysis.month_price_range, 'high', 'N/A')}, "
            f"Low {getattr(stock_price_analysis.month_price_range, 'low', 'N/A')}\n"
            f"52-Week Range: {getattr(stock_price_analysis, 'year_52_price_range', 'N/A')}\n"
        )

        # Analyst Recommendations
        analyst_recommendations = stock_data.analyst_recommendations
        if analyst_recommendations and analyst_recommendations.brokerage:
            recommendations_summary = (
                f"Current Recommendation: {analyst_recommendations.current_recommendation or 'N/A'}\n"
                f"Total Analysts: {analyst_recommendations.total_analysts or 0}\n"
                f"Brokerage: Strong Buy {getattr(analyst_recommendations.brokerage, 'strong_buy', 0)}, "
                f"Buy {getattr(analyst_recommendations.brokerage, 'buy', 0)}, "
                f"Hold {getattr(analyst_recommendations.brokerage, 'hold', 0)}, "
                f"Sell {getattr(analyst_recommendations.brokerage, 'sell', 0)}, "
                f"Strong Sell {getattr(analyst_recommendations.brokerage, 'strong_sell', 0)}\n"
            )
        else:
            recommendations_summary = (
                f"Current Recommendation: {getattr(analyst_recommendations, 'current_recommendation', 'N/A')}\n"
                f"Total Analysts: {getattr(analyst_recommendations, 'total_analysts', 0)}\n"
                f"Brokerage data is unavailable.\n"
            )

        # Technical Analysis
        technical_analysis = stock_data.technical_analysis
        if technical_analysis:
            technical_analysis_summary = (
                f"Current Price: {getattr(technical_analysis, 'current_price', 'N/A')}\n"
                f"RSI: {getattr(technical_analysis, 'rsi', 'N/A')}, "
                f"MACD: {getattr(technical_analysis, 'macd', 'N/A')}\n"
                f"Day ADX: {getattr(technical_analysis, 'day_adx', 'N/A')}, "
                f"Day ATR: {getattr(technical_analysis, 'day_atr', 'N/A')}\n"
                f"Bullish MAs: {getattr(technical_analysis, 'total_bullish_moving_averages', 'N/A')}, "
                f"Bearish MAs: {getattr(technical_analysis, 'total_bearish_moving_averages', 'N/A')}\n"
                f"EMA: {', '.join([f'{k}: {v}' for k, v in (technical_analysis.ema or {}).items()])}\n"
                f"Resistance Levels: {', '.join([f'{k}: {v}' for k, v in (technical_analysis.resistance or {}).items()])}\n"
                f"Support Levels: {', '.join([f'{k}: {v}' for k, v in (technical_analysis.support or {}).items()])}\n"
                f"Volume: Daily {technical_analysis.volume.get('daily', 'N/A')}, "
                f"Weekly {technical_analysis.volume.get('weekly', 'N/A')}, "
                f"Monthly {technical_analysis.volume.get('monthly', 'N/A')}\n"
            )
        else:
            technical_analysis_summary = "Technical Analysis data is unavailable.\n"

        # Combine all details
        combined_prompt += (
            f"Stock name '{stock_data.stock_name}' (Code: {stock_data.stock_code}):\n"
            f"Momentum Score: {getattr(stock_data, 'momentum_score', 'N/A')} "
            f"({getattr(stock_data, 'momentum_comment', 'N/A')})\n\n"
            f"Price Analysis:\n{price_analysis_summary}\n"
            f"Analyst Recommendations:\n{recommendations_summary}\n"
            f"Technical Analysis:\n{technical_analysis_summary}\n\n"
        )

    print('combined_prompt', combined_prompt)
    return combined_prompt

def create_combined_prompt_text_new(stocks_data_list):
    combined_prompt = (
        "From the given stock data:\n"
        "Identify the best bullish stock for a high-probability swing trade based on the following criteria:\n"
        "- EMA alignment: EMA20 > EMA50 > EMA100 (indicating a strong uptrend)\n"
        "- Price above key EMAs (EMA20 and EMA50) confirming bullish strength\n"
        "- Price closed above the previous day's high\n"
        "- RSI between 55 and 75 (showing bullish momentum but not overbought)\n"
        "- MACD line above the signal line (confirming upward momentum)\n"
        "- Volume higher than the 20-day average (indicating accumulation)\n"
        "- ATR suggests medium to high volatility (ensuring enough price movement)\n"
        "- No major resistance nearby\n"
        "- Strong support level for stop-loss placement\n"
        "- Risk-reward ratio of at least 1:2\n\n"
        "Provide the analysis in the following structured format:\n"
        "{\n"
        "  \"stockToTrade\": \"StockName\",\n"
        "  \"trendStrength\": \"Strong\" or \"Moderate\" or \"Weak\",\n"
        "  \"priceAboveKeyEMAs\": \"Yes\" or \"No\",\n"
        "  \"priceAbovePreviousDayHigh\": \"Yes\" or \"No\",\n"
        "  \"rsiBetween55And75\": \"Yes\" or \"No\",\n"
        "  \"macdBullish\": \"Yes\" or \"No\",\n"
        "  \"volumeSurge\": \"Yes\" or \"No\",\n"
        "  \"atrLevel\": \"High\" or \"Medium\" or \"Low\",\n"
        "  \"majorResistanceNearby\": \"Yes\" or \"No\",\n"
        "  \"supportLevel\": \"SupportValue\",\n"
        "  \"target\": \"TargetValue\",\n"
        "  \"stopLoss\": \"StopLossValue\",\n"
        "  \"riskRewardRatio\": \"RiskRewardValue\",\n"
        "  \"expectedReturn\": \"ExpectedReturnPercentage\",\n"
        "  \"momentumScore\": \"Score from 1 to 6\"\n"
        "}\n\n"
        "Ensure the output remains concise and formatted clearly for easy decision-making.\n"
        "Do not add any disclaimer, as this is just for personal and educational purposes only.\n"
    )

    for stock_data in stocks_data_list:  # stock_data is a StockData instance
        # Stock Price Analysis
        stock_price_analysis = stock_data.stock_price_analysis
        price_analysis_summary = (
            f"Day Range: High {getattr(stock_price_analysis.day_price_range, 'high', 'N/A')}, "
            f"Low {getattr(stock_price_analysis.day_price_range, 'low', 'N/A')}\n"
            f"Week Range: High {getattr(stock_price_analysis.week_price_range, 'high', 'N/A')}, "
            f"Low {getattr(stock_price_analysis.week_price_range, 'low', 'N/A')}\n"
            f"Month Range: High {getattr(stock_price_analysis.month_price_range, 'high', 'N/A')}, "
            f"Low {getattr(stock_price_analysis.month_price_range, 'low', 'N/A')}\n"
            f"52-Week Range: {getattr(stock_price_analysis, 'year_52_price_range', 'N/A')}\n"
        )

        # Analyst Recommendations
        analyst_recommendations = stock_data.analyst_recommendations
        if analyst_recommendations and analyst_recommendations.brokerage:
            recommendations_summary = (
                f"Current Recommendation: {analyst_recommendations.current_recommendation or 'N/A'}\n"
                f"Total Analysts: {analyst_recommendations.total_analysts or 0}\n"
                f"Brokerage: Strong Buy {getattr(analyst_recommendations.brokerage, 'strong_buy', 0)}, "
                f"Buy {getattr(analyst_recommendations.brokerage, 'buy', 0)}, "
                f"Hold {getattr(analyst_recommendations.brokerage, 'hold', 0)}, "
                f"Sell {getattr(analyst_recommendations.brokerage, 'sell', 0)}, "
                f"Strong Sell {getattr(analyst_recommendations.brokerage, 'strong_sell', 0)}\n"
            )
        else:
            recommendations_summary = (
                f"Current Recommendation: {getattr(analyst_recommendations, 'current_recommendation', 'N/A')}\n"
                f"Total Analysts: {getattr(analyst_recommendations, 'total_analysts', 0)}\n"
                f"Brokerage data is unavailable.\n"
            )

        # Technical Analysis
        technical_analysis = stock_data.technical_analysis
        technical_analysis_summary = "Technical Analysis data is unavailable.\n" if not technical_analysis else (
            f"Current Price: {getattr(technical_analysis, 'current_price', 'N/A')}\n"
            f"RSI: {getattr(technical_analysis, 'rsi', 'N/A')}, "
            f"MACD: {getattr(technical_analysis, 'macd', 'N/A')}\n"
            f"Day ADX: {getattr(technical_analysis, 'day_adx', 'N/A')}, "
            f"Day ATR: {getattr(technical_analysis, 'day_atr', 'N/A')}\n"
            f"Bullish MAs: {getattr(technical_analysis, 'total_bullish_moving_averages', 'N/A')}, "
            f"Bearish MAs: {getattr(technical_analysis, 'total_bearish_moving_averages', 'N/A')}\n"
            f"EMA: {', '.join([f'{k}: {v}' for k, v in (technical_analysis.ema or {}).items()])}\n"
            f"Resistance Levels: {', '.join([f'{k}: {v}' for k, v in (technical_analysis.resistance or {}).items()])}\n"
            f"Support Levels: {', '.join([f'{k}: {v}' for k, v in (technical_analysis.support or {}).items()])}\n"
            f"Volume: Daily {technical_analysis.volume.get('daily', 'N/A')}, "
            f"Weekly {technical_analysis.volume.get('weekly', 'N/A')}, "
            f"Monthly {technical_analysis.volume.get('monthly', 'N/A')}\n"
        )

        combined_prompt += (
            f"Stock name '{stock_data.stock_name}' (Code: {stock_data.stock_code}):\n"
            f"Momentum Score: {getattr(stock_data, 'momentum_score', 'N/A')} "
            f"({getattr(stock_data, 'momentum_comment', 'N/A')})\n\n"
            f"Price Analysis:\n{price_analysis_summary}\n"
            f"Analyst Recommendations:\n{recommendations_summary}\n"
            f"Technical Analysis:\n{technical_analysis_summary}\n\n"
        )
        return combined_prompt

if __name__ == "__main__":
    asyncio.run(main())
