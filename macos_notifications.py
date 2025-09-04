#!/usr/bin/env python3
import sys
import json
from warn_sub import nina
import subprocess


def read_json_line():
    sys.stdout.flush()
    line = sys.stdin.readline()
    if not line:
        return None

    return json.loads(line.strip())


def say_headline(headline: str):
    subprocess.Popen(["say", "-v", "Anna (Premium)", headline])


def open_event(link: str):
    subprocess.Popen(
        [
            "/Applications/Firefox.app/Contents/MacOS/firefox",
            "-P",
            "default-release",
            link,
        ]
    )


def main():
    first_data = read_json_line()
    got_headline = False
    got_link = False

    if first_data and "headline" in first_data:
        got_headline = True
        print("received headline in first data")
        say_headline(first_data["headline"])

    if first_data and "link" in first_data:
        got_link = True
        print("received link in first data")
        open_event(first_data["link"])

    print("Waiting for event details....")
    # Might never come if something fails

    second_data = read_json_line()
    event_details = nina.parse_event(second_data)

    if not got_headline:
        say_headline(event_details.headline)

    if not got_link:
        open_event(event_details.link)

    print("done")


if __name__ == "__main__":
    main()
