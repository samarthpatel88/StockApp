import json
from dataclasses import dataclass, field
from typing import List, Dict, Union,Optional


@dataclass
class Metric:
    value: Optional[float]  # MetricValue
    conclusion: Optional[str] = None  # MetricText, e.g., "Below industry Median"


@dataclass
class KeyMetrics:
    market_capitalization: Metric
    pe: Metric
    peg: Metric
    price_to_book: Metric
    institute_holding: Metric  # No conclusion available
    revenue_growth_yoy: Metric
    operating_revenue_growth: Metric
    net_profit_growth_yoy: Metric
    net_profit_ttm_growth: Metric
    operating_profit_margin_qtr: Metric
    operating_profit_margin_ttm: Metric
    piotroski_score: Metric
    rel_perf_vs_nifty50_qtr: Metric
    rel_perf_vs_sector_qtr: Metric
    roe_annual: Metric



@dataclass
class SwotAnalysis:
    strength: int
    weakness: int
    opportunities: int
    threat: int


@dataclass
class PriceRange:
    high: float
    low: float


@dataclass
class StockPriceAnalysis:
    day_price_range: PriceRange
    week_price_range: PriceRange
    month_price_range: PriceRange
    year_52_price_range: PriceRange


@dataclass
class Brokerage:
    strong_sell: int
    sell: int
    hold: int
    strong_buy: int
    buy: int


@dataclass
class AnalystRecommendations:
    current_recommendation: str
    total_analysts: int
    brokerage: Brokerage


@dataclass
class StockInsight:
    key: str
    sentiment: str
    description: str

@dataclass
class StockAnalysis:
    insights: List[StockInsight]


@dataclass
class TechnicalAnalysis:
    current_price: float = None
    total_bullish_moving_averages: int = None,
    total_bearish_moving_averages: int = None,
    ema: Dict[str, float] = None,
    resistance: Dict[str, float] = None,
    support: Dict[str, float] = None,
    rsi: float = None,
    macd: float = None,
    day_adx: float = None,
    day_atr: float = None,
    volume: Dict[str, float] = None,


class Shareholding:
    def __init__(self, fii=0.0, dii=0.0, retail=0.0):
        self.fii = fii
        self.dii = dii
        self.retail = retail

    def __repr__(self):
        return (f"Shareholding(FII={self.fii}%, "
                f"DII={self.dii}%, "
                f"Retail={self.retail}%)")


@dataclass
class StockData:
    stock_name: str
    stock_code: str
    momentum_score: int
    momentum_comment: str
    key_metrics: KeyMetrics
    swot_analysis: SwotAnalysis
    stock_price_analysis: StockPriceAnalysis
    analyst_recommendations: AnalystRecommendations
    stock_analysis: StockAnalysis
    technical_analysis: TechnicalAnalysis
    holdings: Shareholding

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
