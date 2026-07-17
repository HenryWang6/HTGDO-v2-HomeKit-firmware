#!/usr/bin/env python3
#
# This script runs patch command on specified files.
#
# Copyright (c) 2024-25 David Kerr, https://github.com/dkerr64
#
import os
import subprocess
from pathlib import Path

Import("env")
#print(env['PROJECT_PACKAGES_DIR']);
#print(env['PROJECT_LIBDEPS_DIR']);

if os.name != "nt":
    target = Path(env["PROJECT_PACKAGES_DIR"]) / (
        "framework-arduinoespressif32/libraries/WebServer/src/WebServer.cpp"
    )
    patch_file = Path(env["PROJECT_DIR"]) / "url_not_found_log.patch"

    # Arduino-ESP32 3.3.8 already contains the former HTGDO patch. Keep this
    # guard so a future framework regression fails the build instead of being
    # silently ignored by a shell return code.
    if 'log_e("request handler not found")' not in target.read_text():
        print("Framework already contains the WebServer not-found logging fix")
    else:
        if not patch_file.is_file():
            raise RuntimeError(
                "Framework needs the WebServer not-found logging patch, but "
                f"the patch file is missing: {patch_file}"
            )

        applied = subprocess.run(
            ["patch", "--forward", "--batch", str(target), str(patch_file)],
            check=False,
        )
        if applied.returncode != 0:
            already_applied = subprocess.run(
                [
                    "patch",
                    "--reverse",
                    "--dry-run",
                    "--batch",
                    str(target),
                    str(patch_file),
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if already_applied.returncode != 0:
                raise RuntimeError(f"Unable to apply framework patch: {patch_file}")
            print(f"Framework patch already applied: {patch_file}")
