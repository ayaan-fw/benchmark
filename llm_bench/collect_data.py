from dotenv import load_dotenv
load_dotenv()
import os
import datetime
import subprocess
import time

"""
Change constants here
"""
api_key = os.getenv('FIREWORKS_API_KEY')
deployment_id = "ejdyohmt"

# Testing mode configuration
TESTING_MODE = "burst"  # Options: "constant" or "burst"

# Constant concurrency mode settings (original behavior)
concurrency_users = [20]  # Number of concurrent workers
spawn_rate = 100          # Rate of spawning new workers (workers/second)

# Burst testing mode settings
burst_configs = [
    {
        "users": 100,           # Number of users in each burst
        "burst_interval": 1.0,  # Interval between bursts in seconds
        "target_rpm": 6000,     # Target requests per minute
        "description": "100 users every 1 second (6000 RPM)"
    },
    {
        "users": 50,
        "burst_interval": 0.5,
        "target_rpm": 6000,
        "description": "50 users every 0.5 seconds (6000 RPM)"
    },
    {
        "users": 200,
        "burst_interval": 2.0,
        "target_rpm": 6000,
        "description": "200 users every 2 seconds (6000 RPM)"
    }
]

# Common settings
prompt_length = 1000    # Input text length for embeddings
embedding_batch_size = 4 # Number of texts to embed in a single request
t = "3min"              # test duration, set to 2 minutes for now

provider_name = "fireworks"
# Using Fireworks embedding model instead of text generation model
model_name = "accounts/ayaan-f375b0/models/qwen3-embedding-8b-fp8"
h = "https://pyroworks-dev-ejdyohmt.us-illinois-1.direct.fireworks.ai" #host url

# Logging configuration
show_embedding_responses = True  # Set to True to see embedding responses (first few dimensions)
verbose_logging = False  # Set to True for more detailed logging output

#Function to utilize subprocess to run the locust script
def execute_subprocess(cmd):
    print(f"\nExecuting benchmark: {' '.join(cmd)}\n")
    process = subprocess.Popen(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )
    # Display output in real-time
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

    return_code = process.poll()
    if return_code != 0:
        print(f"Benchmark failed with return code: {return_code}")
        return False
    return True

def validate_burst_config(config):
    """Validate burst configuration parameters"""
    users = config["users"]
    burst_interval = config["burst_interval"]
    target_rpm = config["target_rpm"]
    
    # Calculate actual RPM based on configuration
    bursts_per_minute = 60 / burst_interval
    actual_rpm = users * bursts_per_minute
    
    print(f"Burst validation:")
    print(f"  Users per burst: {users}")
    print(f"  Burst interval: {burst_interval}s")
    print(f"  Bursts per minute: {bursts_per_minute:.2f}")
    print(f"  Calculated RPM: {actual_rpm:.0f}")
    print(f"  Target RPM: {target_rpm}")
    print(f"  RPM difference: {abs(actual_rpm - target_rpm):.0f}")
    
    if abs(actual_rpm - target_rpm) > target_rpm * 0.05:  # 5% tolerance
        print(f"WARNING: Actual RPM ({actual_rpm:.0f}) differs from target ({target_rpm}) by more than 5%")
    
    return actual_rpm

'''
Make sure to create a .env file in the root directory and add your API keys.
For this example, we will use the Fireworks API key.

Add the following to your .env file:

FIREWORKS_API_KEY=<your_fireworks_api_key>.

Alternatively you can edit the following script flags for custom configurations.
'''

