#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time Auto-updating Ripple (XRP) Price Chart
Automatically updates price every 5 minutes and the graph changes automatically.
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import matplotlib
# Backend setup - for stable rendering across platforms
try:
    matplotlib.use('TkAgg')  # Use TkAgg backend for better compatibility
except ImportError:
    try:
        matplotlib.use('Qt5Agg')  # Fallback to Qt5Agg
    except ImportError:
        matplotlib.use('Agg')  # Fallback to Agg for headless systems
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation
import numpy as np
import os
import csv

class LiveRipplePriceChart:
    def __init__(self):
        """Initialize real-time Ripple (XRP) price chart generator"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # User-Agent setup
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Data storage
        self.price_history = []  # List of (time, price) tuples
        self.currency = "krw"
        self.update_interval = 300  # 5 minutes (in seconds)
        self.is_running = False
        self.data_lock = threading.Lock()
        self.manual_update_mode = False
        
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
        self.data_file = f"ripple_live_data_{datetime.now().strftime('%Y%m%d')}.csv"
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
        """Load initial data with 5-minute intervals"""
        try:
            print("Loading initial data...")
            # Get minutely data for last 12 hours (최대 1일까지만 가능)
            initial_data = self.get_ripple_price_history(1, self.currency)  # minutely data
            
            if initial_data:
                with self.data_lock:
                    # Filter to 5-minute intervals and last 12 hours
                    now = datetime.now()
                    cutoff_time = now - timedelta(hours=12)
                    
                    # 5분 간격으로 필터링 (매 5분마다 하나씩만)
                    filtered_data = []
                    last_minute = None
                    
                    for timestamp, price in initial_data:
                        if timestamp > cutoff_time:
                            minute = timestamp.minute
                            # 5분 단위로만 선택 (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)
                            if minute % 5 == 0 and minute != last_minute:
                                filtered_data.append((timestamp, price))
                                last_minute = minute
                    
                    self.price_history = filtered_data
                    # Save data
                    for timestamp, price in filtered_data:
                        self.save_price_data(timestamp, price)
                    
                print(f"Initial {len(filtered_data)} data points loaded (5-minute intervals, last 12 hours)")
            else:
                # Fallback: start with current price
                current_price = self.get_current_ripple_price(self.currency)
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
    
    def get_ripple_price_history(self, days: int = 1, currency: str = "krw") -> Optional[List[Tuple[datetime, float]]]:
        """Retrieve Ripple (XRP) historical price data."""
        try:
            endpoint = "/coins/ripple/market_chart"
            # 'minutely' interval available only for 1 day or less
            # 'hourly' for 1-90 days, 'daily' for 90+ days
            if days <= 1:
                interval = "minutely"  # 1-minute interval (최근 1일치만 가능)
            elif days <= 90:
                interval = "hourly"
            else:
                interval = "daily"
            
            params = {
                "vs_currency": currency,
                "days": days,
                "interval": interval
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
    
    def get_current_ripple_price(self, currency: str = "krw") -> Optional[float]:
        """Retrieve current Ripple (XRP) price."""
        try:
            endpoint = "/simple/price"
            params = {
                "ids": "ripple",
                "vs_currencies": currency
            }
            
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "ripple" in data and currency in data["ripple"]:
                    return data["ripple"][currency]
            return None
            
        except Exception as e:
            print(f"Current price retrieval error: {e}")
            return None
    
    def update_price_data(self):
        """Update price data."""
        try:
            current_price = self.get_current_ripple_price(self.currency)
            if current_price:
                now = datetime.now()
                
                with self.data_lock:
                    # Prevent duplicate data (within 5 minutes)
                    if (not self.price_history or 
                        (now - self.price_history[-1][0]).total_seconds() > 300):
                        
                        self.price_history.append((now, current_price))
                        self.save_price_data(now, current_price)
                        
                        # Keep only last 12 hours of data (144 data points for 5-minute updates)
                        cutoff_time = now - timedelta(hours=12)
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
        self.fig.suptitle('Real-time Ripple (XRP) Price Chart (Auto-update every 5 minutes)', 
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
                        
                        # Draw line graph - use blue color for Ripple
                        self.ax.plot(dates, prices, linewidth=2.5, color='#0066cc', 
                                   marker='o', markersize=3, markerfacecolor='white', 
                                   markeredgecolor='#0066cc', markeredgewidth=1)
                        
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
                        self.ax.set_title(f'Ripple (XRP) Real-time Price Movement (Currency: {self.currency.upper()})', 
                                        fontsize=14, fontweight='bold', pad=20, fontfamily=current_font)
                        
                        # x-axis setup
                        self.ax.set_xlabel('Time', fontsize=12, fontweight='bold', fontfamily=current_font)
                        
                        # Safe locator setup to prevent too many ticks
                        if len(dates) > 0:
                            time_span = (dates[-1] - dates[0]).total_seconds() / 3600  # hours
                            
                            # Calculate safe interval to keep ticks under 1000
                            total_hours = time_span
                            max_ticks = 6  # Further reduced maximum number of ticks to display
                            
                            # Very aggressive interval calculation for 5-minute updates
                            if time_span > 168:  # More than 1 week
                                interval = max(168, int(total_hours / max_ticks))  # 168 hours or more
                            elif time_span > 72:  # More than 3 days
                                interval = max(72, int(total_hours / max_ticks))  # 72 hours or more
                            elif time_span > 24:  # More than 1 day
                                interval = max(24, int(total_hours / max_ticks))  # 24 hours or more
                            elif time_span > 12:  # More than 12 hours
                                interval = max(12, int(total_hours / max_ticks))  # 12 hours or more
                            elif time_span > 6:  # More than 6 hours
                                interval = max(6, int(total_hours / max_ticks))  # 6 hours or more
                            elif time_span > 2:  # More than 2 hours
                                interval = max(2, int(total_hours / max_ticks))  # 2 hours or more
                            else:  # Less than 2 hours
                                interval = max(1, int(total_hours / max_ticks))  # 1 hour or more
                            
                            # Additional safety check - ensure interval is at least 1
                            if interval < 1:
                                interval = 1
                            
                            # Use very aggressive locator for high-frequency data
                            if len(dates) > 200:  # If we have more than 200 data points
                                # Use day locator for very long periods
                                if time_span > 24:
                                    day_interval = max(1, int(time_span / 24 / max_ticks))
                                    self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=day_interval))
                                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                                else:
                                    self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
                                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                            else:
                                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
                                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                        else:
                            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                        
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
        
        # Start animation with error handling
        try:
            self.ani = FuncAnimation(self.fig, animate, interval=300000, blit=False, 
                                   cache_frame_data=False, save_count=1000)  # Update every 5 minutes
            print("Animation started successfully.")
        except Exception as e:
            print(f"Animation initialization error: {e}")
            print("Falling back to manual update mode...")
            # Fallback to manual updates
            self.manual_update_mode = True
            self.animate_manually()
        
        # Show chart
        try:
            plt.show()
        except Exception as e:
            print(f"Chart display error: {e}")
            print("Please check your display settings.")
        
        return self.fig
    
    def animate_manually(self):
        """Manual animation fallback when automatic animation fails"""
        print("Starting manual update mode...")
        print("Press Ctrl+C to stop the program.")
        
        try:
            while True:
                # Update data
                self.update_price_data()
                
                # Redraw chart
                with self.data_lock:
                    if self.price_history:
                        dates = [item[0] for item in self.price_history]
                        prices = [item[1] for item in self.price_history]
                        
                        # Clear and redraw
                        self.ax.clear()
                        self.ax.plot(dates, prices, linewidth=2.5, color='#0066cc', 
                                   marker='o', markersize=3, markerfacecolor='white', 
                                   markeredgecolor='#0066cc', markeredgewidth=1)
                        
                        # Basic styling with safe locator
                        self.ax.set_title(f'Ripple (XRP) Real-time Price (Manual Update)', 
                                        fontsize=14, fontweight='bold')
                        self.ax.set_xlabel('Time', fontsize=12)
                        self.ax.set_ylabel(f'Price ({self.currency.upper()})', fontsize=12)
                        
                        # Safe locator setup for manual update mode
                        if len(dates) > 0:
                            time_span = (dates[-1] - dates[0]).total_seconds() / 3600  # hours
                            
                            # Calculate safe interval to keep ticks under 1000
                            total_hours = time_span
                            max_ticks = 6  # Further reduced maximum number of ticks to display
                            
                            # Very aggressive interval calculation for 5-minute updates
                            if time_span > 168:  # More than 1 week
                                interval = max(168, int(total_hours / max_ticks))  # 168 hours or more
                            elif time_span > 72:  # More than 3 days
                                interval = max(72, int(total_hours / max_ticks))  # 72 hours or more
                            elif time_span > 24:  # More than 1 day
                                interval = max(24, int(total_hours / max_ticks))  # 24 hours or more
                            elif time_span > 12:  # More than 12 hours
                                interval = max(12, int(total_hours / max_ticks))  # 12 hours or more
                            elif time_span > 6:  # More than 6 hours
                                interval = max(6, int(total_hours / max_ticks))  # 6 hours or more
                            elif time_span > 2:  # More than 2 hours
                                interval = max(2, int(total_hours / max_ticks))  # 2 hours or more
                            else:  # Less than 2 hours
                                interval = max(1, int(total_hours / max_ticks))  # 1 hour or more
                            
                            # Additional safety check - ensure interval is at least 1
                            if interval < 1:
                                interval = 1
                            
                            # Use very aggressive locator for high-frequency data
                            if len(dates) > 200:  # If we have more than 200 data points
                                # Use day locator for very long periods
                                if time_span > 24:
                                    day_interval = max(1, int(time_span / 24 / max_ticks))
                                    self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=day_interval))
                                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                                else:
                                    self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
                                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                            else:
                                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
                                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                        else:
                            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                        self.ax.grid(True, alpha=0.3)
                        
                        # Refresh display
                        self.fig.canvas.draw()
                        self.fig.canvas.flush_events()
                
                time.sleep(300)  # Update every 5 minutes in manual mode
                
        except KeyboardInterrupt:
            print("\nManual update mode stopped by user.")
        except Exception as e:
            print(f"Manual update error: {e}")
    
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
            
            # Draw line graph - use blue color for Ripple
            ax.plot(dates, prices, linewidth=2.5, color='#0066cc', 
                   marker='o', markersize=3, markerfacecolor='white', 
                   markeredgecolor='#0066cc', markeredgewidth=1)
            
            # Chart styling - use current font family
            current_font = plt.rcParams['font.family']
            ax.set_title(f'Ripple (XRP) Price Movement (Manual)', 
                        fontsize=16, fontweight='bold', pad=20, fontfamily=current_font)
            ax.set_xlabel('Time', fontsize=12, fontweight='bold', fontfamily=current_font)
            ax.set_ylabel(f'Price ({self.currency.upper()})', fontsize=12, fontweight='bold', fontfamily=current_font)
            
            # Safe locator setup for manual chart
            if len(dates) > 0:
                time_span = (dates[-1] - dates[0]).total_seconds() / 3600  # hours
                
                # Calculate safe interval to keep ticks under 1000
                total_hours = time_span
                max_ticks = 6  # Further reduced maximum number of ticks to display
                
                # Very aggressive interval calculation for 5-minute updates
                if time_span > 168:  # More than 1 week
                    interval = max(168, int(total_hours / max_ticks))  # 168 hours or more
                elif time_span > 72:  # More than 3 days
                    interval = max(72, int(total_hours / max_ticks))  # 72 hours or more
                elif time_span > 24:  # More than 1 day
                    interval = max(24, int(total_hours / max_ticks))  # 24 hours or more
                elif time_span > 12:  # More than 12 hours
                    interval = max(12, int(total_hours / max_ticks))  # 12 hours or more
                elif time_span > 6:  # More than 6 hours
                    interval = max(6, int(total_hours / max_ticks))  # 6 hours or more
                elif time_span > 2:  # More than 2 hours
                    interval = max(2, int(total_hours / max_ticks))  # 2 hours or more
                else:  # Less than 2 hours
                    interval = max(1, int(total_hours / max_ticks))  # 1 hour or more
                
                # Additional safety check - ensure interval is at least 1
                if interval < 1:
                    interval = 1
                
                # Use very aggressive locator for high-frequency data
                if len(dates) > 200:  # If we have more than 200 data points
                    # Use day locator for very long periods
                    if time_span > 24:
                        day_interval = max(1, int(time_span / 24 / max_ticks))
                        ax.xaxis.set_major_locator(mdates.DayLocator(interval=day_interval))
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                    else:
                        ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                else:
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            else:
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontfamily=current_font)
            plt.setp(ax.yaxis.get_majorticklabels(), fontfamily=current_font)
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
            return fig

def main():
    """Main function"""
    print("=" * 80)
    print("Real-time Auto-updating Ripple (XRP) Price Chart Program")
    print("=" * 80)
    
    # Initialize real-time chart generator
    live_chart = LiveRipplePriceChart()
    
    try:
        print("\n📊 Select chart option:")
        print("1. Real-time auto-update chart (auto-refresh every 5 minutes)")
        print("2. Manual chart creation (with current data)")
        print("3. Start data collection only (background)")
        print("4. Change settings")
        
        choice = input("\nSelect (1-4, default: 1): ").strip() or "1"
        
        if choice == "1":
            # Real-time auto-update chart
            print("\n🔄 Starting real-time auto-update chart...")
            print("💡 Chart will auto-refresh every 5 minutes.")
            print("💡 Price data will be collected automatically every 5 minutes.")
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
            print("💡 Data will be collected automatically every 5 minutes.")
            print("💡 Press Ctrl+C to exit the program.")
            
            live_chart.start_data_collection()
            
            try:
                while True:
                    time.sleep(300)  # Print status every 5 minutes
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
                new_interval = int(input(f"Update interval (current: {live_chart.update_interval//60} minutes, minimum: 1 minute): ").strip())
                if new_interval >= 1:
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
