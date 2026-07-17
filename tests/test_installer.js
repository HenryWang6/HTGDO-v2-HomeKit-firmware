const assert = require("node:assert/strict");
const test = require("node:test");

const installer = require("../docs/installer.js");

const tag = "htgdo-v2-homekit-1";

function manifest() {
    return {
        name: "HTGDO-v2 HomeKit",
        version: tag,
        builds: [
            {
                chipFamily: "ESP32",
                parts: [{ path: `${tag}.factory.bin`, offset: 0 }],
            },
        ],
    };
}

function element() {
    const attributes = new Map();
    return {
        attributes,
        dataset: {},
        hidden: false,
        textContent: "",
        removeAttribute(name) { attributes.delete(name); },
        setAttribute(name, value) { attributes.set(name, value); },
    };
}

test("manifest validation requires one offset-zero ESP32 factory image", () => {
    assert.equal(installer.validateManifest(manifest()).version, tag);

    const wrongOffset = manifest();
    wrongOffset.builds[0].parts[0].offset = 0x1000;
    assert.throws(() => installer.validateManifest(wrongOffset));

    const oldTag = manifest();
    oldTag.version = "htgdo-v2.2-homekit-1";
    assert.throws(() => installer.validateManifest(oldTag));
});

test("only the stable HTGDO-v2 identity is treated as the same firmware", () => {
    assert.equal(
        installer.checkSameFirmware(manifest(), {
            firmware: "htgdo.homekit.v2.esp32",
        }),
        true,
    );
    assert.equal(
        installer.checkSameFirmware(manifest(), { firmware: "HomeKit-ratgdo32" }),
        false,
    );
    assert.equal(
        installer.checkSameFirmware(manifest(), { firmware: "htgdo.esphome" }),
        false,
    );
});

test("successful initialization exposes one validated installer button", async () => {
    const button = element();
    const statusElement = element();
    const versionElement = element();
    const fetchImpl = async () => ({ ok: true, status: 200, json: async () => manifest() });

    await installer.initialize({ fetchImpl, button, statusElement, versionElement });

    assert.equal(button.hidden, false);
    assert.equal(button.attributes.get("manifest"), "manifest.json");
    assert.equal(versionElement.textContent, tag);
    assert.equal(statusElement.dataset.state, "ready");
    assert.equal(
        button.overrides.checkSameFirmware(manifest(), {
            firmware: "htgdo.homekit.v2.esp32",
        }),
        true,
    );
});

test("manifest load failure keeps flashing unavailable", async () => {
    const button = element();
    const statusElement = element();
    const versionElement = element();
    const fetchImpl = async () => ({ ok: false, status: 503 });

    await assert.rejects(
        installer.initialize({ fetchImpl, button, statusElement, versionElement }),
    );
    assert.equal(button.hidden, true);
    assert.equal(button.attributes.has("manifest"), false);
    assert.equal(versionElement.textContent, "Unavailable");
    assert.equal(statusElement.dataset.state, "error");
});
