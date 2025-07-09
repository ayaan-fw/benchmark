#!/usr/bin/env python3
"""
Script to analyze burst patterns from Locust CSV results
Usage: python analyze_burst_pattern.py <csv_file> <expected_burst_interval>
"""

import csv
import sys
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd

def analyze_burst_pattern(csv_file, expected_interval):
    """Analyze the CSV file to confirm burst patterns"""
    
    print(f"Analyzing burst pattern from: {csv_file}")
    print(f"Expected burst interval: {expected_interval}s")
    print("=" * 50)
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Get the start time
        start_time = df['timestamp'].iloc[0]
        
        # Calculate relative time in seconds
        df['relative_time'] = (df['timestamp'] - start_time).dt.total_seconds()
        
        # Group requests by second intervals
        df['time_bucket'] = df['relative_time'].round(1)
        
        # Count requests per time bucket
        requests_per_bucket = df.groupby('time_bucket').size().reset_index(name='request_count')
        
        print("First 20 time buckets:")
        print(requests_per_bucket.head(20))
        
        # Analyze burst detection
        burst_threshold = 10  # Minimum requests to consider a burst
        bursts = requests_per_bucket[requests_per_bucket['request_count'] >= burst_threshold]
        
        if len(bursts) > 0:
            print(f"\nDetected {len(bursts)} potential bursts:")
            print(bursts.head(10))
            
            # Calculate intervals between bursts
            if len(bursts) > 1:
                burst_intervals = bursts['time_bucket'].diff().dropna()
                avg_interval = burst_intervals.mean()
                print(f"\nAverage interval between bursts: {avg_interval:.2f}s")
                print(f"Expected interval: {expected_interval}s")
                print(f"Interval difference: {abs(avg_interval - expected_interval):.2f}s")
                
                if abs(avg_interval - expected_interval) < 0.5:
                    print("✅ BURST PATTERN CONFIRMED!")
                else:
                    print("❌ BURST PATTERN DOES NOT MATCH EXPECTED")
        
        # Create a visualization
        plt.figure(figsize=(15, 8))
        
        # Plot 1: Requests over time
        plt.subplot(2, 1, 1)
        plt.plot(requests_per_bucket['time_bucket'], requests_per_bucket['request_count'], 'b-', alpha=0.7)
        plt.title('Requests per Second Over Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Number of Requests')
        plt.grid(True)
        
        # Add expected burst markers
        max_time = requests_per_bucket['time_bucket'].max()
        for i in range(0, int(max_time), int(expected_interval)):
            plt.axvline(x=i, color='red', linestyle='--', alpha=0.5)
        
        # Plot 2: Histogram of request counts
        plt.subplot(2, 1, 2)
        plt.hist(requests_per_bucket['request_count'], bins=50, alpha=0.7)
        plt.title('Distribution of Requests per Second')
        plt.xlabel('Number of Requests')
        plt.ylabel('Frequency')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f'burst_analysis_{csv_file.replace(".csv", "")}.png')
        print(f"\nVisualization saved as: burst_analysis_{csv_file.replace('.csv', '')}.png")
        
    except Exception as e:
        print(f"Error analyzing CSV: {e}")
        return False
    
    return True

def simple_analysis(csv_file, expected_interval):
    """Simple analysis without pandas/matplotlib dependencies"""
    
    print(f"Analyzing burst pattern from: {csv_file}")
    print(f"Expected burst interval: {expected_interval}s")
    print("=" * 50)
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            timestamps = []
            
            for row in reader:
                if 'timestamp' in row:
                    timestamps.append(row['timestamp'])
        
        if not timestamps:
            print("No timestamp data found in CSV")
            return False
            
        # Convert timestamps and calculate intervals
        print(f"Total requests: {len(timestamps)}")
        print(f"First 10 timestamps:")
        for i, ts in enumerate(timestamps[:10]):
            print(f"  {i+1}: {ts}")
            
        # Group by second intervals
        second_counts = defaultdict(int)
        for ts in timestamps:
            # Extract second from timestamp (simplified)
            try:
                # Assuming timestamp format like "2024-01-01 12:00:00"
                if '.' in ts:
                    ts = ts.split('.')[0]  # Remove microseconds
                dt = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                second_key = dt.strftime('%H:%M:%S')
                second_counts[second_key] += 1
            except:
                continue
        
        # Show request distribution
        print(f"\nRequests per second (first 20):")
        for i, (second, count) in enumerate(sorted(second_counts.items())[:20]):
            print(f"  {second}: {count} requests")
            
        return True
        
    except Exception as e:
        print(f"Error in simple analysis: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyze_burst_pattern.py <csv_file> <expected_burst_interval>")
        print("Example: python analyze_burst_pattern.py stats_stats.csv 5.0")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    expected_interval = float(sys.argv[2])
    
    # Try advanced analysis first, fall back to simple if dependencies missing
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        analyze_burst_pattern(csv_file, expected_interval)
    except ImportError:
        print("pandas/matplotlib not available, using simple analysis...")
        simple_analysis(csv_file, expected_interval) 