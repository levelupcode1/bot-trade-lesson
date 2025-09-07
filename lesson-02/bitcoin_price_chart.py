#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
matplotlib을 사용한 비트코인 가격 차트 생성
CoinGecko API에서 가격 데이터를 수집하고 시간-가격 선 그래프를 생성합니다.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import numpy as np

class BitcoinPriceChart:
    def __init__(self):
        """Initialize Bitcoin price chart generator"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # User-Agent setup
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # matplotlib font setup
        self.setup_font()
        
        # chart style setup
        try:
            plt.style.use('default')
        except:
            pass
        
    def setup_font(self):
        """Font setup for English text"""
        try:
            # Use system default fonts
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.size'] = 10
                
            print("Font setup completed successfully.")
        except Exception as e:
            print(f"Font setup error: {e}")
            print("Using default font.")
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def get_bitcoin_price_history(self, days: int = 30, currency: str = "krw") -> Optional[List[Tuple[datetime, float]]]:
        """
        Retrieve Bitcoin historical price data.
        
        Args:
            days: Number of days to retrieve (default: 30 days)
            currency: Currency (default: "krw")
            
        Returns:
            List of (time, price) tuples or None (on error)
        """
        try:
            endpoint = "/coins/bitcoin/market_chart"
            params = {
                "vs_currency": currency,
                "days": days,
                "interval": "daily"
            }
            
            print(f"Retrieving Bitcoin {days}-day price data... (Currency: {currency.upper()})")
            
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "prices" in data and data["prices"]:
                    # Parse price data
                    price_data = []
                    for timestamp_ms, price in data["prices"]:
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        price_data.append((dt, price))
                    
                    print(f"Collected {len(price_data)} price data points.")
                    return price_data
                else:
                    print("Price data not found.")
                    return None
            else:
                print(f"API request failed: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Error occurred while retrieving data: {e}")
            return None
    
    def get_current_bitcoin_price(self, currency: str = "krw") -> Optional[float]:
        """
        Retrieve current Bitcoin price.
        
        Args:
            currency: Currency (default: "krw")
            
        Returns:
            Current price or None (on error)
        """
        try:
            endpoint = "/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": currency
            }
            
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "bitcoin" in data and currency in data["bitcoin"]:
                    return data["bitcoin"][currency]
            
            return None
            
        except Exception as e:
            print(f"Current price retrieval error: {e}")
            return None
    
    def format_price(self, price: float, currency: str = "krw") -> str:
        """
        Format price in user-friendly format.
        
        Args:
            price: Price value
            currency: Currency
            
        Returns:
            Formatted price string
        """
        if currency.lower() == "krw":
            if price >= 1000000:
                return f"{price/1000000:.1f}M KRW"
            elif price >= 1000:
                return f"{price/1000:.1f}K KRW"
            else:
                return f"{price:,.0f} KRW"
        elif currency.lower() == "usd":
            if price >= 1000000:
                return f"${price/1000000:.1f}M"
            elif price >= 1000:
                return f"${price/1000:.1f}K"
            else:
                return f"${price:,.2f}"
        else:
            return f"{price:,.2f} {currency.upper()}"
    
    def create_price_chart(self, price_data: List[Tuple[datetime, float]], 
                          currency: str = "krw", days: int = 30):
        """
        Create Bitcoin price chart.
        
        Args:
            price_data: List of (time, price) tuples
            currency: Currency
            days: Number of days retrieved
        """
        if not price_data:
            print("No data available to create chart.")
            return
        
        # Separate data
        dates = [item[0] for item in price_data]
        prices = [item[1] for item in price_data]
        
        # Get current price
        current_price = self.get_current_bitcoin_price(currency)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Draw line graph
        line = ax.plot(dates, prices, linewidth=2.5, color='#f7931a', 
                      marker='o', markersize=4, markerfacecolor='white', 
                      markeredgecolor='#f7931a', markeredgewidth=1.5)
        
        # Highlight current price
        if current_price:
            ax.axhline(y=current_price, color='red', linestyle='--', alpha=0.7, 
                      linewidth=1.5, label=f'Current Price: {self.format_price(current_price, currency)}')
        
        # Show highest/lowest prices
        max_price = max(prices)
        min_price = min(prices)
        max_date = dates[prices.index(max_price)]
        min_date = dates[prices.index(min_price)]
        
        # Highest price point
        ax.scatter(max_date, max_price, color='red', s=100, zorder=5, 
                  label=f'Highest: {self.format_price(max_price, currency)}')
        ax.annotate(f'Highest\n{self.format_price(max_price, currency)}', 
                   xy=(max_date, max_price), xytext=(10, 10),
                   textcoords='offset points', ha='left', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                   fontsize=10, color='white', weight='bold')
        
        # Lowest price point
        ax.scatter(min_date, min_price, color='blue', s=100, zorder=5,
                  label=f'Lowest: {self.format_price(min_price, currency)}')
        ax.annotate(f'Lowest\n{self.format_price(min_price, currency)}', 
                   xy=(min_date, min_price), xytext=(10, -10),
                   textcoords='offset points', ha='left', va='top',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                   fontsize=10, color='white', weight='bold')
        
        # Chart styling
        ax.set_title(f'Bitcoin Price Movement ({days} days)', 
                    fontsize=20, fontweight='bold', pad=20, color='#2c3e50')
        
        # X-axis setup
        ax.set_xlabel('Date', fontsize=14, fontweight='bold', color='#2c3e50')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Y-axis setup
        ax.set_ylabel(f'Price ({currency.upper()})', fontsize=14, fontweight='bold', color='#2c3e50')
        
        # Grid setup
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Legend setup
        ax.legend(loc='upper left', fontsize=12, framealpha=0.9)
        
        # Add statistics info
        price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
        change_symbol = "▲" if price_change >= 0 else "▼"
        change_color = 'green' if price_change >= 0 else 'red'
        
        stats_text = f"""Statistics
