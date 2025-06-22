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
    selected_tickers = request.args.getlist('tickers') or tickers
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_volume = request.args.get('min_volume', type=float)
    max_volume = request.args.get('max_volume', type=float)
    
    # Filter data based on parameters
    filtered_data = {}
    for ticker in selected_tickers:
        if ticker in data:
            df = data[ticker].copy()
            
            # Date filtering
            if start_date:
                df = df[df['Date'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['Date'] <= pd.to_datetime(end_date)]
            
            # Volume filtering
            if min_volume is not None:
                df = df[df['Volume'] >= min_volume]
            if max_volume is not None:
                df = df[df['Volume'] <= max_volume]
            
            if not df.empty:
                filtered_data[ticker] = df
    
    # Create candlestick chart for the first selected ticker
    candlestick_html = ""
    if filtered_data:
        first_ticker = list(filtered_data.keys())[0]
        df = filtered_data[first_ticker]
        
        candlestick = go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=first_ticker
        )
        
        candlestick_layout = go.Layout(
            title=f'{first_ticker} Candlestick Chart',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Price'),
            hovermode='closest'
        )
        
        candlestick_fig = go.Figure(data=[candlestick], layout=candlestick_layout)
        candlestick_fig.update_layout(
            xaxis_rangeslider_visible=False,
            showlegend=False
        )
        candlestick_html = candlestick_fig.to_html(
            full_html=False, 
            config={'displayModeBar': False}
        )

    # Create volume bar chart
    volume_html = ""
    if filtered_data:
        volume_data = []
        for ticker, df in filtered_data.items():
            trace = go.Bar(
                x=df['Date'],
                y=df['Volume'],
                name=ticker,
                opacity=0.7
            )
            volume_data.append(trace)
        
        volume_layout = go.Layout(
            title='Trading Volume Over Time',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Volume'),
            barmode='group'
        )
        
        volume_fig = go.Figure(data=volume_data, layout=volume_layout)
        volume_html = volume_fig.to_html(
            full_html=False, 
            config={'displayModeBar': False}
        )

    # Get date range for filter defaults
    all_dates = []
    all_volumes = []
    for df in data.values():
        all_dates.extend(df['Date'].tolist())
        all_volumes.extend(df['Volume'].tolist())
    
    min_date = min(all_dates).strftime('%Y-%m-%d') if all_dates else ''
    max_date = max(all_dates).strftime('%Y-%m-%d') if all_dates else ''
    min_vol = min(all_volumes) if all_volumes else 0
    max_vol = max(all_volumes) if all_volumes else 0

    return render_template(
        'dashboard.html', 
        candlestick_html=candlestick_html, 
        volume_html=volume_html,
        tickers=tickers,
        selected_tickers=selected_tickers,
        min_date=min_date,
        max_date=max_date,
        min_vol=min_vol,
        max_vol=max_vol,
        current_filters={
            'start_date': start_date or min_date,
            'end_date': end_date or max_date,
            'min_volume': min_volume or min_vol,
            'max_volume': max_volume or max_vol
        }
    )

@app.route('/api/data')
def api_data():
    """API endpoint for getting filtered data for cross-filtering"""
    selected_tickers = request.args.getlist('tickers') or tickers
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_volume = request.args.get('min_volume', type=float)
    max_volume = request.args.get('max_volume', type=float)
    
    filtered_data = {}
    for ticker in selected_tickers:
        if ticker in data:
            df = data[ticker].copy()
            
            if start_date:
                df = df[df['Date'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['Date'] <= pd.to_datetime(end_date)]
            if min_volume is not None:
                df = df[df['Volume'] >= min_volume]
            if max_volume is not None:
                df = df[df['Volume'] <= max_volume]
            
            if not df.empty:
                filtered_data[ticker] = df.to_dict('records')
    
    return jsonify(filtered_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
