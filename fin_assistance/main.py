from tools import get_historical_data, analyze_lorentzian,add_technical_indicators

symbol_to_check = 'TON/USDT'

historical_data = get_historical_data(symbol_to_check)

if isinstance(historical_data, str):
    print(f"❌ خطا: {historical_data}")
else:
    print("✅ داده‌های تاریخی با موفقیت دریافت شد.")
    
    print("\n۲. در حال تحلیل با Lorentzian Classification...")
    # ارسال DataFrame به تابع تحلیل جدید
    analyzed_data = analyze_lorentzian(historical_data)
    print(analyzed_data.head())
    print(".........................................................")
    print(".........................................................")
    final_data = add_technical_indicators(analyzed_data)
    print(final_data.tail())