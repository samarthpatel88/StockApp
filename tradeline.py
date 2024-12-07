import asyncio
from typing import Dict

from playwright.async_api import async_playwright
from StockDetails import Metric, KeyMetrics, StockData, PriceRange, StockPriceAnalysis, Brokerage, StockInsight, \
    TechnicalAnalysis, AnalystRecommendations, Shareholding


async def fetch_stock_data():
    url = "https://trendlyne.com/equity/533/HDFCBANK/hdfc-bank-ltd/"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set headless=False to see the browser action
        page = await browser.new_page()
        await page.goto(url)

        # Scroll down the page to load dynamic content
        await scroll_page(page)

        stock_name, nse_stock_code = await fetch_stock_name_and_code(page)

        metrics_data = await fetch_key_metrics(page)

        key_metrics = create_key_metrics(metrics_data)

        swot_analysis = await fetch_swot_data(page)

        momentum_score, momentum_comment = await fetch_momentum_data(page)

        price_ranges = await fetch_price_ranges(page)

        stock_price_analysis = create_stock_price_analysis(price_ranges)

        insights_list = await fetch_stock_analysis(page)

        analysis = await fetch_technical_analysis(page)

        analyst_recommendations = await fetch_brokerage_recommendations(page)

        shareholding = await fetch_shareholding_data(page)

        stockdata = StockData(stock_name=stock_name, stock_code=nse_stock_code, momentum_score=momentum_score,
                              momentum_comment=momentum_comment,
                              key_metrics=key_metrics, swot_analysis=swot_analysis,
                              stock_price_analysis=stock_price_analysis, stock_analysis=insights_list,
                              technical_analysis=analysis,
                              analyst_recommendations=analyst_recommendations, holdings=shareholding)
        print(stockdata)
        # Close the browser
        await browser.close()

async def scroll_page(page):
    for _ in range(7):  # Adjust the range to scroll more times if needed
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await page.wait_for_timeout(1000)  # Wait for 1 second to allow content to load


async def fetch_technical_analysis(page):
    """
    Fetch technical analysis data from the given page.
    :param page: Playwright page instance
    :return: TechnicalAnalysis object with the parsed data
    """
    analysis = TechnicalAnalysis()

    # Fetch current price
    analysis.current_price = await page.locator(
        '#technical-tables span.tech-lg-head.tech-current-price').inner_text()

    # Fetch bullish and bearish moving averages
    analysis.total_bullish_moving_averages = await page.locator(
        '#technical-tables .bullish-span').inner_text()
    analysis.total_bearish_moving_averages = await page.locator(
        '#technical-tables .bearish-span').inner_text()

    # Fetch EMA values
    ema_values = {}
    ema_sections = await page.locator(
        '#technical-tables .tech-ema-section .two-column-container').element_handles()

    for section in ema_sections:
        day_label_element = await section.query_selector('.technical-param')
        day_label = (await day_label_element.inner_text()).strip()

        value_element = await section.query_selector('.value-span')
        value_text = (await value_element.inner_text()).strip()

        ema_values[day_label] = float(value_text)
    analysis.ema = ema_values

    # Fetch resistance values
    resistance_sections = await page.locator(
        '#technical-tables .tech-rs-section .col-xs-6.p-l-0 .two-column-container').element_handles()
    resistances = {}
    for section in resistance_sections:
        label = (await (await section.query_selector('.technical-param')).inner_text()).strip()
        value = float((await (await section.query_selector('.value-span')).inner_text()).strip())
        resistances[label] = value
    analysis.resistance = resistances

    # Fetch support values
    support_sections = await page.locator(
        '#technical-tables .tech-rs-section .col-xs-6.p-r-0 .two-column-container').element_handles()
    supports = {}
    for section in support_sections:
        label = (await (await section.query_selector('.technical-param')).inner_text()).strip()
        value = float((await (await section.query_selector('.value-span')).inner_text()).strip())
        supports[label] = value
    analysis.support = supports

    # Fetch RSI, MACD, ADX, ATR, and volume data
    tech_column_sm = await page.query_selector('#technical-tables .tech-column-sm')
    col_xs_12_divs = await tech_column_sm.query_selector_all('> .col-xs-12')

    if len(col_xs_12_divs) > 1:
        second_div = col_xs_12_divs[1]
        col_xs_6_divs = await second_div.query_selector_all('> .col-xs-6')
        keys = await second_div.query_selector_all('.technical-param')
        values = await second_div.query_selector_all('.value-span')

        analysis_data = {}
        for key, value in zip(keys, values):
            key_text = await key.inner_text()
            value_text = float((await value.inner_text()).strip())

            if 'RSI' in key_text:
                analysis_data['rsi'] = value_text
            elif 'MACD' in key_text:
                analysis_data['macd'] = value_text
            elif 'ADX' in key_text:
                analysis_data['day_adx'] = value_text
            elif 'ATR' in key_text:
                analysis_data['day_atr'] = value_text
            elif 'Volume' in key_text:
                analysis_data.setdefault('volume', {})[key_text] = value_text

        analysis.rsi = analysis_data.get('rsi')
        analysis.macd = analysis_data.get('macd')
        analysis.day_adx = analysis_data.get('day_adx')
        analysis.day_atr = analysis_data.get('day_atr')

    # Fetch additional volume data
    volume_data = await fetch_delivery_volumes(page)
    analysis.volume = volume_data

    return analysis


