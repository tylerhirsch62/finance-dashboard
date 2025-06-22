from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta

app = Flask(__name__)

data_dir = 'finance_dashboard_data'
tickers = ['SPY', 'AAPL', 'NVDA', 'TSLA', 'MSFT']

def load_data():
    data = {}
    for ticker in tickers:
        path = os.path.join(data_dir, f"{ticker}.csv")
        df = pd.read_csv(path)
        # Ensure Date column is properly converted to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        data[ticker] = df
    return data

data = load_data()

@app.route('/')
def dashboard():
    # Get filter parameters from request
    selected_ticker = request.args.get('ticker', 'AAPL')  # Single ticker selection
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_volume = request.args.get('min_volume', type=float)
    max_volume = request.args.get('max_volume', type=float)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    volume_increase_threshold = request.args.get('volume_increase_threshold', type=float)
    
    # Filter data based on parameters
    filtered_data = None
    if selected_ticker in data:
        df = data[selected_ticker].copy()
        
        # Date filtering
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        # Volume filtering - only apply if values are reasonable
        if min_volume is not None and min_volume > 0:
            df = df[df['Volume'] >= min_volume]
        if max_volume is not None and max_volume > 0:
            df = df[df['Volume'] <= max_volume]
        
        # Price filtering - only apply if values are reasonable
        if min_price is not None and min_price > 0:
            df = df[df['Close'] >= min_price]
        if max_price is not None and max_price > 0:
            df = df[df['Close'] <= max_price]
        
        # Volume increase filtering
        if volume_increase_threshold is not None and volume_increase_threshold > 0:
            # Calculate volume change percentage from previous day
            df = df.sort_values('Date')
            df['Volume_Change_Pct'] = df['Volume'].pct_change() * 100
            
            # Filter for days with volume increase above threshold
            df = df[df['Volume_Change_Pct'] >= volume_increase_threshold]
            
            print(f"Volume increase filter: {volume_increase_threshold}% threshold, {len(df)} days found")
        
        if not df.empty:
            filtered_data = df
            print(f"Filtered data has {len(filtered_data)} rows for {selected_ticker}")
        else:
            print(f"No data found after filtering for {selected_ticker}")
    else:
        print(f"Ticker {selected_ticker} not found in data")
    
    # Create price line chart
    price_html = ""
    if filtered_data is not None:
        # Ensure we're using price data
        price_data = filtered_data['Close'].astype(float)
        
        price_trace = go.Scatter(
            x=filtered_data['Date'],
            y=price_data,
            mode='lines',
            name=f'{selected_ticker} Price',
            line=dict(color='#1f77b4', width=3)
        )
        
        price_layout = go.Layout(
            title=f'{selected_ticker} Stock Price Over Time',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Price ($)', tickformat='$.2f'),  # Format as currency
            hovermode='closest',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        price_fig = go.Figure(data=[price_trace], layout=price_layout)
        price_html = price_fig.to_html(
            full_html=False, 
            config={'displayModeBar': False}
        )

    # Create volume line chart
    volume_html = ""
    if filtered_data is not None:
        # Ensure we're using volume data and format it properly
        volume_data = filtered_data['Volume'].astype(float)
        
        volume_trace = go.Scatter(
            x=filtered_data['Date'],
            y=volume_data,
            mode='lines',
            name=f'{selected_ticker} Volume',
            line=dict(color='#1f77b4', width=2),
            fill='tonexty',  # Add fill to make it more distinct
            opacity=0.7
        )
        
        volume_layout = go.Layout(
            title=f'{selected_ticker} Trading Volume Over Time',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Volume (shares)', tickformat=',d'),  # Format large numbers
            hovermode='closest',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        volume_fig = go.Figure(data=[volume_trace], layout=volume_layout)
        volume_html = volume_fig.to_html(
            full_html=False, 
            config={'displayModeBar': False}
        )

    # Get ranges for filter defaults
    all_dates = []
    all_volumes = []
    all_prices = []
    for df in data.values():
        all_dates.extend(df['Date'].tolist())
        all_volumes.extend(df['Volume'].tolist())
        all_prices.extend(df['Close'].tolist())
    
    min_date = min(all_dates).strftime('%Y-%m-%d') if all_dates else ''
    max_date = max(all_dates).strftime('%Y-%m-%d') if all_dates else ''
    min_vol = min(all_volumes) if all_volumes else 0
    max_vol = max(all_volumes) if all_volumes else 0
    min_price_val = min(all_prices) if all_prices else 0
    max_price_val = max(all_prices) if all_prices else 0

    # Debug: Print actual data ranges
    print(f"Data ranges - Price: {min_price_val:.2f} to {max_price_val:.2f}")
    print(f"Data ranges - Volume: {min_vol:,} to {max_vol:,}")
    print(f"Data ranges - Date: {min_date} to {max_date}")

    # Use more reasonable default filter values
    default_min_price = min_price_val if min_price_val > 0 else 0
    default_max_price = max_price_val if max_price_val > 0 else 1000
    default_min_volume = min_vol if min_vol > 0 else 0
    default_max_volume = max_vol if max_vol > 0 else 10000000

    return render_template(
        'dashboard.html', 
        price_html=price_html, 
        volume_html=volume_html,
        tickers=tickers,
        selected_ticker=selected_ticker,
        min_date=min_date,
        max_date=max_date,
        min_vol=min_vol,
        max_vol=max_vol,
        min_price_val=min_price_val,
        max_price_val=max_price_val,
        current_filters={
            'start_date': start_date or min_date,
            'end_date': end_date or max_date,
            'min_volume': min_volume if min_volume is not None else default_min_volume,
            'max_volume': max_volume if max_volume is not None else default_max_volume,
            'min_price': min_price if min_price is not None else default_min_price,
            'max_price': max_price if max_price is not None else default_max_price,
            'volume_increase_threshold': volume_increase_threshold if volume_increase_threshold is not None else ''
        }
    )

@app.route('/api/data')
def api_data():
    """API endpoint for getting filtered data for cross-filtering"""
    selected_ticker = request.args.get('ticker', 'AAPL')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_volume = request.args.get('min_volume', type=float)
    max_volume = request.args.get('max_volume', type=float)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    volume_increase_threshold = request.args.get('volume_increase_threshold', type=float)
    
    filtered_data = {}
    if selected_ticker in data:
        df = data[selected_ticker].copy()
        
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        if min_volume is not None and min_volume > 0:
            df = df[df['Volume'] >= min_volume]
        if max_volume is not None and max_volume > 0:
            df = df[df['Volume'] <= max_volume]
        if min_price is not None and min_price > 0:
            df = df[df['Close'] >= min_price]
        if max_price is not None and max_price > 0:
            df = df[df['Close'] <= max_price]
        
        # Volume increase filtering
        if volume_increase_threshold is not None and volume_increase_threshold > 0:
            df = df.sort_values('Date')
            df['Volume_Change_Pct'] = df['Volume'].pct_change() * 100
            df = df[df['Volume_Change_Pct'] >= volume_increase_threshold]
        
        if not df.empty:
            filtered_data = df.to_dict('records')
    
    return jsonify(filtered_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
