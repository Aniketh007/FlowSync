import requests
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image
import io
import base64
import os

class SimpleStockProvider:
    def __init__(self, api_key='6F4WA1R4O9Z5R8L1'):
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required")
        
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_stock_quote(self, symbol):
        """Get basic stock quote information"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if "Global Quote" not in data or not data["Global Quote"]:
            return None
        
        quote = data["Global Quote"]
        
        # Extract and format the data
        result = {
            'symbol': symbol,
            'price': float(quote.get('05. price', 0)),
            'change': float(quote.get('09. change', 0)),
            'change_percent': quote.get('10. change percent', '0%'),
            'high': float(quote.get('03. high', 0)),
            'low': float(quote.get('04. low', 0)),
            'volume': int(quote.get('06. volume', 0)),
            'latest_trading_day': quote.get('07. latest trading day', '')
        }
        
        return result
    
    def get_simple_chart(self, symbol):
        """Generate a simple chart showing yesterday vs today price"""
        # Get daily data
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': 'compact',
            'apikey': self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if "Time Series (Daily)" not in data:
            return None
        
        # Convert to DataFrame
        time_series = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Rename columns
        df.columns = [col.split('. ')[1] for col in df.columns]
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Sort by date and get last 5 days
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df.tail(5)  # Get last 5 days for a bit more context
        
        # Create a simple chart
        plt.figure(figsize=(8, 4))
        plt.plot(df.index, df['close'], marker='o', linestyle='-', linewidth=2, color='#1F77B4')
        
        # Highlight the last day
        plt.scatter(df.index[-1], df['close'].iloc[-1], color='red', s=100, zorder=5)
        
        # Add labels
        plt.title(f"{symbol} Stock Price - Last 5 Trading Days", fontsize=14)
        plt.ylabel("Price ($)", fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert to base64
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        img_data = base64.b64encode(img_buf.read()).decode('utf-8')
        plt.close()
        
        return img_data
# prompt: get the stock information for today from the above class
symbol=input("Enter the comapny you want the stock information of")
stock_provider = SimpleStockProvider()
stock_info = stock_provider.get_stock_quote(symbol)

if stock_info:
    print(f"Stock Information for {stock_info['symbol']}:")
    print(f"- Price: {stock_info['price']}")
    print(f"- Change: {stock_info['change']} ({stock_info['change_percent']})")
    print(f"- High: {stock_info['high']}")
    print(f"- Low: {stock_info['low']}")
    print(f"- Volume: {stock_info['volume']}")
    print(f"- Latest Trading Day: {stock_info['latest_trading_day']}")
else:
    print("Could not retrieve stock information.")

stock_img=stock_provider.get_simple_chart(symbol)
display(Image(data=base64.b64decode(stock_img)))