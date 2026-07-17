const assert = require("node:assert/strict");
const test = require("node:test");

const contract = require("../src/www/release-contract.js");

function release(tag, { prerelease = false, draft = false, complete = true } = {}) {
    const assets = complete
        ? [
            { name: `${tag}.ota.bin`, browser_download_url: `https://example/${tag}.bin` },
            { name: `${tag}.ota.md5`, browser_download_url: `https://example/${tag}.md5` },
        ]
        : [{ name: `${tag}.ota.bin`, browser_download_url: `https://example/${tag}.bin` }];
    return { tag_name: tag, prerelease, draft, assets };
}

test("release numbers are numeric and dev sorts below release 1", () => {
    assert.equal(contract.parseReleaseNumber("dev"), 0);
    assert.equal(contract.parseReleaseNumber("htgdo-v2-homekit-10"), 10);
    assert.equal(contract.parseReleaseNumber("htgdo-v2.2-homekit-1"), null);
    assert.equal(contract.isUpdateAvailable("dev", "htgdo-v2-homekit-1"), true);
    assert.equal(
        contract.isUpdateAvailable("htgdo-v2-homekit-10", "htgdo-v2-homekit-2"),
        false,
    );
});

test("stable selection ignores drafts, prereleases, and unrelated tags", () => {
    const selected = contract.selectLatestRelease([
        release("htgdo-v2-homekit-2", { prerelease: true }),
        release("htgdo-v2.2-homekit-99"),
        release("htgdo-v2-homekit-3", { draft: true }),
        release("htgdo-v2-homekit-1"),
    ], false);

    assert.equal(selected.tag_name, "htgdo-v2-homekit-1");
});

test("prerelease selection uses the highest numeric release", () => {
    const selected = contract.selectLatestRelease([
        release("htgdo-v2-homekit-2", { prerelease: true }),
        release("htgdo-v2-homekit-10", { prerelease: true }),
        release("htgdo-v2-homekit-9"),
    ], true);

    assert.equal(selected.tag_name, "htgdo-v2-homekit-10");
});

test("OTA selection requires exact bin and MD5 asset names", () => {
    const complete = release("htgdo-v2-homekit-1");
    const assets = contract.selectOtaAssets(complete);
    assert.equal(assets.ota.name, "htgdo-v2-homekit-1.ota.bin");
    assert.equal(assets.md5.name, "htgdo-v2-homekit-1.ota.md5");

    assert.equal(
        contract.selectOtaAssets(release("htgdo-v2-homekit-1", { complete: false })),
        null,
    );
});

test("browser OTA downloads use the CORS-enabled Pages copies", () => {
    const taggedRelease = release("htgdo-v2-homekit-1");
    assert.deepEqual(
        contract.otaDownloadUrls(taggedRelease, "HenryWang6", "HTGDO-v2-HomeKit-firmware"),
        {
            ota: "https://HenryWang6.github.io/HTGDO-v2-HomeKit-firmware/htgdo-v2-homekit-1.ota.bin",
            md5: "https://HenryWang6.github.io/HTGDO-v2-HomeKit-firmware/htgdo-v2-homekit-1.ota.md5",
        },
    );
    assert.equal(contract.otaDownloadUrls(null, "HenryWang6", "repo"), null);
});
