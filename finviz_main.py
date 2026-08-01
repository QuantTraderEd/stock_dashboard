import requests
import pandas as pd

from fake_useragent import UserAgent
from bs4 import BeautifulSoup

# 분석할 종목 리스트
tickers = ["NVDA", "AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "TSM", "AVGO",
           "ORCL", "NFLX",  "PLTR", "ADBE", "NOW", "CRM", "APP", "SNOW", "DDOG", "NET",
           "AMD",  "MU", "INTC", "SNDK",
           "ASML", "AMAT", "LRCX", "KLAC",
           "QCOM", "ARM", "MRVL",
           "HOOD", "COIN",
           "GLW", "COHR", "LITE"
           ]

# 추출할 항목들 (Finviz 페이지 내 snapshot 테이블에 표시되는 이름과 동일해야 함)
keys_to_extract = ["Price", "Market Cap", "Forward P/E",
                   "EPS (ttm)", "EPS this Y", "EPS next Y", "EPS next 5Y", "EPS past 3/5Y",
                   "52W High", "52W Low", "RSI (14)",
                   "Recom", "Target Price"]

# 결과를 담을 리스트
data_list = []

# HTTP 요청 시 사용할 헤더 (User-Agent 지정)
ua = UserAgent()
headers = {
    'User-Agent': ua.random,
}

for ticker in tickers:
    url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
    response = requests.get(url, headers=headers)

    # 요청이 실패했는지 확인
    if response.status_code != 200:
        print(f"Failed to retrieve data for {ticker}")
        continue

    soup = BeautifulSoup(response.content, "html.parser")

    # snapshot 테이블 추출
    snapshot_table = soup.find("table", class_="snapshot-table2")
    data_dict = {}

    if snapshot_table:
        cells = snapshot_table.find_all("td")
        if cells:
            for i in range(0, len(cells), 2):
                label = cells[i].get_text().strip()
                value = cells[i + 1].get_text().strip() if i + 1 < len(cells) else ""
                data_dict[label] = value
    else:
        print(f"Snapshot table not found for {ticker}")
        continue

    # 각 종목에 대해 원하는 항목을 딕셔너리로 정리
    row = {"Ticker": ticker}
    for key in keys_to_extract:
        row[key] = data_dict.get(key, "N/A")
    data_list.append(row)

# DataFrame으로 변환 후 출력
df = pd.DataFrame(data_list)

# 'Market Cap' 컬럼 전처리: 'B' (Billion) 단위를 숫자로 변환
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

df['Market Cap'] = df['Market Cap'].apply(convert_market_cap_to_numeric)
df.sort_values(by='Market Cap', inplace=True, ascending=False)

# 'Market Cap' 컬럼을 다시 'B' 단위 문자열로 변환
def format_market_cap_to_billions(market_cap_numeric):
    if pd.isna(market_cap_numeric):
        return None
    return f"{market_cap_numeric / 1_000_000_000:.2f}B"

df['Market Cap'] = df['Market Cap'].apply(format_market_cap_to_billions)


df['PEG (Fwd P/E to EPS 5Y Groth)'] = pd.to_numeric(df['Forward P/E'], errors='coerce') / pd.to_numeric(df['EPS next 5Y'].str[:-1], errors='coerce')
df['Price'] = df['Price'].apply(lambda x: f"{float(x):.2f}")
df['PEG (Fwd P/E to EPS 5Y Groth)'] = df['PEG (Fwd P/E to EPS 5Y Groth)'].apply(lambda x: f"{x:.4f}")
print(df.to_markdown(index=False))
df.to_csv('./data/finviz_valuation_data.csv', index=False, sep="|")
