import requests
import pandas as pd
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

# 분석할 종목 리스트
TICKERS = [
    "NVDA", "AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "TSM", "AVGO",
    "ORCL", "NFLX", "PLTR", "ADBE", "NOW", "CRM", "APP", "SNOW", "DDOG", "NET",
    "AMD", "MU", "INTC", "SNDK",
    "ASML", "AMAT", "LRCX", "KLAC",
    "QCOM", "ARM", "MRVL",
    "HOOD", "COIN",
    "GLW", "COHR", "LITE",
]

# 추출할 항목들 (Finviz 페이지 내 snapshot 테이블에 표시되는 이름과 동일해야 함)
KEYS_TO_EXTRACT = [
    "Price", "Market Cap", "Forward P/E",
    "EPS (ttm)", "EPS this Y", "EPS next Y", "EPS next 5Y", "EPS past 3/5Y",
    "52W High", "52W Low", "RSI (14)",
    "Recom", "Target Price",
]


def fetch_and_parse_stock_data(ticker, headers):
    """
    Fetches and parses stock data for a given ticker from Finviz.
    """
    url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to retrieve data for {ticker}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    data_dict = {}

    snapshot_tables = soup.find_all("table", class_="snapshot-table2")
    if snapshot_tables:
        for table in snapshot_tables:
            label_cells = table.find_all("div", class_="snapshot-td-label")
            value_cells = table.find_all("div", class_="snapshot-td-content")
            for label_div, value_div in zip(label_cells, value_cells):
                label = label_div.get_text().strip()
                value = value_div.get_text().strip()
                data_dict[label] = value
        if not data_dict:
            print(f"No data parsed for {ticker}")
            return None
    else:
        print(f"Snapshot table not found for {ticker}")
        return None

    return data_dict


def convert_market_cap_to_numeric(market_cap_str):
    if pd.isna(market_cap_str) or not isinstance(market_cap_str, str):
        return None
    market_cap_str = market_cap_str.replace(',', '').strip()
    if market_cap_str.endswith('B'):
        return float(market_cap_str[:-1]) * 1_000_000_000
    elif market_cap_str.endswith('M'):
        return float(market_cap_str[:-1]) * 1_000_000
    try:
        return float(market_cap_str)
    except ValueError:
        return None


def format_market_cap_to_billions(market_cap_numeric):
    if pd.isna(market_cap_numeric):
        return None
    return f"{market_cap_numeric / 1_000_000_000:.2f}B"


def main():
    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    data_list = []
    for ticker in TICKERS:
        data_dict = fetch_and_parse_stock_data(ticker, headers)
        if data_dict:
            row = {"Ticker": ticker}
            for key in KEYS_TO_EXTRACT:
                row[key] = data_dict.get(key, "N/A")
            data_list.append(row)

    df = pd.DataFrame(data_list)

    df['Market Cap'] = df['Market Cap'].apply(convert_market_cap_to_numeric)
    df.sort_values(by='Market Cap', inplace=True, ascending=False)
    df['Market Cap'] = df['Market Cap'].apply(format_market_cap_to_billions)

    df['PEG (Fwd P/E to EPS 5Y Groth)'] = (
        pd.to_numeric(df['Forward P/E'], errors='coerce')
        / pd.to_numeric(df['EPS next 5Y'].str[:-1], errors='coerce')
    )
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce').apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )
    df['PEG (Fwd P/E to EPS 5Y Groth)'] = df['PEG (Fwd P/E to EPS 5Y Groth)'].apply(
        lambda x: f"{x:.4f}" if pd.notna(x) else "N/A"
    )

    print(df.to_markdown(index=False))
    df.to_csv('./data/finviz_valuation_data.csv', index=False, sep="|")


if __name__ == "__main__":
    main()
