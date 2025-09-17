import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from tools import get_historical_data, analyze_lorentzian, add_technical_indicators, plot_with_offset_targets, send_signal_to_n8n

# تنظیمات اولیه صفحه
st.set_page_config(layout="wide", page_title="Live Crypto Dashboard")

SUPPORTED_SYMBOLS = ['TON/USDT', 'ETH/USDT', 'ONDO/USDT', 'RENDER/USDT', 'CRO/USDT']

selected_symbol = st.selectbox(
    'ارز مورد نظر را انتخاب کنید:',
    SUPPORTED_SYMBOLS,
    index=0  # 'TON/USDT' به عنوان گزینه پیش‌فرض انتخاب می‌شود
)

st.title(f"📊 داشبورد زنده ارز دیجیتال ({selected_symbol})")

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.min
    st.session_state.final_data = pd.DataFrame()
    st.session_state.current_symbol = None # ---- تغییر ----: برای ذخیره ارز فعلی

# تعریف ثابت‌ها
UPDATE_INTERVAL_SECONDS = 1800 # 30 دقیقه

# ---- تابع اصلی برای اجرای تحلیل‌ها ----
def run_analysis(symbol: str):
    """این تابع داده‌ها را می‌گیرد، تحلیل می‌کند و در session_state ذخیره می‌کند."""
    print(f"در حال به‌روزرسانی داده‌ها برای {symbol}...")
    try:
        data = get_historical_data(symbol=symbol, timeframe='1h', limit=1000)
        if isinstance(data, str):
            st.error(f"خطا در دریافت داده: {data}")
            return # در صورت خطا، از تابع خارج شو

        analyzed_data = analyze_lorentzian(data)
        final_data = add_technical_indicators(analyzed_data)
        
        # داده‌های جدید را در session_state ذخیره کن
        st.session_state.final_data = final_data
        st.session_state.last_update = datetime.now()
        st.session_state.current_symbol = symbol
        print("به‌روزرسانی با موفقیت انجام شد.")

    except Exception as e:
        st.error(f"یک خطای کلی در هنگام تحلیل رخ داد: {e}")

# ---- بررسی زمان برای اجرای مجدد تحلیل ----
now = datetime.now()
time_since_last_update = (now - st.session_state.last_update).total_seconds()

# اگر ۳۰ دقیقه گذشته باشد یا اولین اجرای برنامه باشد، تحلیل را اجرا کن
if (time_since_last_update > UPDATE_INTERVAL_SECONDS or
    selected_symbol != st.session_state.current_symbol or
    st.session_state.final_data.empty):
    run_analysis(selected_symbol)


# ---- بخش نمایش داشبورد (این بخش همیشه اجرا می‌شود) ----
st.subheader("وضعیت لحظه‌ای")

# اگر داده‌ای برای نمایش وجود نداشت، یک پیام نشان بده
if st.session_state.final_data.empty:
    st.warning("در حال دریافت اولیه داده‌ها... لطفاً چند لحظه صبر کنید.")
