from dotenv import load_dotenv
load_dotenv()
import os
import datetime
import subprocess
import time

"""
Change constants here
"""
api_key = os.getenv('DR_API_KEY')
deployment_id = "ed026bc8"
concurrency_users = [20]  # Number of concurrent workers (changed from rpms)
spawn_rate = 100          # Rate of spawning new workers (workers/second)
prompt_length = 1000    # Input text length for embeddings
embedding_batch_size = 4 # Number of texts to embed in a single request
t = "15min"              # test duration, set to 2 minutes for now

provider_name = "fireworks"
# Using Fireworks embedding model instead of text generation model
model_name = "accounts/ayaan-f375b0/models/qwen3-embedding-8b"
h = "https://pyroworks-i9zno67d.us-illinois-1.direct.fireworks.ai" #host url


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


'''
Make sure to create a .env file in the root directory and add your API keys.
For this example, we will use the Fireworks API key.

Add the following to your .env file:

FIREWORKS_API_KEY=<your_fireworks_api_key>.

Alternatively you can edit the following script flags for custom configurations.
'''

for users in concurrency_users:
    # Create results directory based on concurrency instead of RPM
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    edited_model_name = model_name.replace("/", "_") if provider_name != "fireworks" else model_name.replace("accounts/fireworks/models/", "").replace("/", "_")

    results_dir = f"results/embedding-{edited_model_name}-{users}users-batch{embedding_batch_size}-{t.replace('min', 'm')}"
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
        # Keep output cleaner if verbose logging is disabled
        cmd.append("--only-summary")

    # Add load_test.py as the locust file
    locust_file = os.path.join(os.path.dirname(os.getcwd()), "llm_bench", "load_test.py")
    cmd.extend(["-f", locust_file]) 

    #call our helper function to execute the command
    success = execute_subprocess(cmd)

    #Visualize the results
    if success: 
        time.sleep(1)
        stat_result_paths = [{"path": f'{results_dir}/stats_stats.csv', "config": {"provider": provider_name, "model": model_name}}]
        #visualize_comparative_results(stat_result_paths, results_dir)

    time.sleep(25)