from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProductContractTests(unittest.TestCase):
    def test_shipping_environment_is_explicit_and_not_disco(self):
        platformio = (ROOT / "platformio.ini").read_text()
        shipping = platformio.split("[env:htgdo_v2_esp32]", 1)[1].split(
            "[env:ratgdo_esp32dev]", 1
        )[0]

        self.assertIn("extends = esp32_common", shipping)
        self.assertIn("-D HTGDO_V2", shipping)
        self.assertNotIn("RATGDO32_DISCO", shipping)
        self.assertNotIn("VL53L4CX", shipping)
        self.assertIn("55.03.38/platform-espressif32.zip", platformio)
        self.assertIn("6a1423137d798b856bda5f22dd222abfcd1131ee", platformio)
        self.assertIn("27f1c5075413f48776dffbc47cb954a9d2761ff4", platformio)

    def test_htgdo_identity_and_hap_metadata_are_single_sourced(self):
        ratgdo = (ROOT / "src/ratgdo.h").read_text()
        homekit = (ROOT / "src/homekit.cpp").read_text()
        provision = (ROOT / "src/provision.cpp").read_text()
        ratgdo_cpp = (ROOT / "src/ratgdo.cpp").read_text()
        serial_cli = (ROOT / "src/serialCLI.cpp").read_text()

        self.assertIn('FIRMWARE_IDENTITY "htgdo.homekit.v2.esp32"', ratgdo)
        self.assertIn('HARDWARE_TARGET "htgdo.v2.esp32"', ratgdo)
        self.assertIn('MANUF_NAME "HTGDO"', ratgdo)
        self.assertIn('MODEL_NAME "HTGDO-v2.2"', ratgdo)
        self.assertIn('HARDWARE_REVISION "2.2"', ratgdo)
        self.assertIn("Characteristic::Manufacturer(MANUF_NAME)", homekit)
        self.assertIn("Characteristic::Model(MODEL_NAME)", homekit)
        self.assertIn(
            "Characteristic::FirmwareRevision(HAP_FIRMWARE_VERSION)", homekit
        )
        self.assertIn("FIRMWARE_IDENTITY", provision)
        self.assertIn('"=== Starting %s version %s"', ratgdo_cpp)
        self.assertIn("FIRMWARE_IDENTITY, AUTO_VERSION", ratgdo_cpp)
        self.assertIn("Firmware identity:", serial_cli)
        self.assertIn("Hardware target:", serial_cli)

    def test_ci_runs_tests_and_only_builds_shipping_target(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()

        self.assertIn("submodules: recursive", workflow)
        self.assertIn("name: Run tests", workflow)
        self.assertIn("pio run -e htgdo_v2_esp32", workflow)
        self.assertNotIn("pio run -e ratgdo_esp32dev", workflow)
        self.assertNotIn("upload-artifact", workflow)

    def test_framework_patch_fails_closed(self):
        patch_script = (ROOT / "patch_files.py").read_text()

        self.assertIn("subprocess.run", patch_script)
        self.assertIn("raise RuntimeError", patch_script)
        self.assertNotIn("os.system", patch_script)

    def test_device_ota_uses_fork_release_assets_and_required_md5(self):
        web = (ROOT / "src/web.cpp").read_text()
        functions = (ROOT / "src/www/functions.js").read_text()

        self.assertIn('JSON_ADD_STR("gitUser", gitUser)', web)
        self.assertIn("assets.ota.browser_download_url", functions)
        self.assertIn("assets.md5.browser_download_url", functions)
        self.assertIn("Firmware MD5 checksum URL is missing", functions)
        self.assertNotIn("https://ratgdo.github.io/", functions)
        self.assertNotIn("serverStatus.firmwareVersion < latest.tag_name", functions)

    def test_exact_release_version_fits_crash_diagnostics(self):
        log = (ROOT / "src/log.cpp").read_text()

        self.assertIn("char crashVersion[32]", log)
        self.assertIn('addr2line -p -f -C -e %s.elf', log)


if __name__ == "__main__":
    unittest.main()
