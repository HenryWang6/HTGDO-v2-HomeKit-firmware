"""Create and verify HTGDO-v2 HomeKit release assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.release_version import resolve_versions


MANIFEST_NAME = "HTGDO-v2 HomeKit"
FIRMWARE_IDENTITY = "htgdo.homekit.v2.esp32"
HARDWARE_TARGET = "htgdo.v2.esp32"
MODEL_NAME = "HTGDO-v2.2"
CHIP_FAMILY = "ESP32"


def asset_names(tag: str) -> dict[str, str]:
    """Return the complete public asset contract for a release tag."""

    resolve_versions(tag)
    return {
        "factory": f"{tag}.factory.bin",
        "ota": f"{tag}.ota.bin",
        "md5": f"{tag}.ota.md5",
        "elf": f"{tag}.elf",
        "manifest": "manifest.json",
        "checksums": "SHA256SUMS",
    }


def build_manifest(tag: str) -> dict[str, object]:
    """Build the ESP Web Tools manifest using only standard fields."""

    names = asset_names(tag)
    return {
        "name": MANIFEST_NAME,
        "version": tag,
        "builds": [
            {
                "chipFamily": CHIP_FAMILY,
                "parts": [{"path": names["factory"], "offset": 0}],
            }
        ],
    }


def validate_manifest(manifest: object, tag: str) -> None:
    """Require the exact customer-facing manifest contract."""

    expected = build_manifest(tag)
    if manifest != expected:
        raise ValueError("manifest does not match the HTGDO-v2 HomeKit contract")


def ota_partition_size(partitions_path: Path) -> int:
    """Return the app0 OTA partition size from a PlatformIO CSV file."""

    with partitions_path.open(newline="") as handle:
        rows = csv.reader(line for line in handle if not line.lstrip().startswith("#"))
        for row in rows:
            fields = [field.strip() for field in row]
            if fields and fields[0] == "app0":
                return int(fields[4], 0)
    raise ValueError("app0 partition was not found")


def verify_build(
    elf_path: Path, ota_path: Path, partitions_path: Path, tag: str
) -> dict[str, int]:
    """Verify embedded identity/version metadata and OTA capacity."""

    versions = resolve_versions(tag)
    elf = elf_path.read_bytes()
    required = (
        FIRMWARE_IDENTITY,
        HARDWARE_TARGET,
        MODEL_NAME,
        versions.release,
        versions.hap,
    )
    missing = [value for value in required if value.encode() not in elf]
    if missing:
        raise ValueError(f"release ELF is missing metadata: {', '.join(missing)}")

    ota_size = ota_path.stat().st_size
    partition_size = ota_partition_size(partitions_path)
    if ota_size > partition_size:
        raise ValueError(
            f"OTA image is too large: {ota_size} bytes > {partition_size} bytes"
        )
    return {"ota_size": ota_size, "partition_size": partition_size}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_release(build_dir: Path, output_dir: Path, tag: str) -> None:
    """Copy PlatformIO outputs and generate manifest and checksum sidecars."""

    names = asset_names(tag)
    output_dir.mkdir(parents=True, exist_ok=False)
    sources = {
        "factory": build_dir / "firmware.factory.bin",
        "ota": build_dir / "firmware.bin",
        "elf": build_dir / "firmware.elf",
    }
    for key, source in sources.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, output_dir / names[key])

    (output_dir / names["md5"]).write_text(
        f"{_md5(output_dir / names['ota'])}\n"
    )
    (output_dir / names["manifest"]).write_text(
        json.dumps(build_manifest(tag), indent=2) + "\n"
    )

    checksummed = sorted(
        name for key, name in names.items() if key != "checksums"
    )
    lines = [f"{_sha256(output_dir / name)}  {name}" for name in checksummed]
    (output_dir / names["checksums"]).write_text("\n".join(lines) + "\n")


def verify_release(directory: Path, tag: str) -> None:
    """Verify exact filenames, SHA-256 values, MD5, and manifest contents."""

    names = asset_names(tag)
    expected_files = set(names.values())
    actual_files = {path.name for path in directory.iterdir() if path.is_file()}
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        extra = sorted(actual_files - expected_files)
        raise ValueError(f"release asset mismatch; missing={missing}, extra={extra}")

    checksum_lines = (directory / names["checksums"]).read_text().splitlines()
    expected_checksum_files = expected_files - {names["checksums"]}
    found_checksum_files: set[str] = set()
    for line in checksum_lines:
        digest, separator, filename = line.partition("  ")
        if not separator or filename not in expected_checksum_files:
            raise ValueError(f"invalid SHA256SUMS line: {line}")
        if filename in found_checksum_files:
            raise ValueError(f"duplicate SHA256SUMS entry: {filename}")
        if digest != _sha256(directory / filename):
            raise ValueError(f"SHA-256 mismatch: {filename}")
        found_checksum_files.add(filename)
    if found_checksum_files != expected_checksum_files:
        raise ValueError("SHA256SUMS does not cover every release asset")

    expected_md5 = (directory / names["md5"]).read_text().strip().lower()
    if expected_md5 != _md5(directory / names["ota"]):
        raise ValueError("OTA MD5 mismatch")

    manifest = json.loads((directory / names["manifest"]).read_text())
    validate_manifest(manifest, tag)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--build-dir", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--tag", required=True)

    build = subparsers.add_parser("verify-build")
    build.add_argument("--elf", type=Path, required=True)
    build.add_argument("--ota", type=Path, required=True)
    build.add_argument("--partitions", type=Path, required=True)
    build.add_argument("--tag", required=True)

    release = subparsers.add_parser("verify-release")
    release.add_argument("--directory", type=Path, required=True)
    release.add_argument("--tag", required=True)

    args = parser.parse_args()
    if args.command == "prepare":
        prepare_release(args.build_dir, args.output_dir, args.tag)
    elif args.command == "verify-build":
        result = verify_build(args.elf, args.ota, args.partitions, args.tag)
        print(json.dumps(result, sort_keys=True))
    else:
        verify_release(args.directory, args.tag)


if __name__ == "__main__":
    main()
