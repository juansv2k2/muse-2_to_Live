# Muse 2 to Live

This repository is a clean rewrite of the old duplicated project and is now based on [`muse-lsl`](https://github.com/alexandrebarachant/muse-lsl) for Muse 2 streaming.

## What this project does

- Connects to Muse 2 using `muse-lsl`
- Reads Muse data from LSL
- Sends values to an OSC endpoint (for Ableton Live or any OSC-compatible receiver)

## Prerequisites

- Python 3.10+
- Muse 2 headset
- Bluetooth enabled

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

1. Start Muse streaming in one terminal:

```bash
muselsl stream
```

2. Start the LSL to OSC bridge in another terminal:

```bash
muse2-osc --host 127.0.0.1 --port 5005 --stream-type EEG --auto-reconnect
```

## OSC message format

- Timestamp: `/muse/timestamp`
- Channel values: `/muse/<stream_type>/<channel_index>`

Example for EEG channel 1:

- `/muse/eeg/1`

## Next suggested step

Add an Ableton Live Max for Live patch that maps the OSC paths to parameters.