else:
    # از داده‌های ذخیره شده در session_state برای نمایش استفاده کن
    final_data = st.session_state.final_data
    last_row = final_data.iloc[-1]
    
    # محاسبه مقادیر
    rsi_now = last_row.get('rsi', 0)
    buy_signal = last_row.get('isNewBuySignal', False)
    sell_signal = last_row.get('isNewSellSignal', False)
    lorentz_signal = last_row.get('prediction', 'N/A')
    
    rsi_diff = 0
    if len(final_data) >= 8:
        rsi_7_candles_ago = final_data.iloc[-8].get('rsi', 0)
        rsi_diff = rsi_now - rsi_7_candles_ago

    # نمایش متریک‌ها
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="RSI (14) لحظه‌ای", value=f"{rsi_now:.2f}")
    col2.metric(label="تغییر RSI در ۷ کندل", value=f"{rsi_diff:.2f}", delta=f"{rsi_diff:.2f}")
    col3.metric(label="سیگنال لورنتزین", value=str(lorentz_signal))

    # منطق ارسال سیگنال (بدون تغییر)
  
    # if buy_signal:
    #     col4.metric(label="سیگنال خرید یا فروش؟", value="Buy Signal!")
    #     signal_info = {"type": "BUY", "price": last_row['close'], "rsi": rsi_now}
    #     # send_signal_to_n8n(n8n_webhook_url, signal_info) # برای جلوگیری از ارسال مکرر، این را مدیریت کنید
    # elif sell_signal:
    #     col4.metric(label="سیگنال خرید یا فروش؟", value="Sell Signal!")
    #     signal_info = {"type": "SELL", "price": last_row['close'], "rsi": rsi_now}
    #     # send_signal_to_n8n(n8n_webhook_url, signal_info)
    # else:
    #     col4.metric(label="سیگنال خرید یا فروش؟", value="No Sign!")
    # with col4:
    #     st.markdown('<p style="font-size: 1rem; margin-bottom: 0;">سیگنال خرید یا فروش؟</p>', unsafe_allow_html=True)
    #     if buy_signal:
    #         st.markdown('<p style="font-size: 1.5rem; color: #33ff33; font-weight: bold;">!Buy Signal</p>', unsafe_allow_html=True)
    #         signal_info = {"type": "BUY", "price": last_row['close'], "rsi": rsi_now}
    #         # send_signal_to_n8n(n8n_webhook_url, signal_info)
    #     elif sell_signal:
    #         st.markdown('<p style="font-size: 1.5rem; color: #ff4d4d; font-weight: bold;">!Sell Signal</p>', unsafe_allow_html=True)
    #         signal_info = {"type": "SELL", "price": last_row['close'], "rsi": rsi_now}
    #         # send_signal_to_n8n(n8n_webhook_url, signal_info)
    #     else:
    #         st.markdown('<p style="font-size: 1.5rem; color: gray;">!No Sign</p>', unsafe_allow_html=True)
    N8N_WEBHOOK_URL = "http://host.docker.internal:5678/webhook/ea8e77eb-0809-4ff9-bcf7-8fa53f4e9ef9"
    with col4:
        st.markdown('<p style="font-size: 1rem; margin-bottom: 0;">سیگنال خرید یا فروش؟</p>', unsafe_allow_html=True)
        if buy_signal:
            st.markdown('<p style="font-size: 1.5rem; color: #33ff33; font-weight: bold;">!Buy Signal</p>', unsafe_allow_html=True)
            # ---- بخش جدید ----
            signal_info = {
                "symbol": "TON/USDT", 
                "signal": "BUY", 
                "price": last_row['close'], 
                "rsi": f"{last_row['rsi']:.2f}"
            }
            send_signal_to_n8n(N8N_WEBHOOK_URL, signal_info)
            # ---- پایان بخش جدید ----
        elif sell_signal:
            st.markdown('<p style="font-size: 1.5rem; color: #ff4d4d; font-weight: bold;">!Sell Signal</p>', unsafe_allow_html=True)
            # ---- بخش جدید ----
            signal_info = {
                "symbol": "TON/USDT", 
                "signal": "SELL", 
                "price": last_row['close'], 
                "rsi": f"{last_row['rsi']:.2f}"
            }
            send_signal_to_n8n(N8N_WEBHOOK_URL, signal_info)
            # ---- پایان بخش جدید ----
        else:
            st.markdown('<p style="font-size: 1.5rem; color: gray;">!No Sign</p>', unsafe_allow_html=True)
        
    # نمایش نمودار
    expander = st.expander("📈 مشاهده جزئیات و نمودار 120 کندل اخیر", expanded=True)
    fig = plot_with_offset_targets(final_data.tail(120))
    expander.plotly_chart(fig, use_container_width=True)

# ---- بخش جدید: ایجاد یک مکانیزم برای اجرای مجدد اسکریپت ----
# این کد یک متا تگ در HTML صفحه تزریق می‌کند که باعث می‌شود صفحه هر ۶۰ ثانیه رفرش شود
# این کار باعث اجرای مجدد اسکریپت و بررسی شرط زمان می‌شود.
st.components.v1.html("<meta http-equiv='refresh' content='60'>", height=0)