async def fetch_brokerage_recommendations(page):
    """
    Fetch brokerage recommendations from the given page.

    Args:
        page: Playwright page object.

    Returns:
        AnalystRecommendations object with the recommendation data.
    """
    # Initialize the default analyst recommendations
    analyst_recommendations = AnalystRecommendations(
        current_recommendation=None,
        total_analysts=0,
        brokerage=[]
    )

    # Check if the recommendation-trend-grid is present
    is_recommendation_present = await page.is_visible(".recommendation-trend-grid", timeout=5000)
    print('is_recommendation_present:', is_recommendation_present)

    if is_recommendation_present:
        await page.wait_for_selector(".recommendation-trend-grid")

        # Select all child divs with class 'consensus-card card' inside the parent div
        consensus_cards = page.locator(".recommendation-trend-grid > div.consensus-card.card")
        count = await consensus_cards.count()

        # Ensure there are at least two consensus cards
        if count >= 2:
            second_card = consensus_cards.nth(1) if count == 2 else consensus_cards.nth(2)

            # Wait for the highcharts-container within the second card
            highcharts_container = second_card.locator(".highcharts-container")
            await highcharts_container.wait_for()

            # Locate the recommendation data (e.g., "1 Buy" or "1 Strong Buy")
            recommendation_texts = highcharts_container.locator(
                "g.highcharts-axis-labels.highcharts-xaxis-labels > text"
            )

            # Get the total count of recommendations
            recommendation_count = await recommendation_texts.count()

            # Get the current recommendation (e.g., "BUY")
            current_recommendation_element = second_card.locator(".card-body .title1")
            current_recommendation = await current_recommendation_element.text_content()
            current_recommendation = current_recommendation.strip().upper()

            # Initialize counts for each recommendation type
            recommendation_counts = {
                "Strong Sell": 0,
                "Sell": 0,
                "Hold": 0,
                "Buy": 0,
                "Strong Buy": 0,
            }

            # Extract and set recommendations
            for i in range(recommendation_count):
                recommendation = recommendation_texts.nth(i)

                # Extract the first <tspan> (count) and the second <tspan> (type)
                count_tspan = await recommendation.locator("tspan:first-of-type").text_content()
                type_tspan = await recommendation.locator("tspan:nth-of-type(2)").text_content()

                # Convert count to an integer
                count = int(count_tspan.strip())

                # Update the correct recommendation count
                if type_tspan in recommendation_counts:
                    recommendation_counts[type_tspan] += count

            # Create the Brokerage object using the recommendation counts
            brokerage_data = Brokerage(
                strong_sell=recommendation_counts["Strong Sell"],
                sell=recommendation_counts["Sell"],
                hold=recommendation_counts["Hold"],
                buy=recommendation_counts["Buy"],
                strong_buy=recommendation_counts["Strong Buy"]
            )

            # Get the total analysts (sum of all recommendations from the Brokerage)
            total_analysts = sum(recommendation_counts.values())

            # Create the AnalystRecommendations object
            analyst_recommendations = AnalystRecommendations(
                current_recommendation=current_recommendation,
                total_analysts=total_analysts,
                brokerage=brokerage_data,
            )

    return analyst_recommendations

async def fetch_momentum_data(page):
    status_element = await page.query_selector('.left-insight .insight')
    momentum_comment = await status_element.inner_text()
    score_element = await page.query_selector('.right-number .real-score')
    momentum_score = await score_element.inner_text()
    return momentum_score, momentum_comment


