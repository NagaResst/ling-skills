import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import requests


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "investment-news-analysis"
    / "scripts"
    / "fetch_market_momentum.py"
)
SPEC = importlib.util.spec_from_file_location("fetch_market_momentum", SCRIPT_PATH)
market = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(market)


class MarketMomentumDataContractTests(unittest.TestCase):
    def test_northbound_daily_uses_006_aggregate(self):
        rows = [
            {"TRADE_DATE": "2026-08-20 00:00:00", "MUTUAL_TYPE": "005", "DEAL_AMT": 286248.93},
            {
                "TRADE_DATE": "2026-08-20 00:00:00",
                "MUTUAL_TYPE": "006",
                "DEAL_AMT": 119184.75,
                "NET_DEAL_AMT": -10412.07,
                "BUY_AMT": 54386.34,
                "SELL_AMT": 64798.41,
            },
        ]
        with patch.object(market, "fetch_eastmoney_mutual_deal_history", return_value=rows):
            result = market.get_northbound_daily_raw("2026-08-21")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["mutual_type"], "006")
        self.assertEqual(result["net_deal_amt_yi_if_raw_unit_is_million"], -104.12)

    def test_turnover_report_requires_date_in_body(self):
        class PrimaryResponse:
            def raise_for_status(self):
                raise requests.ConnectionError("800004 unavailable")

        class ReportResponse:
            text = "2026-08-19 沪深京三市今日成交总额25300亿元。"

            def raise_for_status(self):
                return None

        def request(url, **_kwargs):
            return ReportResponse() if "market-close" in url else PrimaryResponse()

        with patch.object(market.requests, "get", side_effect=request):
            result = market.get_market_turnover_summary(
                "2026-08-21",
                fallback_report_url="https://example.test/market-close/2026-08-20",
            )

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("目标日期", result["fallback_report_failure"])

    def test_turnover_report_accepts_verified_same_day_body(self):
        class PrimaryResponse:
            def raise_for_status(self):
                raise requests.ConnectionError("800004 unavailable")

        class ReportResponse:
            text = "2026-08-20 沪深京三市今日成交总额20940亿元，较前一日缩量约4362亿元。"

            def raise_for_status(self):
                return None

        def request(url, **_kwargs):
            return ReportResponse() if "market-close" in url else PrimaryResponse()

        with patch.object(market.requests, "get", side_effect=request):
            result = market.get_market_turnover_summary(
                "2026-08-21",
                fallback_report_url="https://example.test/market-close/2026-08-20",
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["date"], "2026-08-20")
        self.assertEqual(result["total_turnover_yi"], 20940.0)

    def test_required_market_data_blocks_incomplete_payload(self):
        with self.assertRaises(market.RequiredQuantitativeDataUnavailable):
            market.require_daily_market_data(
                {
                    "northbound_daily_raw": {"status": "success"},
                    "market_turnover_summary": {"status": "unavailable", "message": "missing"},
                }
            )


if __name__ == "__main__":
    unittest.main()