def run_constant_concurrency_test():
    """Run tests with constant concurrency (original behavior)"""
    print("=" * 60)
    print("RUNNING CONSTANT CONCURRENCY TESTS")
    print("=" * 60)
    
    for users in concurrency_users:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        edited_model_name = model_name.replace("/", "_") if provider_name != "fireworks" else model_name.replace("accounts/fireworks/models/", "").replace("/", "_")
        
        results_dir = f"results/constant-embedding-{edited_model_name}-{users}users-batch{embedding_batch_size}-{t.replace('min', 'm')}"
        os.makedirs(results_dir, exist_ok=True)

        # Construct the command
        cmd = [
            "locust",
            "--headless",       # Run without web UI
            "-H", h,           # Host URL
            "--provider", provider_name,
            "--model", model_name,
            "--api-key", api_key,
            "-t", t,           # Test duration
            "--html", f"{results_dir}/report.html",  # Generate HTML report
            "--csv", f"{results_dir}/stats",        # Generate CSV stats
        ]

        # Add concurrency-based parameters (no QPS mode)
        cmd.extend([
            "-u", str(users),          # Number of concurrent users
            "-r", str(spawn_rate),     # Spawn rate
            "-p", str(prompt_length),  # Input text length
            "--embedding-mode",        # Enable embedding mode
            "--embedding-batch-size", str(embedding_batch_size),  # Batch size for embeddings
            "--no-stream"              # Embeddings don't use streaming
        ])

        # Add logging flags if enabled
        if show_embedding_responses:
            cmd.append("--show-response")
        
        if not verbose_logging:
            cmd.append("--only-summary")

        # Add load_test.py as the locust file
        locust_file = os.path.join(os.path.dirname(os.getcwd()), "llm_bench", "load_test.py")
        cmd.extend(["-f", locust_file])

        print(f"\nRunning constant concurrency test with {users} users...")
        success = execute_subprocess(cmd)

        if success: 
            time.sleep(1)
            stat_result_paths = [{"path": f'{results_dir}/stats_stats.csv', "config": {"provider": provider_name, "model": model_name}}]

        time.sleep(25)

def run_burst_tests():
    """Run tests with burst patterns"""
    print("=" * 60)
    print("RUNNING BURST PATTERN TESTS")
    print("=" * 60)
    
    for i, config in enumerate(burst_configs):
        print(f"\nBurst Test {i+1}: {config['description']}")
        print("-" * 40)
        
        # Validate configuration
        actual_rpm = validate_burst_config(config)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        edited_model_name = model_name.replace("/", "_") if provider_name != "fireworks" else model_name.replace("accounts/fireworks/models/", "").replace("/", "_")
        
        results_dir = f"results/burst-embedding-{edited_model_name}-{config['users']}users-{config['burst_interval']}s-{actual_rpm:.0f}rpm-batch{embedding_batch_size}-{t.replace('min', 'm')}"
        os.makedirs(results_dir, exist_ok=True)

        # Construct the command
        cmd = [
            "locust",
            "--headless",       # Run without web UI
            "-H", h,           # Host URL
            "--provider", provider_name,
            "--model", model_name,
            "--api-key", api_key,
            "-t", t,           # Test duration
            "--html", f"{results_dir}/report.html",  # Generate HTML report
            "--csv", f"{results_dir}/stats",        # Generate CSV stats
        ]

        # Add burst-specific parameters
        cmd.extend([
            "-u", str(config["users"]),        # Number of users per burst
            "-r", str(config["users"]),        # High spawn rate for quick burst creation
            "--burst", str(config["burst_interval"]),  # Burst interval
            "-p", str(prompt_length),          # Input text length
            "--embedding-mode",                # Enable embedding mode
            "--embedding-batch-size", str(embedding_batch_size),  # Batch size for embeddings
            "--no-stream"                      # Embeddings don't use streaming
        ])

        # Add logging flags if enabled
        if show_embedding_responses:
            cmd.append("--show-response")
        
        if not verbose_logging:
            cmd.append("--only-summary")

        # Add load_test.py as the locust file
        locust_file = os.path.join(os.path.dirname(os.getcwd()), "llm_bench", "load_test.py")
        cmd.extend(["-f", locust_file])

        print(f"\nRunning burst test: {config['description']}")
        success = execute_subprocess(cmd)

        if success: 
            time.sleep(1)
            stat_result_paths = [{"path": f'{results_dir}/stats_stats.csv', "config": {"provider": provider_name, "model": model_name}}]

        time.sleep(25)

# Main execution
if __name__ == "__main__":
    print(f"Testing mode: {TESTING_MODE}")
    print(f"Provider: {provider_name}")
    print(f"Model: {model_name}")
    print(f"Test duration: {t}")
    print(f"Prompt length: {prompt_length}")
    print(f"Embedding batch size: {embedding_batch_size}")
    print()
    
    if TESTING_MODE == "constant":
        run_constant_concurrency_test()
    elif TESTING_MODE == "burst":
        run_burst_tests()
    else:
        print(f"Unknown testing mode: {TESTING_MODE}")
        print("Available modes: 'constant', 'burst'")