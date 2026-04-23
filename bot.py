import requests, time, pandas as pd, numpy as np
from datetime import datetime

# ===== DATA KAMU UDAH GUE ISIN =====
TELEGRAM_TOKEN = "8667387518:AAGSYzF2_e5P-kmILydkpXw8vUua0Vhcaqc"
CHAT_ID = "7790422420" 
TWELVE_API = "3e4df66d466b4e0fbfd76f60ecf8c8d6"
# ===================================

SYMBOL = "XAU/USD"
INTERVAL = "30min"
SCORE_MIN = 4 

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

def get_data():
    url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={INTERVAL}&outputsize=100&apikey={TWELVE_API}"
    r = requests.get(url, timeout=15).json()
    if 'values' not in r: 
        print("Error API:", r)
        return None
    df = pd.DataFrame(r['values'])
    df = df.astype({'open':'float','high':'float','low':'float','close':'float','volume':'float'})
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df.iloc[::-1].reset_index(drop=True)

def rsi(close, p=14):
    d = close.diff()
    g = (d.where(d > 0, 0)).rolling(p).mean()
    l = (-d.where(d < 0, 0)).rolling(p).mean()
    return 100 - (100 / (1 + g/l))

def calc_score(df):
    c,h,l = df['close'],df['high'],df['low']
    e21,c50,c200 = c.ewm(span=21).mean(),c.ewm(span=50).mean(),c.ewm(span=200).mean()
    r = rsi(c,14)
    tr = np.maximum(h-l, np.maximum(abs(h-c.shift(1)), abs(l-c.shift(1))))
    atr = tr.rolling(14).mean()
    i = len(df)-1
    
    buy = sum([c[i]>e21[i], e21[i]>c50[i]>c200[i], 50<r[i]<70, c[i]>c[i-1], c[i]>c200[i]])
    sell = sum([c[i]<e21[i], e21[i]<c50[i]<c200[i], 30<r[i]<50, c[i]<c[i-1], c[i]<c200[i]])
    if atr[i] < 0.15: buy=sell=0 # Filter spread/PHP
    return buy,sell,c[i],atr[i]

def main():
    send_telegram("✅ Bot XAUUSD M30 ON. Monitoring Score 4/5...")
    last = None
    while True:
        try:
            df = get_data()
            if df is None: time.sleep(120); continue
            b,s,price,atr = calc_score(df)
            now = datetime.now().strftime("%H:%M:%S WIB")
            if b >= SCORE_MIN and last!= f"B{price}":
                send_telegram(f"🟢 <b>BUY XAUUSD M30</b>\nHarga: <code>{price:.2f}</code>\nScore: <b>{b}/5</b>\nATR: {atr:.2f}\n{now}")
                last = f"B{price}"
            elif s >= SCORE_MIN and last!= f"S{price}":
                send_telegram(f"🔴 <b>SELL XAUUSD M30</b>\nHarga: <code>{price:.2f}</code>\nScore: <b>{s}/5</b>\nATR: {atr:.2f}\n{now}")
                last = f"S{price}"
            time.sleep(120)
        except Exception as e: print(e); time.sleep(120)

if __name__ == "__main__": main()
