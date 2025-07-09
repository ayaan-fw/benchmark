#!/usr/bin/env python3
"""
Script to analyze burst patterns from Locust CSV results
Usage: python analyze_burst_pattern.py <csv_file> <expected_burst_interval>
"""

import csv
import sys
import datetime
from collections import defaultdict
import os

def analyze_burst_pattern(csv_file, expected_interval):
    """Analyze the CSV file to confirm burst patterns"""
    
    print(f"Analyzing burst pattern from: {csv_file}")
    print(f"Expected burst interval: {expected_interval}s")
    print("=" * 50)
    
    # Try to find the correct CSV file
    csv_dir = os.path.dirname(csv_file)
    
    # Look for history file first (contains timestamps)
    history_file = os.path.join(csv_dir, "stats_history.csv")
    if os.path.exists(history_file):
        print(f"📊 Found history file: {history_file}")
        return analyze_history_file(history_file, expected_interval)
    
    # If no history file, try to analyze the provided file
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        
        df = pd.read_csv(csv_file)
        print("CSV columns:", df.columns.tolist())
        
        # Check if this is a summary stats file (no timestamps)
        if 'timestamp' not in df.columns and 'Type' in df.columns:
            print("\n⚠️  This appears to be a summary statistics file (stats_stats.csv)")
            print("For detailed burst pattern analysis, we need the stats_history.csv file")
            print("Summary from stats_stats.csv:")
            
            # Extract useful info from summary stats
            embedding_row = df[df['Name'] == '/v1/embeddings']
            if not embedding_row.empty:
                req_count = embedding_row['Request Count'].iloc[0]
                rps = embedding_row['Requests/s'].iloc[0]
                avg_response_time = embedding_row['Average Response Time'].iloc[0]
                
                print(f"  Total requests: {req_count}")
                print(f"  Average RPS: {rps:.2f}")
                print(f"  Average response time: {avg_response_time:.2f}ms")
                
                # Calculate expected pattern
                # For burst testing, if we send X requests every Y seconds, average RPS = X/Y
                # But we need to extract the burst size from the test configuration
                # For now, let's work backwards from the total requests and test duration
                
                print(f"\nBurst pattern analysis:")
                print(f"  Expected burst interval: {expected_interval}s")
                print(f"  Actual average RPS: {rps:.2f}")
                
                # Calculate what the burst size would be if this were truly burst testing
                estimated_burst_size = rps * expected_interval
                print(f"  Estimated burst size (if pattern is correct): {estimated_burst_size:.0f} requests per burst")
                
                # Check if the pattern looks like burst testing
                # In burst testing, we expect periods of high activity followed by idle periods
                # The average RPS should be much lower than the peak RPS during bursts
                if estimated_burst_size > 10:  # Reasonable burst size
                    print("✅ RPS PATTERN CONSISTENT WITH BURST TESTING")
                    print(f"💡 This suggests ~{estimated_burst_size:.0f} requests sent every {expected_interval}s")
                else:
                    print("❓ RPS PATTERN NEEDS VERIFICATION - MAY BE CONSTANT LOAD")
            
            return False
            
        # If it has timestamps, proceed with normal analysis
        return analyze_with_timestamps(df, expected_interval, csv_file)
        
    except ImportError:
        print("⚠️  pandas/matplotlib not available, using simple analysis...")
        return simple_analysis(csv_file, expected_interval)
    except Exception as e:
        print(f"❌ Error analyzing CSV: {e}")
        return False

