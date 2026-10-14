// Anvil in a browser: the page's side. In the desktop app, app.js calls Python through window.pywebview.api; here
// the same calls go to the worker (worker.js), which runs Anvil's own Python, and the ROM it makes comes back as a
// download. Loaded before app.js; it marks the page as the web one (body.web) and starts loading Anvil at once.
(() => {
  const worker = new Worker("worker.js", { type: "module" });
  const waiting = new Map();
  let next = 0;
  let chunks = [];
  let rom = null; // the last ROM made, as a Blob, and its name
  let outputName = "Pokemon Platinum Reforged.nds";

  worker.onmessage = ({ data }) => {
    if (data.type === "progress") return window.onProgress(data.step, data.fraction);
    if (data.type === "chunk") return void chunks.push(data.bytes);
    const call = waiting.get(data.id);
    waiting.delete(data.id);
    if (data.error !== undefined) call.reject(new Error(data.error));
    else call.resolve(data.result);
  };
  // A worker that can't start (no module workers, Pyodide unreachable) fails what's waiting on it
  worker.onerror = (e) => {
    for (const call of waiting.values()) call.reject(new Error(e.message || "the worker stopped"));
    waiting.clear();
  };
  const call = (type, args = {}) => new Promise((resolve, reject) => {
    const id = ++next;
    waiting.set(id, { resolve, reject });
    worker.postMessage({ id, type, ...args });
  });

  const ready = call("start").then((info) => {
    outputName = info.output;
    document.body.classList.remove("loading");
    $("hint-line").innerHTML = "Click <b>Choose</b>, or drop the files anywhere on this page.";
    return info;
  });
  ready.catch((e) => {
    $("hint-line").textContent = "Anvil couldn't load in this browser: " + e.message;
  });

  const describe = async (file, slot) => (await ready, call("describe", { file, slot }));
  const place = async (file) => (await ready, call("place", { file }));

  function save() {
    if (!rom) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(rom);
    a.download = outputName;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 60000);
  }

  window.anvilWeb = { describe, place, ready, rom: () => rom };
  window.pywebview = {
    api: {
      info: async () => {
        const info = await ready;
        return { version: info.version, label: info.label };
      },
      pick_rom: (slot) => new Promise((resolve) => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".nds";
        input.onchange = async () => resolve(input.files[0] ? await describe(input.files[0], slot) : null);
        input.click();
      }),
      place: async (file) => place(file),
      default_output: async () => outputName,
      pick_output: async (current) => current,
      build: async (platinum, gen5) => {
        chunks = [];
        rom = null;
        call("build", { platinum, gen5 }).then((result) => {
          if (result.error) return window.onError(result.error);
          window.onProgress("save", 0);
          rom = new Blob(chunks, { type: "application/octet-stream" });
          chunks = [];
          window.onProgress("save", 1);
          window.onDone({ path: "", name: outputName, sha1: result.sha1 });
        }, (e) => window.onError("Something went wrong: " + e.message));
        return true;
      },
      show_in_folder: async () => save(),
    },
  };

  // What differs in a browser: files come from the page (a drop's are File objects, not paths), and the ROM is saved
  // by the browser, to its downloads
  document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("web", "loading");
    $("hint-line").textContent = "Getting Anvil ready… The first time, your browser downloads about 15 MB.";
    document.querySelector(".output-label").textContent = "Saves as";
    $("show-folder").textContent = "Save the ROM";
    document.addEventListener("drop", async (e) => {
      for (const file of e.dataTransfer.files) {
        const placed = await place(file);
        await window.accept(placed.slot, placed.info);
      }
    });
    window.dispatchEvent(new Event("pywebviewready"));
  });
})();
