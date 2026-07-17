(function (root, factory) {
    const installer = factory();
    if (typeof module === "object" && module.exports) {
        module.exports = installer;
    }
    root.HTGDOInstaller = installer;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    const manifestName = "HTGDO-v2 HomeKit";
    const firmwareIdentity = "htgdo.homekit.v2.esp32";
    const releasePattern = /^htgdo-v2-homekit-([1-9][0-9]*)$/;

    function validateManifest(manifest) {
        if (!manifest || manifest.name !== manifestName) {
            throw new Error("Unexpected firmware name");
        }
        if (!releasePattern.test(manifest.version || "")) {
            throw new Error("Invalid release version");
        }
        if (!Array.isArray(manifest.builds) || manifest.builds.length !== 1) {
            throw new Error("Expected one ESP32 build");
        }
        const build = manifest.builds[0];
        const expectedPath = `${manifest.version}.factory.bin`;
        if (build.chipFamily !== "ESP32"
            || !Array.isArray(build.parts)
            || build.parts.length !== 1
            || build.parts[0].offset !== 0
            || build.parts[0].path !== expectedPath) {
            throw new Error("Invalid ESP32 factory image mapping");
        }
        return manifest;
    }

    function checkSameFirmware(manifest, improvInfo) {
        return manifest?.name === manifestName
            && improvInfo?.firmware === firmwareIdentity;
    }

    async function initialize({ fetchImpl, button, statusElement, versionElement }) {
        button.hidden = true;
        button.removeAttribute("manifest");
        statusElement.dataset.state = "loading";
        statusElement.textContent = "Loading release information…";
        versionElement.textContent = "Loading…";
        try {
            const response = await fetchImpl("manifest.json", { cache: "no-store" });
            if (!response.ok) {
                throw new Error(`Manifest returned HTTP ${response.status}`);
            }
            const manifest = validateManifest(await response.json());
            button.overrides = { checkSameFirmware };
            button.setAttribute("manifest", "manifest.json");
            button.hidden = false;
            versionElement.textContent = manifest.version;
            statusElement.dataset.state = "ready";
            statusElement.textContent = "Connect the board by USB to install or update.";
            return manifest;
        } catch (error) {
            button.hidden = true;
            button.removeAttribute("manifest");
            versionElement.textContent = "Unavailable";
            statusElement.dataset.state = "error";
            statusElement.textContent = "Installer is unavailable. Please try again later.";
            throw error;
        }
    }

    return {
        checkSameFirmware,
        firmwareIdentity,
        initialize,
        manifestName,
        releasePattern,
        validateManifest,
    };
});
