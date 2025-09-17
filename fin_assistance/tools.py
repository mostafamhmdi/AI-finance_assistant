import yfinance as yf
import ccxt
import pandas as pd
from advanced_ta import LorentzianClassification
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

def get_historical_data(symbol: str = 'TON/USDT', timeframe: str = '1h', limit: int = 1000) -> pd.DataFrame | str:
    """
    داده‌های کندل استیک را با استفاده از CCXT از صرافی KuCoin دریافت می‌کند.
    """
    try:

        exchange = ccxt.kucoin() 
        
        # بقیه کد دقیقاً مثل قبل است
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        if not ohlcv:
            return f"Error: No data found for symbol '{symbol}' on KuCoin."
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)
        df.columns = df.columns.str.lower()
        
        return df[['open', 'high', 'low', 'close', 'volume']]

    except Exception as e:
        return f"An error occurred fetching data from KuCoin using CCXT: {e}"

def analyze_lorentzian(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyzes the historical data DataFrame using the Lorentzian Classification indicator.
    """
    lc = LorentzianClassification(df)
    # lc.dump('data.csv')
    return lc.df


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches data with indicators, future profits, and details about the next signal.
    """
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['ema_20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
    df['ema_50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
    df['ema_100'] = EMAIndicator(close=df['close'], window=100).ema_indicator()
    df['ema_200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()

    return df

def plot_with_offset_targets(df: pd.DataFrame):
    """
    Plots a comprehensive chart with candlesticks, EMAs, RSI, and signals.
    """

    # 3. ساخت نمودار دو قسمتی (دو ردیف، یک ستون)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True, # محور افقی مشترک
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3] # 70% برای نمودار اصلی، 30% برای RSI
    )

    # --- بخش اول: نمودار اصلی قیمت ---
    
    # افزودن نمودار کندل استیک
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Candlestick'
    ), row=1, col=1)

    # افزودن میانگین‌های متحرک
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_20'], mode='lines', name='EMA 20', line=dict(color='cyan', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_50'], mode='lines', name='EMA 50', line=dict(color='yellow', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_100'], mode='lines', name='EMA 100', line=dict(color="#fd2307", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_200'], mode='lines', name='EMA 200', line=dict(color="#320faf", width=1)), row=1, col=1)

    # افزودن سیگنال‌های خرید/فروش (مثلث‌ها)
    buy_signals = df[df['isNewBuySignal']]
    sell_signals = df[df['isNewSellSignal']]
    fig.add_trace(go.Scatter(
        x=buy_signals.index, y=buy_signals['low'] * 0.98, mode='markers', name='Buy Signal',
        marker=dict(color='lime', symbol='triangle-up', size=10)
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=sell_signals.index, y=sell_signals['high'] * 1.02, mode='markers', name='Sell Signal',
        marker=dict(color='red', symbol='triangle-down', size=10)
    ), row=1, col=1)
    
    # --- بخش دوم: نمودار RSI ---
    
    # افزودن خط RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color='white', width=1.5)), row=2, col=1)
    # افزودن خطوط اشباع خرید و فروش
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="lime", row=2, col=1)

    # --- بخش سوم: رنگی کردن پس‌زمینه بر اساس ستون signal ---
    in_position_long = False
    in_position_short = False
    start_date = None

    for i in range(len(df)):
        current_date = df.index[i]
        # شروع پوزیشن خرید
        if df['signal'][i] == 1 and not in_position_long:
            start_date = current_date
            in_position_long = True
        # پایان پوزیشن خرید
        elif df['signal'][i] != 1 and in_position_long:
            fig.add_vrect(x0=start_date, x1=current_date, fillcolor="green", opacity=0.15, layer="below", line_width=0, row=1, col=1)
            in_position_long = False
        
        # شروع پوزیشن فروش
        if df['signal'][i] == -1 and not in_position_short:
            start_date = current_date
            in_position_short = True
        # پایان پوزیشن فروش
        elif df['signal'][i] != -1 and in_position_short:
            fig.add_vrect(x0=start_date, x1=current_date, fillcolor="red", opacity=0.15, layer="below", line_width=0, row=1, col=1)
            in_position_short = False

    # 4. زیباسازی نهایی نمودار
    fig.update_layout(
        title='تحلیل جامع با اندیکاتورها و سیگنال‌ها',
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)

    # fig.show()
    return fig


# In tools.py

import json

def send_signal_to_n8n(webhook_url, signal_data):
    """اطلاعات سیگنال را به وبهوک n8n ارسال می‌کند."""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, data=json.dumps(signal_data), headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"✅ سیگنال با موفقیت به n8n ارسال شد: {signal_data['signal']}")
        else:
            print(f"❌ خطا در ارسال سیگنال به n8n. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"🔥 خطای شبکه در هنگام اتصال به n8n: {e}")