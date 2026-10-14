// For testing the build page on this machine only (make_site.py --dev, served by serve.py): anvilDev.load(slot, name)
// puts a ROM from "original nds roms" in a slot, as choosing it would; anvilDev.last is what the last build gave.
// Never deployed.
if (["127.0.0.1", "localhost"].includes(location.hostname)) {
  window.anvilDev = {
    last: null,
    async load(slot, name) {
      const blob = await (await fetch("/dev-roms/" + encodeURIComponent(name))).blob();
      const info = await window.anvilWeb.describe(new File([blob], name), slot);
      await window.accept(slot, info);
      return info;
    },
  };
  document.addEventListener("DOMContentLoaded", () => {
    const done = window.onDone, error = window.onError;
    window.onDone = async (result) => {
      done(result);
      // The ROM as the page put it together, for the download, checked as the build checked what it made
      const rom = window.anvilWeb.rom();
      const digest = await crypto.subtle.digest("SHA-1", await rom.arrayBuffer());
      const sha1 = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
      window.anvilDev.last = { ...result, at: performance.now(), download: { size: rom.size, sha1 } };
    };
    window.onError = (message) => { window.anvilDev.last = { error: message }; error(message); };
  });
}
