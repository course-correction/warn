#!/usr/bin/env python3
import sys
import json
from warn_sub import nina
import subprocess
import textwrap


def read_json_line():
    sys.stdout.flush()
    line = sys.stdin.readline()
    if not line:
        return None

    return json.loads(line.strip())


def say_headline(headline: str):
    subprocess.Popen(["sudo", "/opt/statusdisplay/bell.sh"])
    #sink_name = ""
    #audio_file = ""

    #if sink_name != "":
    #    subprocess.Popen([
    #        "ffplay",
    #        "-nodisp",
    #        "-autoexit",
    #        "-f", "pulse",
    #        "-i", audio_file,
    #        "-device", sink_name
    #    ])

    headline = "\n".join(textwrap.wrap(headline, 25, break_long_words=False))


    subprocess.Popen(["/home/sd/sd-ng/tooling/show-fullscreen-text", "15", headline])



def main():
    first_data = read_json_line()
    got_headline = False

    if first_data and "headline" in first_data:
        got_headline = True
        say_headline(first_data["headline"])


    read_json_line()



if __name__ == "__main__":
    main()
