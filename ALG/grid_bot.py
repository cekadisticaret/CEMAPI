"""
grid_bot.py
Grid Trading Bot: Belirli aralıkta alım-satım emirleri yerleştirir.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class GridLevel:
    price: float
    is_buy: bool
    is_sell: bool
    executed: bool = False

class GridBot:
    def __init__(self, lower_price: float, upper_price: float, grids: int = 10, 
                 total_investment: float = 1000.0):
        self.lower = lower_price
        self.upper = upper_price
        self.grids = grids
        self.investment = total_investment
        self.grid_size = (upper_price - lower_price) / grids
        self.per_grid_amount = total_investment / grids
        self.levels: List[GridLevel] = []
        self._create_grids()

    def _create_grids(self):
        for i in range(self.grids + 1):
            price = self.lower + i * self.grid_size
            is_buy = i < self.grids  # En üst seviye hariç hepsinde buy
            is_sell = i > 0  # En alt seviye hariç hepsinde sell
            self.levels.append(GridLevel(price=price, is_buy=is_buy, is_sell=is_sell))

    def check_triggers(self, current_price: float) -> List[Dict]:
        """Mevcut fiyata göre hangi grid seviyeleri tetiklendi?"""
        triggers = []
        for level in self.levels:
            if not level.executed:
                if level.is_buy and current_price <= level.price:
                    triggers.append({"action": "BUY", "price": level.price, "amount": self.per_grid_amount})
                    level.executed = True
                elif level.is_sell and current_price >= level.price:
                    triggers.append({"action": "SELL", "price": level.price, "amount": self.per_grid_amount})
                    level.executed = True
        return triggers

    def simulate(self, prices: pd.Series) -> Dict:
        """Grid bot'u geçmiş fiyatlar üzerinde simüle eder."""
        trades = []
        inventory = 0.0
        cash = self.investment

        for price in prices:
            for level in self.levels:
                if level.is_buy and price <= level.price and inventory < self.per_grid_amount * self.grids:
                    amount = self.per_grid_amount / price
                    inventory += amount
                    cash -= self.per_grid_amount
                    trades.append({"type": "BUY", "price": price, "amount": amount})
                elif level.is_sell and price >= level.price and inventory > 0:
                    amount = self.per_grid_amount / price
                    if inventory >= amount:
                        inventory -= amount
                        cash += self.per_grid_amount
                        trades.append({"type": "SELL", "price": price, "amount": amount})

        final_value = cash + inventory * prices.iloc[-1]
        pnl = final_value - self.investment

        return {
            "initial_investment": self.investment,
            "final_value": round(final_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": f"{pnl/self.investment:.2%}",
            "total_trades": len(trades),
            "grid_levels": len(self.levels),
            "range": f"{self.lower} - {self.upper}"
        }

    def run(self, current_price: float, prices: pd.Series = None) -> Dict:
        if prices is not None:
            return self.simulate(prices)

        triggers = self.check_triggers(current_price)
        return {
            "current_price": current_price,
            "grid_range": f"{self.lower} - {self.upper}",
            "grid_size": round(self.grid_size, 2),
            "active_triggers": triggers,
            "next_buy": next((l.price for l in self.levels if l.is_buy and not l.executed and l.price < current_price), None),
            "next_sell": next((l.price for l in self.levels if l.is_sell and not l.executed and l.price > current_price), None)
        }

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    bot = GridBot(lower_price=80, upper_price=120, grids=10)
    print(bot.run(prices.iloc[-1], prices))
