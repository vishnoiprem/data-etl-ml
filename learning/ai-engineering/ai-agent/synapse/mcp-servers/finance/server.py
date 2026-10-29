"""
Finance MCP Server — wraps yfinance to expose market data as tools.
No API key required; yfinance pulls directly from Yahoo Finance.

Run standalone:  python mcp-servers/finance/server.py
Agents connect via stdio transport.
"""

import json
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).parent.parent.parent / ".env")

mcp = FastMCP("Finance Server")

# Major market indices
INDICES = {
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "NASDAQ": "^IXIC",
    "Russell 2000": "^RUT",
}


def _safe_pct(current, prev) -> float | None:
    try:
        return round((current - prev) / prev * 100, 2)
    except Exception:
        return None


@mcp.tool()
def get_market_summary() -> str:
    """Fetch a summary of major US market indices (S&P 500, Dow, NASDAQ, Russell 2000).

    Returns:
        JSON string with index name, current price, previous close, and % change.
    """
    try:
        import yfinance as yf

        results = []
        for name, symbol in INDICES.items():
            try:
                ticker = yf.Ticker(symbol)
                fi = ticker.fast_info
                price = fi.last_price
                prev = fi.previous_close
                results.append(
                    {
                        "name": name,
                        "symbol": symbol,
                        "price": round(price, 2) if price else None,
                        "previous_close": round(prev, 2) if prev else None,
                        "change_pct": _safe_pct(price, prev),
                    }
                )
            except Exception as exc:
                results.append({"name": name, "symbol": symbol, "error": str(exc)})

        return json.dumps({"indices": results})

    except ImportError:
        return json.dumps({"error": "yfinance not installed — run: pip install yfinance"})
    except Exception as exc:
        return json.dumps({"error": str(exc), "indices": []})


@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """Fetch current price and key stats for a single stock ticker.

    Args:
        symbol: Ticker symbol, e.g. 'AAPL', 'MSFT', 'TSLA'.

    Returns:
        JSON string with price, market cap, P/E ratio, 52-week range, etc.
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol.upper())
        fi = ticker.fast_info
        info = ticker.info or {}

        price = fi.last_price
        prev = fi.previous_close
        result = {
            "symbol": symbol.upper(),
            "name": info.get("longName", symbol),
            "price": round(price, 2) if price else None,
            "previous_close": round(prev, 2) if prev else None,
            "change_pct": _safe_pct(price, prev),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
        }
        return json.dumps(result)

    except ImportError:
        return json.dumps({"error": "yfinance not installed"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def search_tickers(query: str, max_results: int = 3) -> str:
    """Search for stock tickers related to a topic keyword.

    Args:
        query: Search term, e.g. 'electric vehicles', 'AI chips'.
        max_results: Maximum number of tickers to return.

    Returns:
        JSON string with a list of matching tickers and their current prices.
    """
    TOPIC_MAP = {
        "ai": ["NVDA", "MSFT", "GOOGL", "META", "AMD"],
        "artificial intelligence": ["NVDA", "MSFT", "GOOGL"],
        "electric vehicle": ["TSLA", "RIVN", "NIO", "GM"],
        "ev": ["TSLA", "RIVN", "NIO"],
        "energy": ["XOM", "CVX", "NEE", "BP"],
        "crypto": ["COIN", "MSTR", "MARA"],
        "bitcoin": ["COIN", "MSTR", "MARA"],
        "bank": ["JPM", "BAC", "GS", "MS"],
        "tech": ["AAPL", "MSFT", "GOOGL", "META", "AMZN"],
        "health": ["JNJ", "PFE", "UNH", "MRNA"],
        "pharma": ["PFE", "MRNA", "ABBV", "LLY"],
        "retail": ["AMZN", "WMT", "TGT", "COST"],
        "space": ["SPCE", "RKLB", "BA", "LMT"],
    }

    q_lower = query.lower()
    symbols = []
    for keyword, tickers in TOPIC_MAP.items():
        if keyword in q_lower:
            symbols.extend(tickers)
    symbols = list(dict.fromkeys(symbols))[:max_results]  # deduplicate, limit

    if not symbols:
        return json.dumps({"tickers": [], "note": "No topic-matched tickers found"})

    try:
        import yfinance as yf

        results = []
        for sym in symbols:
            try:
                fi = yf.Ticker(sym).fast_info
                price = fi.last_price
                prev = fi.previous_close
                results.append(
                    {
                        "symbol": sym,
                        "price": round(price, 2) if price else None,
                        "change_pct": _safe_pct(price, prev),
                    }
                )
            except Exception:
                pass
        return json.dumps({"tickers": results})

    except ImportError:
        return json.dumps({"error": "yfinance not installed"})
    except Exception as exc:
        return json.dumps({"error": str(exc), "tickers": []})


if __name__ == "__main__":
    mcp.run()
