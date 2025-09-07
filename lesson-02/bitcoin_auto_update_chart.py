#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bitcoin Price Auto-Update Chart
Automatically updates price every hour and refreshes the graph in real-time.
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import numpy as np
import os
import csv

class BitcoinAutoUpdateChart:
    def __init__(self):
        """Initialize Bitcoin auto-update chart system"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # User-Agent setup for API requests
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Data storage
        self.price_history = []  # List of (datetime, price) tuples
        self.currency = "krw"
        self.update_interval = 3600  # 1 hour in seconds
        self.is_running = False
        self.data_lock = threading.Lock()
        
        # Performance optimization settings
        self.max_data_points = 24  # Keep only 24 data points (24 hours)
        
        # Chart components
        self.fig = None
        self.ax = None
        self.ani = None
        
        # Setup matplotlib
        self.setup_matplotlib()
        
        # Data file setup
        self.data_file = f"bitcoin_auto_data_{datetime.now().strftime('%Y%m%d')}.csv"
        self.setup_data_file()
        
        # Load initial data
        self.load_initial_data()
    
    def setup_matplotlib(self):
        """Setup matplotlib for stable rendering"""
        try:
            # Font setup - use system default fonts only
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.size'] = 10
            
            # Disable tooltips to prevent character corruption
            plt.rcParams['toolbar'] = 'None'
            plt.rcParams['figure.autolayout'] = True
            
            print("Matplotlib setup completed successfully")
            
        except Exception as e:
            print(f"Matplotlib setup error: {e}")
    
    def setup_data_file(self):
        """Initialize CSV data file"""
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
        """Load initial price data (last 24 hours)"""
        try:
            print("Loading initial data...")
            initial_data = self.get_bitcoin_price_history(1, self.currency)
            if initial_data:
                with self.data_lock:
                    self.price_history = initial_data
                    # Save initial data
                    for timestamp, price in initial_data:
                        self.save_price_data(timestamp, price)
                print(f"Initial {len(initial_data)} data points loaded")
            else:
                # Start with current price if no historical data
                current_price = self.get_current_bitcoin_price(self.currency)
                if current_price:
                    now = datetime.now()
                    with self.data_lock:
                        self.price_history = [(now, current_price)]
                        self.save_price_data(now, current_price)
                    print("Initialized with current price")
        except Exception as e:
            print(f"Initial data load error: {e}")
    
    def get_bitcoin_price_history(self, days: int = 1, currency: str = "krw") -> Optional[List[Tuple[datetime, float]]]:
        """Get Bitcoin historical price data from CoinGecko API"""
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
        """Get current Bitcoin price from CoinGecko API"""
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
        """Update price data with current price"""
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
                        
                        # Keep only last 24 data points for performance
                        if len(self.price_history) > self.max_data_points:
                            self.price_history = self.price_history[-self.max_data_points:]
                        
                        print(f"[{now.strftime('%H:%M:%S')}] Price updated: {self.format_price(current_price)}")
                        return True  # Data was updated
                    else:
                        print(f"[{now.strftime('%H:%M:%S')}] Update skipped (recent data exists)")
                        return False  # No update needed
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Price retrieval failed")
                return False
                
        except Exception as e:
            print(f"Data update error: {e}")
            return False
    
    def format_price(self, price: float) -> str:
        """Format price in user-friendly format"""
        if self.currency.lower() == "krw":
            if price >= 1000000:
                return f"{price/1000000:.1f}M KRW"
            elif price >= 1000:
                return f"{price/1000:.1f}K KRW"
            else:
                return f"{price:,.0f} KRW"
        elif self.currency.lower() == "usd":
            if price >= 1000000:
                return f"${price/1000000:.1f}M"
            elif price >= 1000:
                return f"${price/1000:.1f}K"
            else:
                return f"${price:,.2f}"
        else:
            return f"{price:,.2f} {self.currency.upper()}"
    
    def data_collection_worker(self):
        """Background worker for automatic data collection"""
        while self.is_running:
            try:
                self.update_price_data()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Data collection worker error: {e}")
                time.sleep(60)  # Retry after 1 minute on error
    
    def start_data_collection(self):
        """Start automatic data collection"""
        if not self.is_running:
            self.is_running = True
            self.collection_thread = threading.Thread(target=self.data_collection_worker, daemon=True)
            self.collection_thread.start()
            print("Automatic data collection started (every 1 hour)")
    
    def stop_data_collection(self):
        """Stop automatic data collection"""
        self.is_running = False
        print("Automatic data collection stopped")
    
    def create_auto_update_chart(self):
        """Create auto-updating chart with real-time refresh"""
        print("Creating chart...")
        
        # Initialize chart with smaller size for better performance
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.fig.suptitle('Bitcoin Price Chart', 
                         fontsize=14, fontweight='bold')
        
        # Simple animation function
        def animate(frame):
            try:
                with self.data_lock:
                    if self.price_history:
                        # Get recent data (last 24 points max)
                        recent_data = self.price_history[-24:] if len(self.price_history) > 24 else self.price_history
                        dates = [item[0] for item in recent_data]
                        prices = [item[1] for item in recent_data]
                        
                        # Clear and redraw
                        self.ax.clear()
                        
                        # Simple line plot
                        self.ax.plot(dates, prices, 'o-', color='#f7931a', linewidth=2, markersize=4)
                        
                        # Current price line
                        if prices:
                            current_price = prices[-1]
                            self.ax.axhline(y=current_price, color='red', linestyle='--', alpha=0.7)
                        
                        # Basic styling
                        self.ax.set_title(f'Bitcoin Price - {self.currency.upper()}')
                        self.ax.set_xlabel('Time')
                        self.ax.set_ylabel(f'Price ({self.currency.upper()})')
                        self.ax.grid(True, alpha=0.3)
                        
                        # Simple time formatting
                        if len(dates) > 0:
                            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
                        
                        # Add current price info
                        if prices:
                            self.ax.text(0.02, 0.98, f'Current: {self.format_price(prices[-1])}', 
                                       transform=self.ax.transAxes, fontsize=12, 
                                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue'))
                        
                        self.fig.tight_layout()
                        
            except Exception as e:
                print(f"Chart update error: {e}")
        
        # Start animation with longer interval
        self.ani = FuncAnimation(self.fig, animate, interval=15000, blit=False, 
                                cache_frame_data=False, save_count=20)
        
        print("Chart created. Showing window...")
        plt.show()
        
        return self.fig
    
    def create_manual_chart(self):
        """Create manual chart without animation"""
        try:
            with self.data_lock:
                if not self.price_history:
                    print("No data to display.")
                    return None
                
                # Get recent data
                recent_data = self.price_history[-24:] if len(self.price_history) > 24 else self.price_history
                dates = [item[0] for item in recent_data]
                prices = [item[1] for item in recent_data]
                
                # Create chart
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # Simple line plot
                ax.plot(dates, prices, 'o-', color='#f7931a', linewidth=2, markersize=4)
                
                # Current price line
                if prices:
                    current_price = prices[-1]
                    ax.axhline(y=current_price, color='red', linestyle='--', alpha=0.7)
                
                # Basic styling
                ax.set_title(f'Bitcoin Price - {self.currency.upper()}')
                ax.set_xlabel('Time')
                ax.set_ylabel(f'Price ({self.currency.upper()})')
                ax.grid(True, alpha=0.3)
                
                # Simple time formatting
                if len(dates) > 0:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Add current price info
                if prices:
                    ax.text(0.02, 0.98, f'Current: {self.format_price(prices[-1])}', 
                           transform=ax.transAxes, fontsize=12, 
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue'))
                
                plt.tight_layout()
                plt.show()
                
                return fig
                
        except Exception as e:
            print(f"Manual chart creation error: {e}")
            return None

def main():
    """Main function"""
    print("=" * 80)
    print("Bitcoin Price Auto-Update Chart Program")
    print("=" * 80)
    print("Features:")
    print("- Automatic price updates every 1 hour")
    print("- Real-time chart refresh every 15 seconds")
    print("- Data saved to CSV file")
    print("- 24-hour price history")
    print("=" * 80)
    
    # Initialize auto-update chart
    chart = BitcoinAutoUpdateChart()
    
    try:
        print("\nSelect mode:")
        print("1. Auto-update chart (recommended)")
        print("2. Manual refresh chart (if auto-update has issues)")
        
        choice = input("\nSelect (1-2, default: 1): ").strip() or "1"
        
        if choice == "1":
            print("\nStarting auto-update chart...")
            print("💡 Chart will auto-refresh every 15 seconds")
            print("💡 Price data will be collected automatically every hour")
            print("💡 Program will exit when chart window is closed")
            print("💡 Simplified for maximum stability")
            
            # Start automatic data collection
            chart.start_data_collection()
            
            # Create and show auto-updating chart
            chart.create_auto_update_chart()
            
        elif choice == "2":
            print("\nStarting manual refresh chart...")
            print("💡 Press Enter to refresh chart")
            print("💡 Price data will be collected automatically every hour")
            print("💡 Type 'quit' to exit")
            
            # Start automatic data collection
            chart.start_data_collection()
            
            # Manual refresh loop
            while True:
                try:
                    user_input = input("\nPress Enter to refresh chart (or 'quit' to exit): ").strip()
                    if user_input.lower() == 'quit':
                        break
                    
                    # Create manual chart
                    chart.create_manual_chart()
                    
                except KeyboardInterrupt:
                    break
        
        print("\n✅ Chart program completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Program interrupted by user")
        chart.stop_data_collection()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        chart.stop_data_collection()
    finally:
        print("\n👋 Exiting program")

if __name__ == "__main__":
    main()
