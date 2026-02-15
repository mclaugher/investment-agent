"""Fundamental analysis tools for agent use (per §6.3).

All tools are @tool decorated, stateless, and return typed dicts.
Primary data source: yfinance. Fallback: FMP API.
"""

from langchain_core.tools import tool

from app.services.data_ingestion import fetch_yfinance_info, fetch_yfinance_financials


def _safe_get(d: dict, *keys, default=None):
    """Safely traverse nested dicts."""
    val = d
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, default)
        else:
            return default
    return val if val is not None else default


@tool
def get_financial_ratios(symbol: str) -> dict:
    """Calculate and return key financial ratios.
    Returns: {pe, forward_pe, pb, ps, ev_ebitda, roe, roa, debt_equity, current_ratio,
              quick_ratio, gross_margin, operating_margin, net_margin, revenue_growth_yoy,
              earnings_growth_yoy, dividend_yield, payout_ratio, beta}"""
    info = fetch_yfinance_info(symbol)

    return {
        "symbol": symbol,
        "pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "pb": info.get("priceToBook"),
        "ps": info.get("priceToSalesTrailing12Months"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "debt_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "quick_ratio": info.get("quickRatio"),
        "gross_margin": info.get("grossMargins"),
        "operating_margin": info.get("operatingMargins"),
        "net_margin": info.get("profitMargins"),
        "revenue_growth_yoy": info.get("revenueGrowth"),
        "earnings_growth_yoy": info.get("earningsGrowth"),
        "dividend_yield": info.get("dividendYield"),
        "payout_ratio": info.get("payoutRatio"),
        "beta": info.get("beta"),
    }


@tool
def run_dcf_analysis(
    symbol: str,
    growth_rate: float | None = None,
    discount_rate: float = 0.10,
    terminal_growth: float = 0.025,
    projection_years: int = 5,
) -> dict:
    """Run a discounted cash flow analysis using historical free cash flow.
    If growth_rate is None, estimate from historical FCF growth.
    Returns: {fair_value_per_share, current_price, upside_pct, assumptions,
              projected_fcf, sensitivity_table}"""
    data = fetch_yfinance_financials(symbol)
    info = data.get("info", {})
    cashflow = data.get("cashflow", {})

    # Extract FCF from cashflow statement
    fcf_values = []
    free_cashflow_row = cashflow.get("Free Cash Flow") or cashflow.get("FreeCashFlow") or {}
    if isinstance(free_cashflow_row, dict):
        for period, val in sorted(free_cashflow_row.items(), reverse=True):
            if val is not None:
                fcf_values.append(float(val))

    if not fcf_values:
        return {
            "symbol": symbol,
            "error": "Insufficient free cash flow data for DCF",
            "current_price": info.get("regularMarketPrice") or info.get("currentPrice", 0),
        }

    latest_fcf = fcf_values[0]

    # Estimate growth rate from historical FCF if not provided
    if growth_rate is None:
        if len(fcf_values) >= 2 and fcf_values[-1] > 0:
            cagr = (fcf_values[0] / fcf_values[-1]) ** (1 / len(fcf_values)) - 1
            growth_rate = max(min(cagr, 0.30), -0.10)  # Clamp to [-10%, 30%]
        else:
            growth_rate = 0.05  # Default 5%

    shares_outstanding = info.get("sharesOutstanding", 1)
    current_price = info.get("regularMarketPrice") or info.get("currentPrice", 0)

    # Three scenarios per §6.3: bull (growth+2%), base, bear (growth-2%)
    scenarios = {
        "bull": growth_rate + 0.02,
        "base": growth_rate,
        "bear": growth_rate - 0.02,
    }

    results = {}
    for scenario_name, rate in scenarios.items():
        projected_fcf = []
        fcf = latest_fcf
        pv_total = 0

        for year in range(1, projection_years + 1):
            fcf = fcf * (1 + rate)
            pv = fcf / ((1 + discount_rate) ** year)
            pv_total += pv
            projected_fcf.append({"year": year, "fcf": round(fcf, 2), "pv": round(pv, 2)})

        # Terminal value
        terminal_fcf = fcf * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)
        pv_total += pv_terminal

        fair_value = pv_total / shares_outstanding if shares_outstanding > 0 else 0
        upside = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0

        results[scenario_name] = {
            "fair_value_per_share": round(fair_value, 2),
            "upside_pct": round(upside, 2),
            "growth_rate": round(rate, 4),
            "projected_fcf": projected_fcf,
        }

    base = results["base"]
    return {
        "symbol": symbol,
        "fair_value_per_share": base["fair_value_per_share"],
        "current_price": current_price,
        "upside_pct": base["upside_pct"],
        "assumptions": {
            "base_growth_rate": round(growth_rate, 4),
            "discount_rate": discount_rate,
            "terminal_growth": terminal_growth,
            "projection_years": projection_years,
            "latest_fcf": round(latest_fcf, 2),
            "shares_outstanding": shares_outstanding,
        },
        "projected_fcf": base["projected_fcf"],
        "sensitivity_table": {
            "bull": {"fair_value": results["bull"]["fair_value_per_share"], "upside_pct": results["bull"]["upside_pct"]},
            "base": {"fair_value": base["fair_value_per_share"], "upside_pct": base["upside_pct"]},
            "bear": {"fair_value": results["bear"]["fair_value_per_share"], "upside_pct": results["bear"]["upside_pct"]},
        },
    }


