import subprocess
import time
import requests


def start_ngrok(port):
    command = f"ngrok http {port}"
    process = subprocess.Popen(command, shell=True)
    return process


def get_ngrok_url(port):
    time.sleep(3)  # Wait for ngrok to start and be available
    try:
        ngrok_api_url = "http://localhost:4040/api/tunnels"
        tunnels_info = requests.get(ngrok_api_url).json()
        for tunnel in tunnels_info['tunnels']:
            if tunnel['config']['addr'].endswith(f"{port}"):
                return tunnel['public_url']
    except Exception as e:
        print(f"Error fetching ngrok URL: {e}")
    return None

# Start ngrok for Django (port 8000)
django_process = start_ngrok(8000)
django_url = get_ngrok_url(8000)

# # Start ngrok for MinIO (port 9000)
minio_process = start_ngrok(9000)
minio_url = get_ngrok_url(9000)

print(f"ngrok tunnel for Django: {django_url}")
# print(f"ngrok tunnel for MinIO: {minio_url}")

# Function to stop ngrok processes
def stop_ngrok():
    django_process.terminate()
    minio_process.terminate()
    print("Ngrok tunnels closed.")


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_ngrok()
