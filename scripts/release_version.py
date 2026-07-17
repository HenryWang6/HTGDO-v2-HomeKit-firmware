"""Validate HTGDO HomeKit release tags and derive HomeKit metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass


RELEASE_TAG_PATTERN = re.compile(r"^htgdo-v2-homekit-([1-9][0-9]*)$")


@dataclass(frozen=True)
class FirmwareVersions:
    release: str
    hap: str


def resolve_versions(release_tag: str | None) -> FirmwareVersions:
    """Return the public and HAP versions for a dev or release build."""

    if not release_tag or release_tag == "dev":
        return FirmwareVersions(release="dev", hap="0.0.0")

    match = RELEASE_TAG_PATTERN.fullmatch(release_tag)
    if not match:
        raise ValueError(
            "release tag must match htgdo-v2-homekit-N with N greater than zero"
        )

    release_number = int(match.group(1))
    return FirmwareVersions(release=release_tag, hap=f"{release_number}.0.0")
