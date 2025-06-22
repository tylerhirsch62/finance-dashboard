#!/usr/bin/env python3
"""
Azure Deployment Helper Script
This script prepares the finance dashboard for Azure Web App deployment.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_requirements():
    """Check if required packages are installed"""
    print("🔍 Checking requirements...")
    try:
        import flask
        import pandas
        import plotly
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def download_sample_data():
    """Download sample data for deployment"""
    print("📊 Downloading sample data...")
    
    # Try pandas_datareader first
    if run_command("python download_pandas_datareader.py", "Downloading data with pandas_datareader"):
        return True
    
    # Fallback to yfinance
    if run_command("python download_data.py", "Downloading data with yfinance"):
        return True
    
    # Create sample data if both fail
    print("⚠️  Both download methods failed, creating sample data...")
    return create_sample_data()

def create_sample_data():
    """Create sample data for testing"""
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Create sample data directory
        data_dir = 'finance_dashboard_data'
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate sample data for each ticker
        tickers = ['SPY', 'AAPL', 'NVDA', 'TSLA', 'MSFT']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 30 days of data
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        date_range = date_range[date_range.weekday < 5]  # Weekdays only
        
        for ticker in tickers:
            print(f"Creating sample data for {ticker}...")
            
            # Generate realistic sample data
            np.random.seed(hash(ticker) % 1000)
            base_price = {'SPY': 400, 'AAPL': 150, 'NVDA': 300, 'TSLA': 200, 'MSFT': 250}.get(ticker, 100)
            
            prices = [base_price]
            for i in range(1, len(date_range)):
                change = np.random.normal(0, 0.02)
                new_price = prices[-1] * (1 + change)
                prices.append(max(new_price, 1))
            
            df = pd.DataFrame({
                'Date': date_range,
                'Open': prices,
                'High': [p * 1.01 for p in prices],
                'Low': [p * 0.99 for p in prices],
                'Close': prices,
                'Adj Close': prices,
                'Volume': np.random.randint(1000000, 10000000, len(date_range))
            })
            
            df.to_csv(os.path.join(data_dir, f'{ticker}.csv'), index=False)
        
        print("✅ Sample data created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def verify_deployment_files():
    """Verify all required files exist"""
    print("🔍 Verifying deployment files...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'startup.txt',
        'web.config',
        'templates/dashboard.html',
        'finance_dashboard_data'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def main():
    """Main deployment preparation function"""
    print("🚀 Finance Dashboard - Azure Deployment Preparation")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Download/create data
    if not download_sample_data():
        print("❌ Failed to prepare data")
        sys.exit(1)
    
    # Verify files
    if not verify_deployment_files():
        print("❌ Missing required files")
        sys.exit(1)
    
    print("\n🎉 Deployment preparation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Push your code to GitHub")
    print("2. Create an Azure Web App")
    print("3. Connect your GitHub repository")
    print("4. Set startup command: python app.py")
    print("5. Deploy!")
    
    print("\n📚 For detailed instructions, see README.md")

if __name__ == "__main__":
    main() 