import ccxt
import pandas as pd
import ta
import time
from datetime import datetime
import plotext as plt
from dotenv import load_dotenv
import os

load_dotenv()

class TradingBot:
    def __init__(self, api_key, secret, symbol='BTC/USDT', timeframe='1m'):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True
        })
        self.symbol = symbol
        self.timeframe = timeframe
        self.balance = self.exchange.fetch_balance()['USDT']['free']
        self.trade_history = pd.DataFrame(columns=[
            'timestamp', 'type', 'price', 'quantity', 'sl', 'tp', 'pnl'
        ])
        self.active_trade = False
        self.start_balance = self.balance

    def _get_ohlcv(self):
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def _calculate_indicators(self, df):
        # Indicadores de tendência
        df['sma20'] = ta.trend.sma_indicator(df['close'], 20)
        df['sma50'] = ta.trend.sma_indicator(df['close'], 50)
        
        # Bollinger Bands
        indicator_bb = ta.volatility.BollingerBands(df['close'], 20, 2)
        df['bb_upper'] = indicator_bb.bollinger_hband()
        df['bb_lower'] = indicator_bb.bollinger_lband()
        
        # Volume
        df['volume_ma'] = ta.trend.sma_indicator(df['volume'], 20)
        return df
    
    def _show_compact_chart(self, df):
        plt.clear_figure()
        
        # Configuração da grade de subplots
        plt.subplots(2, 1)
        
        # Gráfico de preço (ocupa 2/3 do espaço)
        plt.subplot(1, 1)
        plt.plot(df['close'], label="Preço", color=51)
        plt.plot(df['sma20'], label="SMA20", color=214)
        plt.ylim(df['close'].min() * 0.998, df['close'].max() * 1.002)
        plt.plotsize(80, 15)  # Largura x Altura
        
        # Gráfico de volume (ocupa 1/3 do espaço)
        plt.subplot(2, 1)
        plt.bar(df['volume'], color=33)
        plt.plotsize(80, 5)
        plt.ylim(0, df['volume'].max() * 1.1)
        
        plt.show()
        
        # Info resumida
        last = df.iloc[-1]
        print(f"Último: {last['close']:.2f} | SMA20: {last['sma20']:.2f}")
        print(f"Variação 24h: {(last['close'] - df.iloc[0]['close'])/df.iloc[0]['close']*100:+.2f}%")

    def _show_market_status(self, df):
        plt.clear_figure()
        plt.subplots(2, 1)
        
        # Gráfico de preço
        plt.subplot(1, 1)
        plt.plot(df['close'], label="Preço", color=204)
        plt.plot(df['sma20'], label="SMA 20", color=226)
        plt.plot(df['sma50'], label="SMA 50", color=201)
        plt.plot(df['bb_upper'], label="BB Superior", color=196)
        plt.plot(df['bb_lower'], label="BB Inferior", color=34)
        plt.title(f"Análise de Mercado - {self.symbol}")
        plt.xlabel("Períodos")
        plt.ylabel("Preço (USDT)")
        
        # Gráfico de volume
        plt.subplot(2, 1)
        plt.bar(df['volume'], label="Volume", color=33)
        plt.plot(df['volume_ma'], label="Média Volume", color=214)
        plt.xlabel("Períodos")
        plt.ylabel("Volume")
        
        plt.show()
        
        # Estatísticas em tempo real
        last = df.iloc[-1]
        change_24h = ((last['close'] - df.iloc[0]['close']) / df.iloc[0]['close']) * 100
        print(f"\nÚltimo Preço: {last['close']:.2f}")
        print(f"Variação 24h: {change_24h:+.2f}%")
        print(f"Volume 24h: {df['volume'].sum():.2f} {self.symbol.split('/')[0]}")
        print(f"RSI Atual: {ta.momentum.rsi(df['close'], 14).iloc[-1]:.2f}")

    def _generate_signal(self, df):
        latest = df.iloc[-1]
        return (
            latest['sma20'] > latest['sma50'] and
            latest['close'] < latest['bb_lower'] and
            ta.momentum.rsi(df['close'], 14).iloc[-1] < 35
        )
    
    def _show_compact_performance(self, data):
        plt.clear_figure()
        plt.plot(data, color=46)
        plt.plotsize(60, 8)
        plt.title("Lucro Acumulado")
        plt.ylim(min(data)*0.95 if data else 0, max(data)*1.05 if data else 1)
        plt.show()

    def _calculate_position_size(self):
        return self.balance * 0.1

    def _execute_trade(self, price):
        position_size = self._calculate_position_size()
        quantity = position_size / price
        commission = position_size * 0.001
        self.balance -= commission
        
        trade_data = {
            'timestamp': datetime.now(),
            'type': 'buy',
            'price': price,
            'quantity': quantity,
            'sl': price * 0.98,
            'tp': price * 1.03,
            'pnl': None
        }

        # Criar DataFrame com tipos explícitos
        new_trade = pd.DataFrame([trade_data], columns=self.trade_history.columns)
        self.trade_history = pd.concat(
            [self.trade_history, new_trade],
            ignore_index=True,
            copy=False
        )
        self.active_trade = True
        print(f"\n▶ Trade Aberto: {quantity:.6f} {self.symbol} a ${price:.2f}")

    def _close_trade(self, price, reason):
        last_trade = self.trade_history.iloc[-1]
        pnl = (price - last_trade['price']) * last_trade['quantity']
        pnl -= price * last_trade['quantity'] * 0.001
        
        self.balance += pnl
        self.active_trade = False
        
        close_data = {
            'timestamp': datetime.now(),
            'type': 'sell',
            'price': price,
            'quantity': last_trade['quantity'],
            'sl': None,
            'tp': None,
            'pnl': pnl
        }
        
        # Garantir a consistência dos tipos
        new_close = pd.DataFrame([close_data], columns=self.trade_history.columns)
        self.trade_history = pd.concat(
            [self.trade_history, new_close],
            ignore_index=True,
            copy=False
        )
        color = 46 if pnl >= 0 else 196
        print(f"\n\033[38;5;{color}m◼ Trade Fechado ({reason}): P&L ${pnl:.2f}\033[0m")

    def _plot_performance(self, data):
        plt.clear_figure()
        plt.plot(data, color=51)
        plt.title("Evolução do Lucro Acumulado")
        plt.xlabel("Trades")
        plt.ylabel("Lucro (USDT)")
        plt.show()

    # def show_results(self):
    #     closed_trades = self.trade_history[self.trade_history['type'] == 'sell']
        
    #     print("\n" + "="*40)
    #     print(f"{' RESULTADOS FINAIS ':=^40}")
    #     print("="*40)
        
    #     print(f"\nSaldo Inicial: ${self.start_balance:.2f}")
    #     print(f"Saldo Final:   ${self.balance:.2f}")
        
    #     if not closed_trades.empty:
    #         cumulative_pnl = closed_trades['pnl'].cumsum()
    #         total_pnl = cumulative_pnl.iloc[-1]
    #         win_rate = (len(closed_trades[closed_trades['pnl'] > 0]) / len(closed_trades)) * 100
            
    #         print("\n=== ESTATÍSTICAS ===")
    #         print(f"Trades Realizados: {len(closed_trades)}")
    #         print(f"Lucro Total: ${total_pnl:.2f}")
    #         print(f"Taxa de Acerto: {win_rate:.1f}%")
            
    #         print("\n=== GRÁFICO DE PERFORMANCE ===")
    #         self._plot_performance(cumulative_pnl.tolist())
            
    #         print("\n=== ÚLTIMOS TRADES ===")
    #         for _, trade in closed_trades.tail(3).iterrows():
    #             pnl_sign = '+' if trade['pnl'] >=0 else '-'
    #             print(f"{trade['timestamp'].strftime('%d/%m %H:%M')} | "
    #                   f"Preço: ${trade['price']:.2f} | "
    #                   f"P&L: {pnl_sign}${abs(trade['pnl']):.2f}")
    #     else:
    #         print("\nNenhum trade realizado")

    ###### FUNÇÃO EM TESTE #####
    def show_results(self):
        closed_trades = self.trade_history[self.trade_history['type'] == 'sell']
        
        print("\n" + "="*40)
        print(f"{' RESULTADOS ':=^40}")
        print("="*40)
        
        print(f"\n💰 Saldo: ${self.start_balance:.2f} → ${self.balance:.2f}")
        
        if not closed_trades.empty:
            cumulative_pnl = closed_trades['pnl'].cumsum()
            
            print("\n📊 Performance:")
            self._show_compact_performance(cumulative_pnl.tolist())
            
            print("\n📝 Últimos Trades:")
            for _, trade in closed_trades.tail(2).iterrows():
                status = "✅ Lucro" if trade['pnl'] >=0 else "❌ Prejuízo"
                print(f"{trade['timestamp'].strftime('%H:%M')} | {status}: ${abs(trade['pnl']):.2f}")
        else:
            print("\n📭 Nenhum trade realizado")


    def run(self):
        print(f"\n🔎 Iniciando Monitoramento: {self.symbol}")
        try:
            while True:
                df = self._get_ohlcv()
                df = self._calculate_indicators(df)
                
                if not self.active_trade:
                    if self._generate_signal(df):
                        price = df.iloc[-1]['close']
                        self._execute_trade(price)
                    else:
                        plt.clc()
                        #self._show_market_status(df)
                        self._show_compact_chart(df)
                else:
                    last_trade = self.trade_history.iloc[-1]
                    current_price = df.iloc[-1]['close']
                    
                    if current_price <= last_trade['sl']:
                        self._close_trade(current_price, 'Stop Loss')
                    elif current_price >= last_trade['tp']:
                        self._close_trade(current_price, 'Take Profit')
                
                time.sleep(60)
                
        except Exception as e:
            print(f"\033[31mErro: {str(e)}\033[0m")
        except KeyboardInterrupt:
            self.show_results()

if __name__ == "__main__":

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    bot = TradingBot(api_key, api_secret)
    bot.run()