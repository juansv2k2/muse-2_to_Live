from __future__ import annotations

import argparse
import sys
import time
from collections import deque

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from pylsl import StreamInlet, resolve_byprop


def connect_eeg_stream(timeout: float) -> StreamInlet:
    """Resolve the Muse EEG stream and return an inlet."""
    while True:
        streams = resolve_byprop("type", "EEG", timeout=timeout)
        if streams:
            print("Connected to Muse EEG stream.")
            return StreamInlet(streams[0])

        print("No EEG LSL stream found. Start streaming with: muselsl stream", file=sys.stderr)
        time.sleep(1.0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Live Muse 2 brainwaves viewer (EEG over LSL).")
    parser.add_argument("--window-seconds", type=float, default=8.0, help="Visible time window")
    parser.add_argument("--sample-rate", type=int, default=256, help="Expected EEG sample rate")
    parser.add_argument("--refresh-ms", type=int, default=50, help="Plot refresh interval in milliseconds")
    parser.add_argument(
        "--scale",
        type=float,
        default=300.0,
        help="Vertical range for each channel in microvolts (+/-scale/2)",
    )
    args = parser.parse_args()

    inlet = connect_eeg_stream(timeout=5.0)
    channel_count = inlet.info().channel_count()
    if channel_count < 4:
        print(f"EEG stream has {channel_count} channels, need at least 4.", file=sys.stderr)
        return 1

    max_points = max(32, int(args.window_seconds * args.sample_rate))
    times = deque(maxlen=max_points)
    channels = [deque(maxlen=max_points) for _ in range(4)]

    fig, ax = plt.subplots(figsize=(11, 6))
    colors = ["#f94144", "#f3722c", "#277da1", "#43aa8b"]
    labels = ["TP9", "AF7", "AF8", "TP10"]
    offsets = np.array([0.0, args.scale, 2 * args.scale, 3 * args.scale], dtype=float)

    lines = []
    for idx, (color, label) in enumerate(zip(colors, labels)):
        (line,) = ax.plot([], [], color=color, linewidth=1.1, label=label)
        lines.append(line)
        ax.axhline(offsets[idx], color="#cccccc", linewidth=0.4, linestyle="--")

    ax.set_title("Muse 2 EEG Live View")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Channels (offset)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.2)

    def update(_frame):
        pulled = 0
        while pulled < 24:
            sample, timestamp = inlet.pull_sample(timeout=0.0)
            if sample is None:
                break
            times.append(timestamp)
            if len(sample) < 4:
                continue
            for i in range(4):
                channels[i].append(float(sample[i]))
            pulled += 1

        if not times:
            return lines

        t = np.array(times, dtype=float)
        t = t - t[-1]

        for i in range(4):
            y = np.array(channels[i], dtype=float) + offsets[i]
            lines[i].set_data(t, y)

        ax.set_xlim(-args.window_seconds, 0.0)
        ax.set_ylim(-args.scale * 0.5, offsets[-1] + args.scale * 0.8)
        return lines

    # Keep a strong reference, otherwise matplotlib may stop updating frames.
    animation = FuncAnimation(fig, update, interval=args.refresh_ms, blit=False)

    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        del animation

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
