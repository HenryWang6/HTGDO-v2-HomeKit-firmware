(function (root, factory) {
    const contract = factory();
    if (typeof module === "object" && module.exports) {
        module.exports = contract;
    }
    root.HTGDORelease = contract;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    const releasePattern = /^htgdo-v2-homekit-([1-9][0-9]*)$/;

    function parseReleaseNumber(version) {
        if (version === "dev") {
            return 0;
        }
        const match = releasePattern.exec(version || "");
        return match ? Number.parseInt(match[1], 10) : null;
    }

    function selectLatestRelease(releases, includePrerelease) {
        return (Array.isArray(releases) ? releases : [])
            .filter((release) => {
                return !release.draft
                    && (includePrerelease || !release.prerelease)
                    && parseReleaseNumber(release.tag_name) !== null;
            })
            .sort((left, right) => {
                return parseReleaseNumber(right.tag_name) - parseReleaseNumber(left.tag_name);
            })[0];
    }

    function selectOtaAssets(release) {
        if (!release || parseReleaseNumber(release.tag_name) === null) {
            return null;
        }
        const otaName = `${release.tag_name}.ota.bin`;
        const md5Name = `${release.tag_name}.ota.md5`;
        const assets = Array.isArray(release.assets) ? release.assets : [];
        const ota = assets.find((asset) => asset.name === otaName);
        const md5 = assets.find((asset) => asset.name === md5Name);
        if (!ota?.browser_download_url || !md5?.browser_download_url) {
            return null;
        }
        return { ota, md5 };
    }

    function isUpdateAvailable(installedVersion, releaseTag) {
        const installed = parseReleaseNumber(installedVersion);
        const available = parseReleaseNumber(releaseTag);
        return installed !== null && available !== null && available > installed;
    }

    return {
        isUpdateAvailable,
        parseReleaseNumber,
        releasePattern,
        selectLatestRelease,
        selectOtaAssets,
    };
});
