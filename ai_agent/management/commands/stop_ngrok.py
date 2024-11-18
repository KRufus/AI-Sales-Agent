from django.core.management.base import BaseCommand
import psutil 

class Command(BaseCommand):
    help = 'Stop ngrok tunnels for Django and MinIO'

    def handle(self, *args, **kwargs):
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == 'ngrok':
                process.terminate()  # Terminate ngrok process
                self.stdout.write(f"Terminated ngrok process with PID: {process.info['pid']}")
        self.stdout.write("All ngrok processes have been terminated.")
