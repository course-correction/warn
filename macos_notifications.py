#!/usr/bin/env python3
import sys
import time
import json
from warn_sub import nina
from mac_notifications import client
import subprocess


def read_json_line():
    sys.stdout.flush()
    line = sys.stdin.readline()
    if not line:
        return None

    return json.loads(line.strip())


def main():
    first_data = read_json_line()
    print("Waiting for event details....")
    # Might never come if something fails

    second_data = read_json_line()
    event_details = nina.parse_event(second_data)

    client.create_notification(
        title="NINA",
        text=event_details.headline,
        action_button_str="Open",
        action_callback=lambda: subprocess.Popen(["open", event_details.link]),
    )

    while client.get_notification_manager().get_active_running_notifications() > 0:
        time.sleep(1)
    client.stop_listening_for_callbacks()


if __name__ == "__main__":
    main()