@tool
def get_comparable_analysis(symbol: str) -> dict:
    """Compare a stock against its sector peers on key valuation multiples.
    Automatically identifies 5-8 peers in the same GICS sub-industry.
    Returns: {target, peers, target_vs_median}"""
    info = fetch_yfinance_info(symbol)
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")

    target_metrics = {
        "symbol": symbol,
        "sector": sector,
        "industry": industry,
        "pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "pb": info.get("priceToBook"),
        "ps": info.get("priceToSalesTrailing12Months"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "market_cap": info.get("marketCap"),
        "dividend_yield": info.get("dividendYield"),
    }

    # Identify peers from sector universe
    from scripts.seed_universe import STOCK_UNIVERSE

    # Find which sector group contains this symbol
    peers_list = []
    for sec_name, symbols in STOCK_UNIVERSE.items():
        if symbol in symbols:
            peers_list = [s for s in symbols if s != symbol]
            break

    # If not found in universe, return target only
    if not peers_list:
        return {"target": target_metrics, "peers": [], "target_vs_median": {}}

    # Fetch peer data (limit to 8)
    peers = []
    for peer_symbol in peers_list[:8]:
        try:
            peer_info = fetch_yfinance_info(peer_symbol)
            peers.append({
                "symbol": peer_symbol,
                "pe": peer_info.get("trailingPE"),
                "forward_pe": peer_info.get("forwardPE"),
                "pb": peer_info.get("priceToBook"),
                "ps": peer_info.get("priceToSalesTrailing12Months"),
                "ev_ebitda": peer_info.get("enterpriseToEbitda"),
                "market_cap": peer_info.get("marketCap"),
            })
        except Exception:
            continue

    # Calculate median multiples and premium/discount
    target_vs_median = {}
    for metric in ["pe", "forward_pe", "pb", "ps", "ev_ebitda"]:
        peer_vals = [p[metric] for p in peers if p.get(metric) is not None]
        target_val = target_metrics.get(metric)
        if peer_vals and target_val is not None:
            peer_vals_sorted = sorted(peer_vals)
            median = peer_vals_sorted[len(peer_vals_sorted) // 2]
            if median > 0:
                premium_pct = round(((target_val - median) / median) * 100, 2)
                target_vs_median[f"{metric}_premium_pct"] = premium_pct
                target_vs_median[f"{metric}_median"] = round(median, 2)

    return {
        "target": target_metrics,
        "peers": peers,
        "target_vs_median": target_vs_median,
    }
