from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable

from pylsl import StreamInlet, resolve_byprop
from pythonosc.udp_client import SimpleUDPClient


def pick_stream(stream_types: Iterable[str], timeout: float = 8.0):
    """Resolve the first available LSL stream by stream type preference order."""
    for stream_type in stream_types:
        streams = resolve_byprop("type", stream_type, timeout=timeout)
        if streams:
            return stream_type, streams[0]
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bridge Muse LSL stream data to OSC for Ableton Live or other OSC targets."
    )
    parser.add_argument("--host", default="127.0.0.1", help="OSC target host")
    parser.add_argument("--port", default=5005, type=int, help="OSC target port")
    parser.add_argument(
        "--stream-type",
        default="EEG",
        choices=["EEG", "PPG", "ACC", "GYRO"],
        help="Preferred Muse stream type",
    )
    parser.add_argument(
        "--osc-prefix",
        default="/muse",
        help="OSC address prefix (example: /muse)",
    )
    parser.add_argument(
        "--auto-reconnect",
        action="store_true",
        help="Reconnect automatically when stream disconnects",
    )
    args = parser.parse_args()

    client = SimpleUDPClient(args.host, args.port)
    stream_order = [args.stream_type, "EEG", "PPG", "ACC", "GYRO"]

    while True:
        chosen_type, stream = pick_stream(stream_order)
        if stream is None:
            print("No Muse LSL stream found. Start streaming with: muselsl stream", file=sys.stderr)
            if not args.auto_reconnect:
                return 1
            time.sleep(2)
            continue

        print(f"Connected to LSL stream type: {chosen_type}")
        inlet = StreamInlet(stream)

        try:
            while True:
                sample, timestamp = inlet.pull_sample(timeout=2.0)
                if sample is None:
                    if args.auto_reconnect:
                        raise RuntimeError("LSL stream timeout")
                    continue

                client.send_message(f"{args.osc_prefix}/timestamp", float(timestamp))
                for idx, value in enumerate(sample, start=1):
                    client.send_message(f"{args.osc_prefix}/{chosen_type.lower()}/{idx}", float(value))
        except KeyboardInterrupt:
            print("Stopped by user.")
            return 0
        except Exception as exc:  # pragma: no cover - runtime reconnection path
            print(f"Stream disconnected: {exc}", file=sys.stderr)
            if not args.auto_reconnect:
                return 2
            time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
