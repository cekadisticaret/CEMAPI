"""
liquidation_cascade_fade.py
Likidasyon Kaskadi Fade: Zorunlu kapanis kaskadini tespit edip tersine
pozisyon acar. 1-3 dakikalik scalping.
"""
import pandas as pd
import numpy as np
from typing import Dict

class LiquidationCascadeFade:
    def __init__(self, 
                 price_speed_threshold: float = 0.03,  # %3 5-mum hiz
                 volume_mult: float = 3.0,  # 3x ortalama hacim
                 cooldown_bars: int = 3,
                 max_hold_bars: int = 3,
                 fade_pct: float = 0.005):
        """
        Args:
            price_speed_threshold: 5 mumluk fiyat degisimi esigi (%)
            volume_mult: Hacim carpani esigi
            cooldown_bars: Tekrar giris bekleme suresi
            max_hold_bars: Maksimum tutma suresi
            fade_pct: Karsi pozisyon acma mesafesi (%)
        """
        self.price_speed_threshold = price_speed_threshold
        self.volume_mult = volume_mult
        self.cooldown_bars = cooldown_bars
        self.max_hold_bars = max_hold_bars
        self.fade_pct = fade_pct

    def calculate(self, close: pd.Series, volume: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"close": close, "volume": volume})

        # 5 mumluk fiyat hizi
        df["price_change_5"] = close.pct_change(5)

        # Hacim ortalamasi
        df["vol_avg_20"] = volume.rolling(20).mean()
        df["vol_ratio"] = volume / df["vol_avg_20"]

        # Kaskad tespiti
        df["cascade_down"] = (df["price_change_5"] < -self.price_speed_threshold) &                              (df["vol_ratio"] > self.volume_mult)
        df["cascade_up"] = (df["price_change_5"] > self.price_speed_threshold) &                            (df["vol_ratio"] > self.volume_mult)

        # Mean reversion sinyali (kaskadin ardindan)
        df["fade_long"] = df["cascade_down"].shift(1) & (close > close.shift(1))
        df["fade_short"] = df["cascade_up"].shift(1) & (close < close.shift(1))

        return df

    def generate_signal(self, close: pd.Series, volume: pd.Series) -> Dict:
        df = self.calculate(close, volume)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        price = latest["close"]
        price_change = latest["price_change_5"]
        vol_ratio = latest["vol_ratio"]

        # Aktif kaskad var mi?
        if latest["cascade_down"]:
            signal = "CASCADE_DOWN"
            desc = f"Dusus kaskadi! 5-mum: {price_change:.2%}, hacim: {vol_ratio:.1f}x. Fade long dusun."
            entry = price * (1 + self.fade_pct)
            stop = price * (1 - self.fade_pct * 2)
        elif latest["cascade_up"]:
            signal = "CASCADE_UP"
            desc = f"Yukselis kaskadi! 5-mum: {price_change:.2%}, hacim: {vol_ratio:.1f}x. Fade short dusun."
            entry = price * (1 - self.fade_pct)
            stop = price * (1 + self.fade_pct * 2)
        elif prev["cascade_down"] and close.iloc[-1] > close.iloc[-2]:
            signal = "FADE_LONG"
            desc = "Kaskad sonrasi donus tespit edildi. Long fade aktif."
            entry = price
            stop = price * 0.99
        elif prev["cascade_up"] and close.iloc[-1] < close.iloc[-2]:
            signal = "FADE_SHORT"
            desc = "Kaskad sonrasi donus tespit edildi. Short fade aktif."
            entry = price
            stop = price * 1.01
        else:
            signal = "NO_CASCADE"
            desc = "Kaskad yok. Bekle."
            entry = None
            stop = None

        return {
            "signal": signal,
            "price": round(float(price), 2),
            "price_speed_5m": f"{price_change:.2%}",
            "volume_ratio": round(float(vol_ratio), 2) if not pd.isna(vol_ratio) else None,
            "suggested_entry": round(float(entry), 2) if entry else None,
            "suggested_stop": round(float(stop), 2) if stop else None,
            "max_hold_bars": self.max_hold_bars,
            "description": desc
        }

    def run(self, close: pd.Series, volume: pd.Series) -> Dict:
        return self.generate_signal(close, volume)


if __name__ == "__main__":
    np.random.seed(42)
    n = 100
    close = pd.Series(100 + np.cumsum(np.random.randn(n) * 2))
    # Kaskad simulasyonu
    close.iloc[50:55] = close.iloc[50] * (1 - np.linspace(0, 0.05, 5))
    volume = pd.Series(np.random.randint(1000, 5000, n))
    volume.iloc[50:55] *= 4  # Hacim patlamasi

    print(LiquidationCascadeFade().run(close, volume))
