# MidiMover

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-FFD43B.svg)

MidiMover is a desktop application for turning motion real-time sensor data into MIDI output. It discovers compatible SensorServer devices over Zero-configuration networking, reads live orientation and acceleration streams from an Android device, and maps them to MIDI note and CC messages for use with DAWs, virtual instruments, and hardware synthesizers.

This project is designed for creative control workflows where physical movement replaces a traditional MIDI controller. Instead of sending a fixed note stream, it transforms motion signals such as tilt, turn, speed, and twist into parameterized MIDI output you can shape in real time.

## What the project does

MidiMover connects to the Android app SensorServer which exposes sensor data via WebSockets and maps it to MIDI. The application provides:

- automatic discovery of SensorServer devices on the local network
- real-time sensor streaming from Android IMU data
- orientation normalization for pitch, roll, and azimuth calculations
- configurable MIDI mappings with input ranges, output ranges, inversion, and exponential curves
- note quantization to a selectable musical scale
- output to a local MIDI port for software or hardware instruments
- a small GUI for connection management and patch configuration

## Why the project is useful

This project is useful when you want to play or control music with physical movement rather than a keyboard or pad. Typical use cases include:

- using a phone as a motion controller for a DAW or synth
- mapping tilt and rotation to pitch, filters, and modulation
- creating expressive, gesture-based performance interfaces
- prototyping custom MIDI controllers without custom hardware

### Key features

- Zero-config discovery with mDNS/zeroconf
- WebSocket data ingestion from Android SensorServer
- MIDI note and CC output with channel selection
- Patch-based control mapping with editable ranges and curves
- Scale-aware note quantization for melodic control
- Cross-platform MIDI backend setup for macOS and Windows

## Project layout

- `app.py` — application entry point and Tkinter window lifecycle
- `input.py` — WebSocket discovery and sensor streaming logic
- `output.py` — MIDI mapping, note quantization, and message sending
- `settings.py` — saved defaults and runtime state management
- `gui/` — Tkinter UI components for connections and control mapping
- `app_data/` — persistent user settings and patch definitions
- `dev/` — recording/playback utilities and development notes

## Getting started

### Prerequisites

Before running the app, make sure you have:

- Python 3.10 or newer
- A compatible Android device running the SensorServer app
- A MIDI output available on your machine, such as:
  - macOS: IAC Driver or a virtual MIDI bus
  - Windows: loopMIDI or another virtual MIDI driver
- Access to the same local network as the Android device

### Install

```bash
git clone https://github.com/aidanmaier/web_sockets_client.git
cd websockets_sensor_access
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
git clone https://github.com/aidanmaier/web_sockets_client.git
cd websockets_sensor_access
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Run the app

```bash
python app.py
```

The GUI will open with a connection panel and control mapping interface. From there you can configure the input device, MIDI output port, and live motion mappings.

## Quick usage workflow

1. Install and start the Android SensorServer app on your device.
2. Ensure the phone and the computer are on the same network.
3. Launch MidiMover.
4. In the Connections panel, select the discovered sensor service.
5. Choose the MIDI output port you want to use.
6. Open the Controls panel and load or edit a patch.
7. Map motion parameters such as Tilt, Turn, Speed, or Twist to MIDI notes or CC values.
8. Press Play to start streaming sensor data.

### Example motion mapping

A typical mapping might do the following:

- `Turn` → mapped to note pitch in a selected scale
- `Tilt` → mapped to filter cutoff or effect control
- `Speed` → mapped to volume or modulation
- `Twist` → mapped to a secondary MIDI CC parameter

This allows a real-world movement pattern to become an expressive musical input.

## Support and resources

For help, use the following resources:

- Project repository: https://github.com/aidanmaier/web_sockets_client
- SensorServer upstream project: https://github.com/UmerCodez/SensorServer
- SensorServer app on F-Droid: https://f-droid.org/packages/github.umer0586.sensorserver/
- Virtual MIDI bus setup guide: https://help.ableton.com/hc/en-us/articles/209774225-Setting-up-a-virtual-MIDI-bus
- BandLab MIDI setup guide: https://help.bandlab.com/hc/en-us/articles/58150962949785-Connecting-MIDI-Devices

If something does not work as expected, open an issue in the GitHub repository and include:

- your operating system
- Python version
- whether the Android SensorServer service is discovered
- the MIDI output port selected
- a short description of the mapping or workflow being tested

## Maintainer and contribution

This project is maintained by the repository owner via GitHub: @aidanmaier.

Contributions are welcome. For a concise contribution checklist, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Contribution expectations

- keep changes focused and easy to review
- prefer small, well-scoped updates
- add or update documentation when behavior changes
- test new mapping logic or connection behavior before submitting a PR

## License

This project is intended for use under the project’s repository license. See the repository metadata for the current license declaration.

---

If you want a more tailored version, this README can also be expanded with screenshots, patch examples, or a short architecture diagram for the sensor-to-MIDI pipeline.