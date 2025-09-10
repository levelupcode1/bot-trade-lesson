#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time Auto-updating Bitcoin Price Chart
Automatically updates price every hour and the graph changes automatically.
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import matplotlib
# Backend setup - for stable rendering across platforms
matplotlib.use('Qt5Agg')  # Use Qt5 backend instead of Tkinter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation
import numpy as np
import os
import csv

class LiveBitcoinPriceChart:
    def __init__(self):
        """Initialize real-time Bitcoin price chart generator"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # User-Agent setup
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Data storage
        self.price_history = []  # List of (time, price) tuples
        self.currency = "krw"
        self.update_interval = 3600  # 1 hour (in seconds)
        self.is_running = False
        self.data_lock = threading.Lock()
        
        # matplotlib font setup
        self.setup_font()
        
        # Disable matplotlib tooltips globally
        plt.rcParams['toolbar'] = 'None'
        plt.rcParams['figure.autolayout'] = True
        
        # Chart style setup - use default style to prevent corruption
        try:
            plt.style.use('default')  # Use default style for stability
        except:
            pass  # Ignore if style setup fails
        
        # Data file setup
        self.data_file = f"bitcoin_live_data_{datetime.now().strftime('%Y%m%d')}.csv"
        self.setup_data_file()
        
        # Load initial data
        self.load_initial_data()
        
    def setup_data_file(self):
        """Initialize data storage file"""
        try:
            if not os.path.exists(self.data_file):
                with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'datetime', 'price', 'currency'])
                print(f"Data file created: {self.data_file}")
        except Exception as e:
            print(f"Data file creation error: {e}")
    
    def save_price_data(self, timestamp: datetime, price: float):
        """Save price data to CSV file"""
        try:
            with open(self.data_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp.timestamp(),
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    price,
                    self.currency
                ])
        except Exception as e:
            print(f"Data save error: {e}")
    
    def load_initial_data(self):
        """Load initial data (last 24 hours)"""
        try:
            print("Loading initial data...")
            initial_data = self.get_bitcoin_price_history(1, self.currency)  # 1 day
            if initial_data:
                with self.data_lock:
                    self.price_history = initial_data
                    # Save data
                    for timestamp, price in initial_data:
                        self.save_price_data(timestamp, price)
                print(f"Initial {len(initial_data)} data points loaded")
            else:
                # If no initial data, start with current price
                current_price = self.get_current_bitcoin_price(self.currency)
                if current_price:
                    now = datetime.now()
                    with self.data_lock:
                        self.price_history = [(now, current_price)]
                        self.save_price_data(now, current_price)
                    print("Initialized with current price")
        except Exception as e:
            print(f"Initial data load error: {e}")
    
    def setup_font(self):
        """Font setup optimized for cross-platform environment"""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                font_candidates = ['AppleGothic', 'Malgun Gothic', 'NanumGothic', 'Arial Unicode MS', 'Arial']
            elif system == "Windows":
                font_candidates = ['Malgun Gothic', 'NanumGothic', 'Arial', 'Calibri', 'Segoe UI']
            else:  # Linux
                font_candidates = ['NanumGothic', 'DejaVu Sans', 'Liberation Sans', 'Arial']
            
            # Find available fonts
            available_fonts = [f.name for f in font_manager.fontManager.ttflist]
            
            for font in font_candidates:
                if font in available_fonts:
                    plt.rcParams['font.family'] = font
                    print(f"Font set successfully: {font}")
                    break
            else:
                # Use default font if none found
                plt.rcParams['font.family'] = 'DejaVu Sans'
                print("Using default font: DejaVu Sans")
            
            # Prevent minus sign corruption
            plt.rcParams['axes.unicode_minus'] = False
            
            # Font size settings
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['axes.labelsize'] = 12
            plt.rcParams['xtick.labelsize'] = 10
            plt.rcParams['ytick.labelsize'] = 10
            plt.rcParams['legend.fontsize'] = 10
            
        except Exception as e:
            print(f"Font setup error: {e}")
            # Use default settings on error
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
    
    def get_bitcoin_price_history(self, days: int = 1, currency: str = "krw") -> Optional[List[Tuple[datetime, float]]]:
        """Retrieve Bitcoin historical price data."""
        try:
            endpoint = "/coins/bitcoin/market_chart"
            params = {
                "vs_currency": currency,
                "days": days,
                "interval": "hourly"
            }
            
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "prices" in data and data["prices"]:
                    price_data = []
                    for timestamp_ms, price in data["prices"]:
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        price_data.append((dt, price))
                    
                    return price_data
            return None
                
        except Exception as e:
            print(f"Price data retrieval error: {e}")
            return None
    
    def get_current_bitcoin_price(self, currency: str = "krw") -> Optional[float]:
        """Retrieve current Bitcoin price."""
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
    
    def update_price_data(self):
        """Update price data."""
        try:
            current_price = self.get_current_bitcoin_price(self.currency)
            if current_price:
                now = datetime.now()
                
                with self.data_lock:
                    # Prevent duplicate data (within 1 minute)
                    if (not self.price_history or 
                        (now - self.price_history[-1][0]).total_seconds() > 60):
                        
                        self.price_history.append((now, current_price))
                        self.save_price_data(now, current_price)
                        
                        # Keep only last 24 hours of data
                        cutoff_time = now - timedelta(hours=24)
                        self.price_history = [
                            (t, p) for t, p in self.price_history 
                            if t > cutoff_time
                        ]
                        
                        print(f"[{now.strftime('%H:%M:%S')}] Price update: {self.format_price(current_price, self.currency)}")
                    else:
                        print(f"[{now.strftime('%H:%M:%S')}] Update skipped (recent data exists)")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Price retrieval failed")
                
        except Exception as e:
            print(f"Data update error: {e}")
    
    def format_price(self, price: float, currency: str = "krw") -> str:
        """Format price in user-friendly format."""
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
    
    def data_collection_worker(self):
        """Background data collection worker"""
        while self.is_running:
            try:
                self.update_price_data()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Data collection worker error: {e}")
                time.sleep(60)  # Retry after 1 minute on error
    
    def start_data_collection(self):
        """Start data collection."""
        if not self.is_running:
            self.is_running = True
            self.collection_thread = threading.Thread(target=self.data_collection_worker, daemon=True)
            self.collection_thread.start()
            print("Automatic data collection has started.")
    
    def stop_data_collection(self):
        """Stop data collection."""
        self.is_running = False
        print("Automatic data collection has stopped.")
    
    def create_live_chart(self):
        """Create real-time updating chart."""
        # Initialize chart
        self.fig, self.ax = plt.subplots(figsize=(16, 10))
        current_font = plt.rcParams['font.family']
        self.fig.suptitle('Real-time Bitcoin Price Chart (Auto-update every hour)', 
                         fontsize=16, fontweight='bold', fontfamily=current_font)
        
        # Disable matplotlib tooltips to prevent character corruption
        self.fig.canvas.mpl_connect('motion_notify_event', lambda event: None)
        
        # Additional tooltip prevention
        plt.rcParams['toolbar'] = 'None'  # Disable toolbar
        plt.rcParams['figure.autolayout'] = True  # Auto layout
        
        # Animation function
        def animate(frame):
            try:
                with self.data_lock:
                    if self.price_history:
                        # Separate data
                        dates = [item[0] for item in self.price_history]
                        prices = [item[1] for item in self.price_history]
                        
                        # Clear chart
                        self.ax.clear()
                        
                        # Draw line graph - simplified to prevent tooltip issues
                        self.ax.plot(dates, prices, linewidth=2.5, color='#f7931a', 
                                   marker='o', markersize=3, markerfacecolor='white', 
                                   markeredgecolor='#f7931a', markeredgewidth=1)
                        
                        # Highlight current price
                        if prices:
                            current_price = prices[-1]
                            self.ax.axhline(y=current_price, color='red', linestyle='--', 
                                          alpha=0.7, linewidth=1.5, 
                                          label=f'Current Price: {self.format_price(current_price, self.currency)}')
                        
                        # Show highest/lowest prices
                        if len(prices) > 1:
                            max_price = max(prices)
                            min_price = min(prices)
                            max_date = dates[prices.index(max_price)]
                            min_date = dates[prices.index(min_price)]
                            
                            # Highest price point
                            self.ax.scatter(max_date, max_price, color='red', s=100, zorder=5,
                                          label=f'Highest: {self.format_price(max_price, self.currency)}')
                            
                            # Lowest price point
                            self.ax.scatter(min_date, min_price, color='blue', s=100, zorder=5,
                                          label=f'Lowest: {self.format_price(min_price, self.currency)}')
                        
                        # Chart styling - use current font family
                        current_font = plt.rcParams['font.family']
                        self.ax.set_title(f'Bitcoin Real-time Price Movement (Currency: {self.currency.upper()})', 
                                        fontsize=14, fontweight='bold', pad=20, fontfamily=current_font)
                        
                        # x-axis setup
                        self.ax.set_xlabel('Time', fontsize=12, fontweight='bold', fontfamily=current_font)
                        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                        self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontfamily=current_font)
                        
                        # y-axis setup
                        self.ax.set_ylabel(f'Price ({self.currency.upper()})', fontsize=12, fontweight='bold', fontfamily=current_font)
                        plt.setp(self.ax.yaxis.get_majorticklabels(), fontfamily=current_font)
                        
                        # Grid setup
                        self.ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
                        self.ax.set_axisbelow(True)
                        
                        # Legend setup
                        self.ax.legend(loc='upper left', fontsize=10, framealpha=0.9, prop={'family': current_font})
                        
                        # Add statistics info - prevent text corruption
                        if len(prices) > 1:
                            price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
                            change_symbol = "▲" if price_change >= 0 else "▼"  # Use unicode characters instead of emojis
                            
                            # Simple text to prevent corruption
                            stats_text = f"""Real-time Statistics
