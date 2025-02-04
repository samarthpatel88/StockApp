import asyncio
import json
from dataclasses import asdict
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
    return getMomentomStock(top_stocks)

async def getMomentomStock(top_stocks):
    # Load stock URLs from a JSON file
    stock_urls = load_stock_urls('stocklist.json')

    if isinstance(top_stocks[0], tuple):  # Check if the first element is a tuple
        urls_for_stocks = {code: stock_urls.get(code, "URL not found") for code, _ in top_stocks}
    elif isinstance(top_stocks[0], str): # Check if the first element is a string
        urls_for_stocks = {code: stock_urls.get(code, "URL not found") for code in top_stocks}
    else:
        print("Unsupported top_stocks format")
        return  # Or raise an exception
    # Filter out stocks with "URL not found"
    valid_urls = [url for url in urls_for_stocks.values() if url != "URL not found"]

    print('valid_urls', valid_urls)

    # Use asyncio.gather to fetch data from all valid URLs concurrently
    tasks = [fetch_stock_data(url) for url in valid_urls]
    stock_data_list: List[StockData] = await asyncio.gather(*tasks)
    print('stock_data_list', stock_data_list)
    # Generate and return the combined prompt text
    prompt_text = create_combined_prompt_text(stock_data_list)
    # API KEY - AIzaSyCTDCN5PyIgLzJE8cqW-7zuekZH1b9dwT8

    os.environ["API_KEY"] = 'AIzaSyCTDCN5PyIgLzJE8cqW-7zuekZH1b9dwT8'
    genai.configure(api_key=os.environ["API_KEY"])

    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    response = model.generate_content(prompt_text)
    return response.text

def load_stock_urls(file_path: str) -> dict:
    """Load stock URLs from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

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


if __name__ == "__main__":
    asyncio.run(main())
