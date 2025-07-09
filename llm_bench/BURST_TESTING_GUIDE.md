# Burst Testing Validation Guide

This guide explains how to confirm that your burst testing is working correctly with the pattern "250 requests every 5 seconds".

## Methods to Confirm Burst Pattern

### 1. **Configuration Validation (Pre-Test)**

When you run `python collect_data.py` with burst mode, you'll see validation output:

```
Burst validation:
  Users per burst: 250
  Burst interval: 5.0s
  Bursts per minute: 12.00
  Bursts per hour: 720
  Calculated RPM: 3000
  Target RPM: 3000
  RPM difference: 0

Timing pattern preview:
  At time 0s: 250 requests sent
  At time 5.0s: 250 requests sent
  At time 10.0s: 250 requests sent
  At time 15.0s: 250 requests sent
  ...
```

### 2. **Real-Time Web UI Monitoring**

Enable the web UI for real-time visualization:

```python
# In collect_data.py
enable_web_ui = True
```

Then run the test and visit `http://localhost:8089` to see:
- Real-time request rate graphs
- Charts showing request patterns over time
- Current RPS (requests per second) metrics

### 3. **CSV Analysis (Post-Test)**

After the test completes, analyze the CSV output:

```bash
# Install dependencies if needed
pip install pandas matplotlib

# Analyze the results
python analyze_burst_pattern.py results/burst-*/stats_stats.csv 5.0
```

Expected output:
```
Analyzing burst pattern from: results/burst-*/stats_stats.csv
Expected burst interval: 5.0s
==================================================
First 20 time buckets:
   time_bucket  request_count
0          0.0            250
1          5.0            250
2         10.0            250
3         15.0            250
...

Detected 180 potential bursts:
Average interval between bursts: 5.02s
Expected interval: 5.0s
Interval difference: 0.02s
✅ BURST PATTERN CONFIRMED!
```

### 4. **Manual CSV Inspection**

You can manually inspect the CSV file:

```bash
# Look at the timestamps
head -20 results/burst-*/stats_stats.csv

# Count requests per second
cut -d',' -f1 results/burst-*/stats_stats.csv | cut -d' ' -f2 | cut -d':' -f3 | sort | uniq -c
```

### 5. **Console Output During Test**

During the test, you'll see output like:
```
Embedding response: 45.23 ms, 3072 dimensions, sent 1 texts, received 1 embeddings
Embedding response: 43.18 ms, 3072 dimensions, sent 1 texts, received 1 embeddings
...
[250 similar lines within ~1 second]
[5 second pause]
Embedding response: 44.91 ms, 3072 dimensions, sent 1 texts, received 1 embeddings
...
```

## Example Burst Configuration

```python
{
    "users": 250,           # 250 requests per burst
    "burst_interval": 5.0,  # Every 5 seconds
    "target_rpm": 3000,     # 250 * 12 = 3000 RPM
    "description": "250 users every 5 seconds (3000 RPM)"
}
```

## Key Validation Points

### ✅ **Correct Pattern Indicators:**
- CSV shows 250 requests clustered around 0s, 5s, 10s, 15s, etc.
- Web UI shows spike pattern every 5 seconds
- Average interval between bursts ≈ 5.0 seconds
- Total RPM matches calculation (250 × 12 = 3000)

### ❌ **Incorrect Pattern Indicators:**
- Requests spread evenly over time (constant rate)
- Irregular intervals between bursts
- Total request count doesn't match expected
- Web UI shows smooth continuous rate

## Troubleshooting

### **If burst pattern is not working:**

1. **Check Locust version:** Ensure you have a recent version that supports `--burst`
2. **Verify configuration:** Make sure `TESTING_MODE = "burst"` is set
3. **Check server capacity:** Server might be too slow to handle burst loads
4. **Review logs:** Look for warnings about insufficient users or overload

### **If timing is slightly off:**
- Small variations (±0.5s) are normal due to network latency
- Large variations indicate system overload or configuration issues

## Advanced Analysis

For detailed analysis, you can create custom scripts to:
- Plot request timestamps as scatter plots
- Calculate standard deviation of inter-burst intervals
- Analyze response time distribution during bursts vs. idle periods
- Compare server behavior under burst vs. constant load

## Example Results Directory Structure

```
results/
├── burst-embedding-qwen3-embedding-8b-250users-5.0s-3000rpm-batch4-15m/
│   ├── report.html          # Locust HTML report
│   ├── stats_stats.csv      # Request-level data
│   ├── stats_failures.csv   # Failure data
│   └── stats_history.csv    # Time-series data
└── burst_analysis_stats_stats.png  # Generated visualization
```

The burst testing helps you understand how your system performs under realistic traffic patterns where requests come in waves rather than at a constant rate. 