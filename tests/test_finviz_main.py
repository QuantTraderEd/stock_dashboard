import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from finviz_main import fetch_and_parse_stock_data

@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get"""
    with patch('requests.get') as mock_get:
        yield mock_get

def test_fetch_and_parse_stock_data_success(mock_requests_get):
    """
    Test fetch_and_parse_stock_data for a successful response.
    Finviz now uses multiple snapshot-table2 tables with div-based label/value structure.
    """
    html_content = """
    <table class="snapshot-table2">
        <tr>
            <td><div class="snapshot-td-label">Market Cap</div></td>
            <td><div class="snapshot-td-content">4537.07B</div></td>
            <td><div class="snapshot-td-label">Enterprise Value</div></td>
            <td><div class="snapshot-td-content">4559.02B</div></td>
        </tr>
    </table>
    <table class="snapshot-table2">
        <tr>
            <td><div class="snapshot-td-label">Forward P/E</div></td>
            <td><div class="snapshot-td-content">32.21</div></td>
            <td><div class="snapshot-td-label">P/E</div></td>
            <td><div class="snapshot-td-content">35.41</div></td>
        </tr>
    </table>
    <table class="snapshot-table2">
        <tr>
            <td><div class="snapshot-td-label">Price</div></td>
            <td><div class="snapshot-td-content">308.91</div></td>
            <td><div class="snapshot-td-label">RSI (14)</div></td>
            <td><div class="snapshot-td-content">43.24</div></td>
        </tr>
    </table>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = html_content.encode('utf-8')
    mock_requests_get.return_value = mock_response

    ticker = "AAPL"
    headers = {"User-Agent": "test-agent"}
    data = fetch_and_parse_stock_data(ticker, headers)

    assert data is not None
    assert data["Market Cap"] == "4537.07B"
    assert data["Forward P/E"] == "32.21"
    assert data["Price"] == "308.91"
    assert data["RSI (14)"] == "43.24"
    mock_requests_get.assert_called_once_with(
        f"https://finviz.com/quote.ashx?t={ticker}&p=d", headers=headers
    )

def test_fetch_and_parse_stock_data_multiple_tables(mock_requests_get):
    """
    Test that data from all snapshot-table2 tables is aggregated.
    """
    html_content = """
    <table class="snapshot-table2">
        <tr>
            <td><div class="snapshot-td-label">Market Cap</div></td>
            <td><div class="snapshot-td-content">300B</div></td>
        </tr>
    </table>
    <table class="snapshot-table2">
        <tr>
            <td><div class="snapshot-td-label">EPS (ttm)</div></td>
            <td><div class="snapshot-td-content">8.72</div></td>
        </tr>
    </table>
    <table class="snapshot-table2">
        <tr>
            <td><div class="snapshot-td-label">Price</div></td>
            <td><div class="snapshot-td-content">150.00</div></td>
            <td><div class="snapshot-td-label">Recom</div></td>
            <td><div class="snapshot-td-content">1.98</div></td>
        </tr>
    </table>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = html_content.encode('utf-8')
    mock_requests_get.return_value = mock_response

    data = fetch_and_parse_stock_data("NVDA", {"User-Agent": "test-agent"})

    assert data is not None
    assert data["Market Cap"] == "300B"
    assert data["EPS (ttm)"] == "8.72"
    assert data["Price"] == "150.00"
    assert data["Recom"] == "1.98"

def test_fetch_and_parse_stock_data_http_error(mock_requests_get):
    """
    Test fetch_and_parse_stock_data for an HTTP error response.
    """
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response

    ticker = "FAIL"
    headers = {"User-Agent": "test-agent"}
    data = fetch_and_parse_stock_data(ticker, headers)

    assert data is None
    mock_requests_get.assert_called_once_with(
        f"https://finviz.com/quote.ashx?t={ticker}&p=d", headers=headers
    )

def test_fetch_and_parse_stock_data_no_table(mock_requests_get):
    """
    Test fetch_and_parse_stock_data when no snapshot table is found.
    """
    html_content = "<html><body>No data here</body></html>"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = html_content.encode('utf-8')
    mock_requests_get.return_value = mock_response

    data = fetch_and_parse_stock_data("NOTABLE", {"User-Agent": "test-agent"})

    assert data is None

def test_fetch_and_parse_stock_data_empty_table(mock_requests_get):
    """
    Test fetch_and_parse_stock_data when snapshot table exists but has no label/value divs.
    """
    html_content = """
    <table class="snapshot-table2">
        <tr><td>No divs here</td></tr>
    </table>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = html_content.encode('utf-8')
    mock_requests_get.return_value = mock_response

    data = fetch_and_parse_stock_data("EMPTY", {"User-Agent": "test-agent"})

    assert data is None