async def fetch_price_ranges(page):
    rows = await page.query_selector_all('#performanceAnalysisParent tr.stcard')
    price_ranges = {}
    for row in rows:
        title = await row.eval_on_selector('h3 span', 'element => element.textContent')
        low_price = await row.eval_on_selector(
            '.tl__progress_text--2pOON.tl__progress_se--CbMSc span:first-child',
            'element => element.textContent',
        )
        high_price = await row.eval_on_selector(
            '.tl__progress_text--2pOON.tl__progress_se--CbMSc span:last-child',
            'element => element.textContent',
        )

        low_price_float = float(low_price.replace(',', ''))
        high_price_float = float(high_price.replace(',', ''))

        if "Day Price Range" in title:
            price_ranges['day_price_range'] = PriceRange(high=high_price_float, low=low_price_float)
        elif "Week Price Range" in title:
            price_ranges['week_price_range'] = PriceRange(high=high_price_float, low=low_price_float)
        elif "Month Price Range" in title:
            price_ranges['month_price_range'] = PriceRange(high=high_price_float, low=low_price_float)
        elif "52 Week Price Range" in title:
            price_ranges['year_52_price_range'] = PriceRange(high=high_price_float, low=low_price_float)
    return price_ranges


def create_stock_price_analysis(price_ranges):
    return StockPriceAnalysis(
        day_price_range=price_ranges.get('day_price_range'),
        week_price_range=price_ranges.get('week_price_range'),
        month_price_range=price_ranges.get('month_price_range'),
        year_52_price_range=price_ranges.get('year_52_price_range'),
    )


async def fetch_stock_analysis(page):
    section_element = await page.query_selector('section#stockAnalysisSection')
    insights_list = []

    if section_element:
        article_element = await section_element.query_selector('article')
        if article_element:
            ul_element = await article_element.query_selector('ul')
            if ul_element:
                li_elements = await ul_element.query_selector_all('li')
                for li in li_elements:
                    sentiment_element = await li.query_selector('span')
                    sentiment_text = await sentiment_element.text_content() if sentiment_element else 'N/A'

                    description_element = await li.query_selector('h3')
                    description_text = await description_element.text_content() if description_element else 'N/A'

                    strong_element = await li.query_selector('h3 strong')
                    key = await strong_element.text_content() if strong_element else 'N/A'

                    insight = StockInsight(key=key, sentiment=sentiment_text, description=description_text)
                    insights_list.append(insight)
    return insights_list


async def fetch_shareholding_data(page):
    shareholding_wrappers = await page.query_selector_all('.bootstrap-scope.shareholding-wrapper')
    shareholding = Shareholding()

    for wrapper in shareholding_wrappers:
        tables = await wrapper.query_selector_all('table.tl-dataTable')
        for table in tables:
            rows = await table.query_selector_all('tbody#shTableLimitedRows tr')
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) > 3:
                    category = await cells[1].inner_text()
                    percentage_text = await cells[3].inner_text()
                    percentage = float(percentage_text.replace('%', '').strip())

                    if category == 'FII':
                        shareholding.fii += percentage
                    elif category == 'DII':
                        shareholding.dii += percentage
                    elif category == 'PUBLIC':
                        shareholding.retail += percentage
    return shareholding


async def fetch_stock_name_and_code(page):
    stock_name = await page.inner_text("span.stock-info-heading.stock-info-ho.fw700")
    stock_info = await page.inner_text("span.m-l-1.fs075rem.gr.stock-info-details")

    nse_stock_code = ""
    for line in stock_info.splitlines():
        if "NSE:" in line:
            nse_stock_code = line.split("NSE:")[1].strip().split(" | ")[0].strip()

    return stock_name, nse_stock_code


async def fetch_key_metrics(page):
    div_selector = "div.desktop-view-metric-cards"
    metrics_data = {}
    rows = await page.query_selector_all(f"{div_selector} table tbody tr")

    for row in rows:
        first_td = await row.query_selector("td:first-child")
        h3_text, span_text_content = await extract_first_td_data(first_td)

        second_td_value = await extract_second_td_data(row)

        if h3_text:
            metrics_data[h3_text] = {
                "value": second_td_value,
                "text": span_text_content  # Save the qualitative text
            }

    return metrics_data


async def extract_first_td_data(first_td):
    if not first_td:
        return None, None

    h3_element = await first_td.query_selector("h3.stcard-title.shrink-text.text-ellipsis")
    if h3_element:
        h3_text = await h3_element.inner_text()
        span_text = await first_td.query_selector("div.stcard-footer span")
        span_text_content = await span_text.inner_text() if span_text else None
        return h3_text, span_text_content
    return None, None


async def extract_second_td_data(row):
    second_td = await row.query_selector("td:nth-child(2)")
    if second_td:
        span_element = await second_td.query_selector("span.color202020")
        if span_element:
            return await span_element.inner_text()
    return None

