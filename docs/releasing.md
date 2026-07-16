# Release process

HTGDO HomeKit releases are created with the manual **Release HomeKit Firmware**
GitHub Actions workflow.

Use a hardware-linked release tag:

```text
htgdo-v2.2-homekit-N
```

For example:

```text
htgdo-v2.2-homekit-1
```

The workflow must be run from `main`. It builds the PlatformIO firmware, creates
the web installer manifest, deploys the installer to GitHub Pages, and creates a
GitHub Release with the firmware binaries, manifest, checksums, and release
notes.

Release artifacts are not committed back into `docs/firmware/`.
