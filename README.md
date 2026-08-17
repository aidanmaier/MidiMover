# MidiMover

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-FFD43B.svg)

MidiMover is a desktop application for turning motion real-time sensor data into MIDI output. It allows musicians to control instruments using only gestural motion, and the controls can be mapped to fit the performer's personal range of motion.

MidiMover discovers compatible [SensorServer](https://github.com/UmerCodez/SensorServer) instances over Zero-configuration networking, reads live orientation and acceleration streams from an Android device, and maps them to MIDI note and CC messages for use with DAWs, virtual instruments, and hardware synthesizers.



## Features

MidiMover connects to the Android app SensorServer which exposes sensor data via WebSockets and maps it to MIDI. The application provides:

- automatic discovery of SensorServer instances on the local network
- Motion parameters: pitch, roll, azimuth and speed can be mapped to notes or common General MIDI controls
- configurable MIDI mappings with input ranges, output ranges, inversion, and linear/exponential curves
- note quantization to a selectable musical scale and root note

## Project layout

- `app.py` — application entry point and Tkinter window lifecycle
- `input.py` — WebSocket discovery and sensor streaming logic
- `output.py` — MIDI mapping, note quantization, and MIDI message sending
- `settings.py` — shared settings across the application
- `gui/` — Tkinter UI components for connections and control mapping
- `app_data/` — persistent settings and patch data
- `dev/` — data recording/playback dev tools

## Getting started

### Prerequisites

- Python 3.10 or newer
- A compatible Android device running the SensorServer app
- A MIDI output available on your machine, such as:
  - macOS: IAC Driver Bus
  - Windows: loopMIDI or another virtual MIDI driver
- A MIDI-compatible DAW or digital instrument available on your machine
- Access to the same local network as the Android device (can run on mobile hotspot)

### Run the app

```bash
python app.py
```

The GUI will open with a connection panel and control mapping interface. From there you can configure the input device, MIDI output port, and live motion mappings.

## Recommended quick set-up using BandLab

1. Install and start the Android SensorServer app on your device. [https://f-droid.org/packages/github.umer0586.sensorserver/]
2. Ensure the phone and the computer are on the same network.
3. Launch MidiMover and select SensorServer and your chosen MIDI ouput (Connections panel).
4. Open BandLab online studio [https://help.bandlab.com/hc/en-us/articles/115002945153-Getting-Started-with-the-BandLab-Studio] and allow access to your MIDI devices (pop-up).
5. Load a virtual instrument in the BandLab studio (recommended: Percussion > Marimba).
6. Set IAC Driver/loopMIDI as your MIDI device in BandLab [https://help.bandlab.com/hc/en-us/articles/58150962949785-Connecting-MIDI-Devices].
7. Try playing the virtual keyboard inside GarageBand to check your audio connection [https://help.bandlab.com/hc/en-us/articles/56922726115097-Audio-Output-Issues].
8. Start MidiMover and try moving the controller to control the audio output.


## Resources

- SensorServer repository: https://github.com/UmerCodez/SensorServer
- SensorServer app on F-Droid: https://f-droid.org/packages/github.umer0586.sensorserver/
- Virtual MIDI bus setup guide: https://help.ableton.com/hc/en-us/articles/209774225-Setting-up-a-virtual-MIDI-bus
- loopMIDI driver for Windows users: https://www.tobias-erichsen.de/software/loopmidi.html
- BandLab free browser-based DAW: https://www.bandlab.com/


## License

This project is intended for use under the project’s repository license. See the repository metadata for the current license declaration.

