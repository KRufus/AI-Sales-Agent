from django.core.management.base import BaseCommand
import subprocess
import psutil
import time
from ai_agent.utils.ngrok_manager import start_ngrok, get_ngrok_url

class Command(BaseCommand):
    help = 'Start or stop ngrok tunnels for Django and MinIO'

    def add_arguments(self, parser):
        parser.add_argument('--stop', action='store_true', help='Stop ngrok tunnels')

    def handle(self, *args, **options):
        if options['stop']:
            # Stop ngrok processes
            for process in psutil.process_iter(['pid', 'name']):
                if process.info['name'] == 'ngrok':
                    process.terminate()
                    self.stdout.write(f"Terminated ngrok process with PID: {process.info['pid']}")
            self.stdout.write("All ngrok processes have been terminated.")
        else:
            # Start ngrok tunnels
            django_process = start_ngrok(8000)
            django_url = get_ngrok_url(8000)
            minio_process = start_ngrok(9000)
            minio_url = get_ngrok_url(9000)

            self.stdout.write(f"ngrok Django URL: {django_url}")
            # self.stdout.write(f"ngrok MinIO URL: {minio_url}")

            try:
                self.stdout.write("ngrok tunnels are running... Press Ctrl+C to stop.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                django_process.terminate()
                minio_process.terminate()
                self.stdout.write("ngrok tunnels stopped.")