Start Price: {self.format_price(prices[0], currency)}
Current Price: {self.format_price(prices[-1], currency)}
{days}-day Change: {change_symbol} {price_change:+.2f}%
Highest: {self.format_price(max_price, currency)}
Lowest: {self.format_price(min_price, currency)}
Average: {self.format_price(np.mean(prices), currency)}"""
        
        # Display statistics on chart
        ax.text(0.98, 0.02, stats_text, transform=ax.transAxes, 
               fontsize=11, verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8),
               fontfamily='monospace')
        
        # Background color setup
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('white')
        
        # Layout adjustment
        plt.tight_layout()
        
        # Show chart
        plt.show()
        
        # Save chart
        filename = f"bitcoin_price_chart_{currency}_{days}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Chart saved as '{filename}'.")
        
        return fig
    
    def create_multiple_currency_chart(self, currencies: List[str] = ["krw", "usd"], days: int = 30):
        """
        Create chart comparing Bitcoin prices in multiple currencies.
        
        Args:
            currencies: List of currencies to compare
            days: Number of days to retrieve
        """
        fig, ax = plt.subplots(figsize=(16, 10))
        
        colors = ['#f7931a', '#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
        
        for i, currency in enumerate(currencies):
            price_data = self.get_bitcoin_price_history(days, currency)
            if price_data:
                dates = [item[0] for item in price_data]
                prices = [item[1] for item in price_data]
                
                # Normalize prices to relative change rate compared to first price
                normalized_prices = [(price / prices[0]) * 100 for price in prices]
                
                ax.plot(dates, normalized_prices, linewidth=2.5, 
                       color=colors[i % len(colors)], marker='o', markersize=3,
                       label=f'{currency.upper()} (Base: 100%)')
        
        ax.set_title(f'Bitcoin Price Change Rate Comparison ({days} days)', 
                    fontsize=20, fontweight='bold', pad=20, color='#2c3e50')
        ax.set_xlabel('Date', fontsize=14, fontweight='bold')
        ax.set_ylabel('Relative Change Rate (%)', fontsize=14, fontweight='bold')
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=12)
        
        plt.tight_layout()
        plt.show()

def main():
    """Main function"""
    print("=" * 70)
    print("Bitcoin Price Chart Generator using matplotlib")
    print("=" * 70)
    
    # Initialize chart generator
    chart_generator = BitcoinPriceChart()
    
    try:
        # Get user input
        print("\n📊 Select chart option:")
        print("1. Single currency price chart (default: KRW, 30 days)")
        print("2. Multiple currency comparison chart")
        print("3. Custom settings")
        
        choice = input("\nSelect (1-3, default: 1): ").strip() or "1"
        
        if choice == "1":
            # Create default chart
            print("\n🔄 Creating default chart...")
            price_data = chart_generator.get_bitcoin_price_history(30, "krw")
            if price_data:
                chart_generator.create_price_chart(price_data, "krw", 30)
            else:
                print("❌ Unable to retrieve data.")
                
        elif choice == "2":
            # Multiple currency comparison chart
            print("\n🔄 Creating multiple currency comparison chart...")
            chart_generator.create_multiple_currency_chart(["krw", "usd"], 30)
            
        elif choice == "3":
            # Custom settings
            print("\n⚙️ Custom settings")
            
            # Currency selection
            currency = input("Currency (krw/usd/eur, default: krw): ").strip().lower() or "krw"
            
            # Days selection
            try:
                days = int(input("Number of days (1-365, default: 30): ").strip() or "30")
                days = max(1, min(365, days))
            except ValueError:
                days = 30
                print(f"Invalid input. Using default {days} days.")
            
            print(f"\n🔄 Creating {currency.upper()} {days}-day chart...")
            price_data = chart_generator.get_bitcoin_price_history(days, currency)
            if price_data:
                chart_generator.create_price_chart(price_data, currency, days)
            else:
                print("❌ Unable to retrieve data.")
        
        else:
            print("❌ Invalid selection. Creating default chart.")
            price_data = chart_generator.get_bitcoin_price_history(30, "krw")
            if price_data:
                chart_generator.create_price_chart(price_data, "krw", 30)
        
        print("\n✅ Program completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Program interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error occurred during program execution: {e}")
    finally:
        print("\n👋 Exiting program.")

if __name__ == "__main__":
    main()