def analyze_history_file(history_file, expected_interval):
    """Analyze the stats_history.csv file for burst patterns"""
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        
        df = pd.read_csv(history_file)
        print("History file columns:", df.columns.tolist())
        
        # History file typically has columns like: Timestamp, User Count, Type, Name, Requests/s, etc.
        if 'Timestamp' in df.columns:
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['Timestamp'])
            
            # Filter for embedding requests
            embedding_data = df[df['Name'] == '/v1/embeddings'].copy()
            if embedding_data.empty:
                embedding_data = df[df['Type'] == 'POST'].copy()
            
            if not embedding_data.empty:
                # Sort by timestamp
                embedding_data = embedding_data.sort_values('timestamp')
                
                # Get the start time
                start_time = embedding_data['timestamp'].iloc[0]
                
                # Calculate relative time in seconds
                embedding_data['relative_time'] = (embedding_data['timestamp'] - start_time).dt.total_seconds()
                
                # Plot RPS over time
                plt.figure(figsize=(15, 6))
                plt.plot(embedding_data['relative_time'], embedding_data['Requests/s'], 'b-', alpha=0.7)
                plt.title('Requests per Second Over Time')
                plt.xlabel('Time (seconds)')
                plt.ylabel('Requests/s')
                plt.grid(True)
                
                # Add expected burst markers
                max_time = embedding_data['relative_time'].max()
                for i in range(0, int(max_time), int(expected_interval)):
                    plt.axvline(x=i, color='red', linestyle='--', alpha=0.5, label='Expected burst times' if i == 0 else "")
                
                plt.legend()
                plt.tight_layout()
                plt.savefig(f'burst_analysis_history.png')
                print(f"\n📈 Visualization saved as: burst_analysis_history.png")
                
                # Analyze the pattern
                rps_values = embedding_data['Requests/s'].values
                high_rps = rps_values[rps_values > rps_values.mean() + rps_values.std()]
                
                print(f"\nBurst analysis:")
                print(f"  Average RPS: {rps_values.mean():.2f}")
                print(f"  Max RPS: {rps_values.max():.2f}")
                print(f"  Number of high-RPS periods: {len(high_rps)}")
                
                # Check if pattern matches expected
                if len(high_rps) > 0:
                    print("✅ BURST PATTERN DETECTED IN HISTORY DATA")
                else:
                    print("❓ NO CLEAR BURST PATTERN FOUND")
                
                return True
        
        return False
        
    except ImportError:
        print("⚠️  pandas/matplotlib not available for history analysis")
        return False
    except Exception as e:
        print(f"❌ Error analyzing history file: {e}")
        return False

def analyze_with_timestamps(df, expected_interval, csv_file):
    """Analyze CSV with individual request timestamps"""
    import pandas as pd
    import matplotlib.pyplot as plt
    
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
    print(f"\n📈 Visualization saved as: burst_analysis_{csv_file.replace('.csv', '')}.png")
    
    return True

def simple_analysis(csv_file, expected_interval):
    """Simple analysis without pandas/matplotlib dependencies"""
    
    print(f"Analyzing burst pattern from: {csv_file}")
    print(f"Expected burst interval: {expected_interval}s")
    print("=" * 50)
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            print("❌ No data found in CSV")
            return False
            
        # Check if this is a summary stats file
        if 'Type' in rows[0] and 'Name' in rows[0]:
            print("\n⚠️  This appears to be a summary statistics file (stats_stats.csv)")
            print("For detailed burst pattern analysis, we need the stats_history.csv file")
            print("Summary from stats_stats.csv:")
            
            # Find embedding row
            for row in rows:
                if row.get('Name') == '/v1/embeddings':
                    req_count = float(row.get('Request Count', 0))
                    rps = float(row.get('Requests/s', 0))
                    avg_response_time = float(row.get('Average Response Time', 0))
                    
                    print(f"  Total requests: {req_count:.0f}")
                    print(f"  Average RPS: {rps:.2f}")
                    print(f"  Average response time: {avg_response_time:.2f}ms")
                    
                    # Calculate if the pattern matches
                    estimated_burst_size = rps * expected_interval
                    print(f"\nBurst pattern analysis:")
                    print(f"  Expected burst interval: {expected_interval}s")
                    print(f"  Estimated burst size: {estimated_burst_size:.0f} requests per burst")
                    
                    # For burst testing, the average RPS should be much lower than peak
                    # because there are idle periods between bursts
                    if estimated_burst_size > 10:  # Reasonable burst size
                        print("✅ RPS PATTERN CONSISTENT WITH BURST TESTING")
                        print(f"💡 This suggests ~{estimated_burst_size:.0f} requests sent every {expected_interval}s")
                    else:
                        print("❓ RPS PATTERN NEEDS VERIFICATION - MAY BE CONSTANT LOAD")
                    
                    break
            
            return False
            
        # If it has timestamps, try to analyze them
        timestamps = []
        for row in rows:
            if 'timestamp' in row:
                timestamps.append(row['timestamp'])
        
        if not timestamps:
            print("❌ No timestamp data found in CSV")
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
        print(f"❌ Error in simple analysis: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyze_burst_pattern.py <csv_file> <expected_burst_interval>")
        print("Example: python analyze_burst_pattern.py stats_stats.csv 5.0")
        print("\nThis script will:")
        print("1. Look for stats_history.csv in the same directory for detailed analysis")
        print("2. Analyze the provided CSV file if no history file is found")
        print("3. Provide burst pattern validation and visualization")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    expected_interval = float(sys.argv[2])
    
    print("🔍 BURST PATTERN ANALYSIS")
    print("=" * 50)
    
    # Try advanced analysis first, fall back to simple if dependencies missing
    try:
        analyze_burst_pattern(csv_file, expected_interval)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1) 