async def fetch_delivery_volumes(page) -> Dict[str, float]:
    # Wait for the table to load (adjust selector if needed)
    await page.wait_for_selector("#deliveryTable")

    # Extract daily, weekly, and monthly delivery volumes
    daily_volume = await page.locator("#deliveryTable tbody tr td:nth-child(1)").inner_text()
    weekly_volume = await page.locator("#deliveryTable tbody tr td:nth-child(2)").inner_text()
    monthly_volume = await page.locator("#deliveryTable tbody tr td:nth-child(3)").inner_text()

    volume: Dict[str, float] = {
        "daily": float(daily_volume.strip('%')),
        "weekly": float(weekly_volume.strip('%')),
        "monthly": float(monthly_volume.strip('%'))
    }
    return volume


async def fetch_swot_data(page):
    swot_data = {}

    # Locate the div containing the SWOT analysis
    swot_selector = "div.swot-main-holder"
    strength = await page.query_selector("a.strength-box")
    if strength:
        strength_value = await strength.query_selector("p.swot-box-value")
        swot_data["strength"] = int(await strength_value.inner_text())
    weakness = await page.query_selector("a.weakness-box")
    if weakness:
        weakness_value = await weakness.query_selector("p.swot-box-value")
        swot_data["weakness"] = int(await weakness_value.inner_text())

    opportunities = await page.query_selector("a.opportunities-box")
    if opportunities:
        opportunity_value = await opportunities.query_selector("p.swot-box-value")
        swot_data["opportunity"] = int(await opportunity_value.inner_text())

    threats = await page.query_selector("a.threats-box")
    if threats:
        threat_value = await threats.query_selector("p.swot-box-value")
        swot_data["threat"] = int(await threat_value.inner_text())

    return swot_data


def create_key_metrics(metrics_data):
    return KeyMetrics(
        market_capitalization=Metric(value=metrics_data.get("Market Capitalization", {}).get("value"),
                                     conclusion=metrics_data.get("Market Capitalization", {}).get("text")),
        pe=Metric(value=metrics_data.get("PE TTM", {}).get("value"),
                  conclusion=metrics_data.get("PE TTM", {}).get("text")),
        peg=Metric(value=metrics_data.get("PEG TTM", {}).get("value"),
                   conclusion=metrics_data.get("PEG TTM", {}).get("text")),
        price_to_book=Metric(value=metrics_data.get("Price to Book", {}).get("value"),
                             conclusion=metrics_data.get("Price to Book", {}).get("text")),
        institute_holding=Metric(value=metrics_data.get("Institutional holding current Qtr %", {}).get("value"),
                                 conclusion=metrics_data.get("Institutional holding current Qtr %", {}).get("text")),
        revenue_growth_yoy=Metric(value=metrics_data.get("Revenue Growth Qtr YoY %", {}).get("value"),
                                  conclusion=metrics_data.get("Revenue Growth Qtr YoY %", {}).get("text")),
        operating_revenue_growth=Metric(value=metrics_data.get("Operating Revenue growth TTM %", {}).get("value"),
                                        conclusion=metrics_data.get("Operating Revenue growth TTM %", {}).get("text")),
        net_profit_growth_yoy=Metric(value=metrics_data.get("Net Profit Qtr Growth YoY %", {}).get("value"),
                                     conclusion=metrics_data.get("Net Profit Qtr Growth YoY %", {}).get("text")),
        net_profit_ttm_growth=Metric(value=metrics_data.get("Net Profit TTM Growth %", {}).get("value"),
                                     conclusion=metrics_data.get("Net Profit TTM Growth %", {}).get("text")),
        operating_profit_margin_qtr=Metric(value=metrics_data.get("Operating Profit Margin Qtr %", {}).get("value"),
                                           conclusion=metrics_data.get("Operating Profit Margin Qtr %", {}).get(
                                               "text")),
        operating_profit_margin_ttm=Metric(value=metrics_data.get("Operating Profit Margin TTM %", {}).get("value"),
                                           conclusion=metrics_data.get("Operating Profit Margin TTM %", {}).get(
                                               "text")),
        piotroski_score=Metric(value=metrics_data.get("Piotroski Score", {}).get("value"),
                               conclusion=metrics_data.get("Piotroski Score", {}).get("text")),
        rel_perf_vs_nifty50_qtr=Metric(value=metrics_data.get("Rel Perf vs Nifty50 quarter%", {}).get("value"),
                                       conclusion=metrics_data.get("Rel Perf vs Nifty50 quarter%", {}).get("text")),
        rel_perf_vs_sector_qtr=Metric(value=metrics_data.get("Rel Perf vs Sector quarter%", {}).get("value"),
                                      conclusion=metrics_data.get("Rel Perf vs Sector quarter%", {}).get("text")),
        roe_annual=Metric(value=metrics_data.get("ROE Annual %", {}).get("value"),
                          conclusion=metrics_data.get("ROE Annual %", {}).get("text"))
    )


# Run the asynchronous function
asyncio.run(fetch_stock_data())