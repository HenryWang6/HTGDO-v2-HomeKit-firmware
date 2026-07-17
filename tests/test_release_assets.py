import json
from pathlib import Path
import tempfile
import unittest

from scripts.release_assets import (
    FIRMWARE_IDENTITY,
    HARDWARE_TARGET,
    MODEL_NAME,
    asset_names,
    build_manifest,
    prepare_release,
    validate_manifest,
    verify_build,
    verify_release,
)


TAG = "htgdo-v2-homekit-1"


class ReleaseAssetTests(unittest.TestCase):
    def test_manifest_uses_standard_fields_and_factory_offset_zero(self):
        manifest = build_manifest(TAG)

        self.assertEqual(set(manifest), {"name", "version", "builds"})
        self.assertEqual(manifest["name"], "HTGDO-v2 HomeKit")
        self.assertEqual(manifest["version"], TAG)
        self.assertEqual(manifest["builds"][0]["chipFamily"], "ESP32")
        self.assertEqual(
            manifest["builds"][0]["parts"],
            [{"path": f"{TAG}.factory.bin", "offset": 0}],
        )

    def test_manifest_rejects_nonstandard_or_wrong_release_data(self):
        manifest = build_manifest(TAG)
        manifest["new_install_skip_erase"] = True
        with self.assertRaises(ValueError):
            validate_manifest(manifest, TAG)

        with self.assertRaises(ValueError):
            validate_manifest(build_manifest(TAG), "htgdo-v2-homekit-2")

    def test_prepare_and_verify_exact_release_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_dir = root / "build"
            output_dir = root / "release"
            build_dir.mkdir()
            (build_dir / "firmware.factory.bin").write_bytes(b"factory")
            (build_dir / "firmware.bin").write_bytes(b"ota")
            (build_dir / "firmware.elf").write_bytes(b"elf")

            prepare_release(build_dir, output_dir, TAG)
            verify_release(output_dir, TAG)

            self.assertEqual(
                {path.name for path in output_dir.iterdir()},
                set(asset_names(TAG).values()),
            )
            self.assertEqual(
                json.loads((output_dir / "manifest.json").read_text()),
                build_manifest(TAG),
            )

            (output_dir / asset_names(TAG)["ota"]).write_bytes(b"changed")
            with self.assertRaises(ValueError):
                verify_release(output_dir, TAG)

    def test_verify_build_checks_metadata_and_partition_capacity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            elf = root / "firmware.elf"
            ota = root / "firmware.bin"
            partitions = root / "partitions.csv"
            elf.write_bytes(
                "\0".join(
                    (
                        FIRMWARE_IDENTITY,
                        HARDWARE_TARGET,
                        MODEL_NAME,
                        TAG,
                        "1.0.0",
                    )
                ).encode()
            )
            ota.write_bytes(b"ota")
            partitions.write_text("app0,app,ota_0,0x10000,0x1000,\n")

            self.assertEqual(verify_build(elf, ota, partitions, TAG)["ota_size"], 3)

            ota.write_bytes(b"x" * 0x1001)
            with self.assertRaises(ValueError):
                verify_build(elf, ota, partitions, TAG)


if __name__ == "__main__":
    unittest.main()
