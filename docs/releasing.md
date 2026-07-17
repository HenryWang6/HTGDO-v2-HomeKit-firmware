# HomeKit release process

HTGDO-v2 HomeKit releases use the manual **Release HomeKit Firmware** workflow. The workflow has two operations and must be run from `main`.

## Version contract

- Tag and full firmware version: `htgdo-v2-homekit-N`
- Stable firmware identity: `htgdo.homekit.v2.esp32`
- Hardware target: `htgdo.v2.esp32`
- Apple Home Firmware Revision: `N.0.0`
- Development builds: `dev` and Apple Home `0.0.0`

Release `htgdo-v2-homekit-1`, for example, embeds the full tag and Apple firmware revision `1.0.0`.

## Publish a prerelease

Run the workflow with:

```text
operation: publish_prerelease
release_tag: htgdo-v2-homekit-1
```

The workflow rejects non-main refs, malformed tags, and existing tags or releases. It builds `htgdo_v2_esp32` once, validates embedded identity and version metadata, checks the OTA image against the app partition, and reconstructs the complete factory image with esptool to verify the offset-zero binary.

It then creates a GitHub prerelease before deploying the matching GitHub Pages installer. Generated artifacts are never committed to `docs/firmware/`.

Assets are fixed to:

```text
htgdo-v2-homekit-N.factory.bin
htgdo-v2-homekit-N.ota.bin
htgdo-v2-homekit-N.ota.md5
htgdo-v2-homekit-N.elf
manifest.json
SHA256SUMS
```

`manifest.json` uses a single ESP32 factory image at offset `0`. `SHA256SUMS` covers every other release asset; the MD5 sidecar is additionally required by device OTA.

The device web UI selects the exact OTA and MD5 asset names from the GitHub
Release API, then downloads the byte-identical Pages copies. GitHub's
release-asset redirects do not permit browser cross-origin reads; Pages supplies
the required CORS header without adding a third-party proxy.

## Validate

Before promotion, verify USB installation, Improv provisioning, Apple Home pairing, device metadata, and OTA from a development build. Compare every GitHub Release and Pages asset, including SHA-256 and OTA MD5 values.

The generic legacy identity `HomeKit-ratgdo32` is intentionally not considered the same HTGDO-v2 firmware. Its first migration requires an explicit erase.

## Promote without rebuilding

After validation, run the workflow again with the same tag:

```text
operation: promote
release_tag: htgdo-v2-homekit-1
```

Promotion downloads and verifies the existing prerelease, checks that its tag and target source commit match, and changes only the prerelease flag. It does not rebuild, retag, redeploy Pages, or replace assets.

Promotion confirms that the public workflow passed. The release remains unsuitable for shipping or pre-flashing until the real-opener gate is recorded separately.
