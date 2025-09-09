import streamlit as st
import time
import pandas as pd
from tools import get_historical_data, analyze_lorentzian, add_technical_indicators,plot_with_offset_targets

st.set_page_config(layout="wide", page_title="Live Crypto Dashboard")
st.title("📊 داشبورد زنده ارز دیجیتال (TON/USDT)")

st.subheader("وضعیت لحظه‌ای")
col1, col2, col3,col4  = st.columns(4)
rsi_placeholder = col1.empty()
rsi_diff_placeholder = col2.empty()
lorentz_placeholder = col3.empty()
signal_placeholder = col4.empty()


expander = st.expander("📈 مشاهده جزئیات و نمودار ۴۸ کندل اخیر", expanded=False) # expanded=False یعنی به صورت پیش‌فرض بسته باشد
plot_placeholder = expander.empty()

while True:
    print("در حال به‌روزرسانی داده‌ها...")
    try:
        # ۱. دریافت داده‌های جدید
        # ۴۸ کندل + داده‌های بیشتر برای محاسبه صحیح اندیکاتورها
        data = get_historical_data(timeframe='1h', limit=1000) 
        if isinstance(data, str):
            st.error(f"خطا در دریافت داده: {data}")
            continue

        # ۲. اجرای تحلیل‌ها
        analyzed_data = analyze_lorentzian(data)
        final_data = add_technical_indicators(analyzed_data)

        # ۳. محاسبه مقادیر برای داشبورد کوچک
        if not final_data.empty:
            print("داده ها سالم اند...")
            last_row = final_data.iloc[-1]
            rsi_now = last_row['rsi']
            buy_signal = last_row['isNewBuySignal']
            sell_signal = last_row['isNewSellSignal']
            lorentz_signal = analyzed_data.iloc[-1]['prediction']
            
            # --- بخش اصلاح شده ---
            # فقط در صورتی تغییرات RSI را حساب کن که حداقل ۸ ردیف داده داشته باشیم
            if len(final_data) >= 8:
                rsi_7_candles_ago = final_data.iloc[-8]['rsi']
                rsi_diff = rsi_now - rsi_7_candles_ago
            else:
                # اگر داده کافی نبود، یک مقدار پیش‌فرض نشان بده
                rsi_diff = 0 
            # --- پایان بخش اصلاح شده ---

            # ۴. به‌روزرسانی مقادیر روی داشبورد
            rsi_placeholder.metric(label="RSI (14) لحظه‌ای", value=f"{rsi_now:.2f}")
            rsi_diff_placeholder.metric(label="تغییر RSI در ۷ کندل", value=f"{rsi_diff:.2f}", delta=f"{rsi_diff:.2f}")
            lorentz_placeholder.metric(label="سیگنال لورنتزین", value=str(lorentz_signal))
            if buy_signal == False and sell_signal == False:
                signal_placeholder.metric(label="سیگنال خرید یا فروش؟", value=str("No Sign!"))
            elif buy_signal == True:
                signal_placeholder.metric(label="سیگنال خرید یا فروش؟", value=str("Buy Signal!"))
            elif sell_signal == True:
                signal_placeholder.metric(label="سیگنال خرید یا فروش؟", value=str("Sell Signal!"))
            
            
            fig = plot_with_offset_targets(final_data.tail(48)) 
            plot_placeholder.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"یک خطای کلی رخ داد: {e}")
    
    # انتظار به مدت ۳۰ دقیقه
    time.sleep(1800)