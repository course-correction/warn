#!/usr/bin/env python3
import asyncio
import json
from pathlib import Path
import subprocess
import fcm
import nina
import logging
import argparse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

persist = False
command_str = ""

async def main():
    global persist
    global command_str
    
    parser = argparse.ArgumentParser(
        description="""Subscribe to MoWaS and DWD warnings.

IMPORTANT: This script is not affiliated with any government institution. It utilizes undocumented APIs of NINA and Google, which even in their original intended usage explicitly state that they “are not designed for emergency alerts or other high-risk activities […]. Any such use is expressly prohibited under Section 4.a.7 of the Terms of Service” (quote from Google/Firebase messaging docs).

As such, expect this app to break. You should also be aware that even if you communicate this, users can get accustomed to this app working and start feeling a misguided sense of reliability.
"""
    )
    
    parser.add_argument("--debug", action="store_true", help="Set logging level to debug.")
    parser.add_argument("--persist", action="store_true", help="Save push events as files.")
    parser.add_argument("command", help="Command to execute on push event. Event information is passwd via STDIN as json. First the push data, then the event details after they are queried from nina API.")
    parser.add_argument("region", type=int, nargs="*", help="Region codes to subscribe to. If ommited subscribe to all.")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        
    persist = args.persist
    command_str = args.command

    region_codes = args.region
    if not region_codes:
        logging.info("Subscribing to all region codes")
        region_codes = nina.get_region_codes()
        

    fcm_client = fcm.get_push_client(on_notification)
    
    fcm_token = await fcm_client.checkin_or_register()
    await fcm_client.start()
    nina.configure_push(fcm_token, region_codes)
    
    while True:
        await asyncio.sleep(1)
    
SAVE_DIR = Path("received")

def on_notification(msg, _a, _b):
    logger.debug("New push event", msg)
    msg = json.loads(msg["data"]["custom"])
    try:
        parsed = nina.parse_push_msg(msg)
    except Exception as e:
        logger.error("Unable to parse push message", msg)
        raise e
    
    logger.info(f"Received push event {parsed}")
    if parsed.provider not in ["MOWAS", "DWD"]:
        logger.warning(f"Ignoring push msg from provider {parsed.provider}")
        return
        
    if persist:
        if not SAVE_DIR.exists():
            SAVE_DIR.mkdir()
        
        with open(SAVE_DIR / f"push_{parsed.id}.json", "w") as f:
            json.dump(msg, f, indent=4)
            
    
    parsed_json = parsed.model_dump_json()
    
    process = subprocess.Popen(
        command_str,
        shell=True,
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    process.stdin.write(parsed_json + "\n") # pyright: ignore[reportOptionalMemberAccess]
    process.stdin.flush() # pyright: ignore[reportOptionalMemberAccess]


    event = nina.get_event_raw(parsed.id)
    if persist:        
        with open(SAVE_DIR / f"event_{parsed.id}.json", "w") as f:
            json.dump(event, f, indent=4)
    
    event_str = json.dumps(event)
    # Send second input
    process.stdin.write(event_str + "\n") # pyright: ignore[reportOptionalMemberAccess]
    process.stdin.flush() # pyright: ignore[reportOptionalMemberAccess]
        


if __name__ == "__main__":
    asyncio.run(main())
