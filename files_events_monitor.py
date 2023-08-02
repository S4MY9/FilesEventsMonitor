import os
import sys
import time
import requests
import datetime
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

EVENT_COLORS = {
    "created": 0x00FF00,
    "deleted": 0xFF0000,
    "modified": 0xFFFF00,
    "moved": 0x0000FF
}

EMOJIS = {
    "created": ":green_circle:",
    "deleted": ":red_circle:",
    "modified": ":yellow_circle:",
    "moved": ":blue_circle:",
    "date": ":calendar:",
    "file_path": ":file_folder:"
}

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Custom FileSystemEventHandler to handle file system events
class FileMonitorHandler(FileSystemEventHandler):
    def __init__(self, discord_webhook_url=None, output_file=None):
        self.discord_webhook_url = discord_webhook_url
        self.output_file = output_file

    def on_any_event(self, event):
        timestamp = get_timestamp()
        event_type = event.event_type.lower()
        file_path = event.src_path
        if event_type == "moved":
            print(f"[{timestamp}] {event_type.upper()} {file_path} -> {event.dest_path}")
        else:
            print(f"[{timestamp}] {event_type.upper()} {file_path}")

        if self.discord_webhook_url:
            self.send_discord_alert(event_type, file_path, timestamp, event)
        if self.output_file:
            self.save_to_output_file(timestamp, event_type, file_path)

    def send_discord_alert(self, event_type, file_path, timestamp, event):
        data = {
            "username": "Files Events Monitor",
            "avatar_url": "https://media.istockphoto.com/id/881436122/vector/file-folder-flat-vector-icon.jpg?s=170667a&w=0&k=20&c=NObDpHxdzdTQbT1Z7K_vPFqNv_EN_8c3tcRB6VPdiwE=",
            "embeds": [
                {
                    "title": f"{EMOJIS[event_type]} {event_type.upper()}",
                    "color": EVENT_COLORS.get(event_type, 0xFFFFFF),
                    "fields": [
                        {"name": ":calendar: Date", "value": timestamp},
                        {"name": ":file_folder: File Path", "value": file_path}
                    ],
                    "footer": {
                        "text": "Created by S4MY9. https://s4my9.github.io"
                    }
                }
            ]
        }
        if event_type == "moved":
            data["embeds"][0]["fields"].append({"name": ":file_folder: Destination Path", "value": event.dest_path})

        requests.post(self.discord_webhook_url, json=data)

    def save_to_output_file(self, timestamp, event_type, file_path):
        with open(self.output_file, "a") as output_file:
            output_file.write(f"[{timestamp}] {event_type.upper()} {file_path}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Monitor the integrity and activity of files in a specified directory.\n-> Created by S4MY9. https://s4my9.github.io",
        formatter_class=argparse.RawTextHelpFormatter,
        usage="%(prog)s <directory> [-h] [-w] [-o]"
    )
    parser.add_argument("directory", help="The directory path to monitor.")
    parser.add_argument("-w", "--webhook", help="Discord webhook URL", metavar='')
    parser.add_argument("-o", "--output", help="Output file path", metavar='')
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print("Error: The specified directory does not exist.")
        sys.exit(1)

    event_handler = FileMonitorHandler(discord_webhook_url=args.webhook, output_file=args.output)
    observer = Observer()
    observer.schedule(event_handler, path=args.directory, recursive=True)
    observer.start()

    try:
        print(f"[*] Monitoring directory: {args.directory}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()