import os
import sys
from pathlib import Path

Import("env")

project_dir = Path(env.subst("$PROJECT_DIR")).resolve()
sys.path.insert(0, str(project_dir))
from scripts.release_version import resolve_versions


versions = resolve_versions(os.environ.get("HTGDO_RELEASE_TAG"))
print(f"Firmware Version: {versions.release}")
print(f"HomeKit Firmware Revision: {versions.hap}")

env.Append(
    BUILD_FLAGS=[
        f'-D AUTO_VERSION=\\"{versions.release}\\"',
        f'-D HAP_FIRMWARE_VERSION=\\"{versions.hap}\\"',
    ]
)
