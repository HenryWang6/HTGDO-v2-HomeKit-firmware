# HTGDO HomeKit v2.5 preview

**Pre-release for optional testing.** `htgdo-v2-homekit-5` remains the current stable release. The device updater shows this preview only when **Include pre-releases** is selected.

## What's included

- Automatic obstruction status selection for Security+ openers: opener messages provide status until a connected GPIO4 sensor produces valid pulses, then the sensor input takes priority.
- Motion is added to Apple Home when the opener's motion sensor is first discovered, and remains available after a restart.
- Reliability improvements for Security+ communication, web updates, and live logs.

## Tests completed

- Real Security+ 2.0 opener: door open, stop, close, light control, remote lock, and Apple Home status and controls.
- Obstruction reporting through opener messages and through a connected GPIO4 sensor, including obstructed and clear transitions.
- OTA from release 5 with Wi-Fi settings and Apple Home pairing retained; interrupted upload and update recovery.
- Factory reset, Wi-Fi setup, fresh Apple Home pairing, first Motion discovery and updates, and Motion availability after restart.
- Settings persistence, device-name changes, saved logs, and live log reconnection.
- Automated tests and the HomeKit firmware build in GitHub Actions.

This preview was validated with a Security+ 2.0 opener. Security+ 1.0 opener testing remains on the checklist before a general release.