Start: {self.format_price(prices[0], self.currency)}
Current: {self.format_price(prices[-1], self.currency)}
Change: {change_symbol} {price_change:+.2f}%
Points: {len(prices)}
Update: {datetime.now().strftime('%H:%M:%S')}"""
                            
                            self.ax.text(0.98, 0.02, stats_text, transform=self.ax.transAxes,
                                       fontsize=9, verticalalignment='bottom', 
                                       horizontalalignment='right',
                                       bbox=dict(boxstyle='round,pad=0.3', 
                                               facecolor='lightblue', alpha=0.8),
                                       fontfamily=current_font)
                        
                        # Background color setup
                        self.ax.set_facecolor('#f8f9fa')
                        self.fig.patch.set_facecolor('white')
                        
                        # Layout adjustment
                        self.fig.tight_layout()
                        
            except Exception as e:
                print(f"Chart update error: {e}")
        
        # Start animation
        self.ani = FuncAnimation(self.fig, animate, interval=5000, blit=False)  # Update every 5 seconds
        
        # Show chart
        plt.show()
        
        return self.fig
    
    def create_manual_chart(self):
        """Create chart manually."""
        with self.data_lock:
            if not self.price_history:
                print("No data to display.")
                return None
            
            # Separate data
            dates = [item[0] for item in self.price_history]
            prices = [item[1] for item in self.price_history]
            
            # Create chart
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Disable tooltips for manual chart
            fig.canvas.mpl_connect('motion_notify_event', lambda event: None)
            
            # Draw line graph - simplified to prevent tooltip issues
            ax.plot(dates, prices, linewidth=2.5, color='#f7931a', 
                   marker='o', markersize=3, markerfacecolor='white', 
                   markeredgecolor='#f7931a', markeredgewidth=1)
            
            # Chart styling - use current font family
            current_font = plt.rcParams['font.family']
            ax.set_title(f'Bitcoin Price Movement (Manual)', 
                        fontsize=16, fontweight='bold', pad=20, fontfamily=current_font)
            ax.set_xlabel('Time', fontsize=12, fontweight='bold', fontfamily=current_font)
            ax.set_ylabel(f'Price ({self.currency.upper()})', fontsize=12, fontweight='bold', fontfamily=current_font)
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontfamily=current_font)
            plt.setp(ax.yaxis.get_majorticklabels(), fontfamily=current_font)
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
            return fig

def main():
    """Main function"""
    print("=" * 80)
    print("Real-time Auto-updating Bitcoin Price Chart Program")
    print("=" * 80)
    
    # Initialize real-time chart generator
    live_chart = LiveBitcoinPriceChart()
    
    try:
        print("\n📊 Select chart option:")
        print("1. Real-time auto-update chart (auto-refresh every hour)")
        print("2. Manual chart creation (with current data)")
        print("3. Start data collection only (background)")
        print("4. Change settings")
        
        choice = input("\nSelect (1-4, default: 1): ").strip() or "1"
        
        if choice == "1":
            # Real-time auto-update chart
            print("\n🔄 Starting real-time auto-update chart...")
            print("💡 Chart will auto-refresh every 5 seconds.")
            print("💡 Price data will be collected automatically every hour.")
            print("💡 Program will exit when chart is closed.")
            
            # Start data collection
            live_chart.start_data_collection()
            
            # Create real-time chart
            live_chart.create_live_chart()
            
        elif choice == "2":
            # Manual chart creation
            print("\n🔄 Creating manual chart...")
            live_chart.create_manual_chart()
            
        elif choice == "3":
            # Start data collection only
            print("\n🔄 Starting background data collection...")
            print("💡 Data will be collected automatically every hour.")
            print("💡 Press Ctrl+C to exit the program.")
            
            live_chart.start_data_collection()
            
            try:
                while True:
                    time.sleep(60)  # Print status every minute
                    with live_chart.data_lock:
                        if live_chart.price_history:
                            latest = live_chart.price_history[-1]
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                                  f"Latest data: {latest[0].strftime('%H:%M:%S')} - "
                                  f"{live_chart.format_price(latest[1], live_chart.currency)}")
            except KeyboardInterrupt:
                print("\n⏹️ Interrupted by user.")
                live_chart.stop_data_collection()
                
        elif choice == "4":
            # Change settings
            print("\n⚙️ Change Settings")
            
            # Change currency
            new_currency = input(f"Currency (current: {live_chart.currency}, krw/usd/eur): ").strip().lower()
            if new_currency in ['krw', 'usd', 'eur']:
                live_chart.currency = new_currency
                print(f"Currency changed to {new_currency.upper()}.")
            
            # Change update interval
            try:
                new_interval = int(input(f"Update interval (current: {live_chart.update_interval//60} minutes, in minutes): ").strip())
                if new_interval > 0:
                    live_chart.update_interval = new_interval * 60
                    print(f"Update interval changed to {new_interval} minutes.")
            except ValueError:
                print("Invalid input. Keeping existing settings.")
        
        else:
            print("❌ Invalid selection. Running default option.")
            live_chart.start_data_collection()
            live_chart.create_live_chart()
        
        print("\n✅ Program completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Program interrupted by user.")
        live_chart.stop_data_collection()
    except Exception as e:
        print(f"\n❌ Error occurred during program execution: {e}")
        live_chart.stop_data_collection()
    finally:
        print("\n👋 Exiting program.")

if __name__ == "__main__":
    main()
