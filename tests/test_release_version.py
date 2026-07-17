import unittest

from scripts.release_version import resolve_versions


class ReleaseVersionTests(unittest.TestCase):
    def test_dev_is_the_default_contract(self):
        self.assertEqual(resolve_versions(None).release, "dev")
        self.assertEqual(resolve_versions("").hap, "0.0.0")
        self.assertEqual(resolve_versions("dev").hap, "0.0.0")

    def test_release_number_maps_to_hap_version(self):
        versions = resolve_versions("htgdo-v2-homekit-1")
        self.assertEqual(versions.release, "htgdo-v2-homekit-1")
        self.assertEqual(versions.hap, "1.0.0")

        self.assertEqual(
            resolve_versions("htgdo-v2-homekit-15").hap,
            "15.0.0",
        )

    def test_invalid_release_tags_are_rejected(self):
        invalid_tags = (
            "htgdo-v2.2-homekit-1",
            "htgdo-v2-homekit-0",
            "htgdo-v3-homekit-1",
            "v1",
            "1.0.0",
        )
        for tag in invalid_tags:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                resolve_versions(tag)


if __name__ == "__main__":
    unittest.main()
