// The page's side of the Platinum Reforged Anvil: the two ROM slots, where to save, the build and its progress.
// Python's side is window.pywebview.api (app.py Api); it calls back window.onProgress, onDone, onError, onDropped.
const $ = (id) => document.getElementById(id);
const state = { platinum: null, gen5: null, out: "", outChosen: false, busy: false };
let api = null;

function show(view) {
  for (const id of ["setup", "progress", "done", "error"]) $(id).hidden = id !== view;
}

function toast(text) {
  const el = $("toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.hidden = true), 3200);
}

function renderSlot(slot) {
  const el = $("slot-" + slot);
  const info = state[slot];
  el.classList.toggle("ok", !!info && info.ok);
  el.classList.toggle("bad", !!info && !info.ok);
  el.querySelector(".file-title").textContent = info ? (info.ok ? info.title : `${info.title} — ${info.problem}`) : "";
  el.querySelector(".file-name").textContent = info ? info.name : "";
  el.querySelector(".browse").textContent = info ? "Change…" : "Choose…";
}

function renderOutput() {
  // The path is shown right to left so a long one loses its start, not its file name; the marks keep its own
  // characters in order (a Linux path's leading / would otherwise show at its end)
  $("output-path").textContent = state.out ? `‎${state.out}‎` : "Choose your Platinum ROM first";
  $("output-path").title = state.out;
  $("change-output").disabled = !state.out;
  $("build").disabled = !(state.platinum && state.platinum.ok && state.gen5 && state.gen5.ok && state.out);
}

async function accept(slot, info) {
  if (!info) return;
  state[slot] = info;
  renderSlot(slot);
  if (slot === "platinum" && info.ok && !state.outChosen) state.out = await api.default_output(info.path);
  renderOutput();
}

window.onDropped = async (path) => {
  const placed = await api.place(path);
  if (placed) await accept(placed.slot, placed.info);
};

// By the time each step takes: making the sprites about 15 s, putting the ROM together about 8 s
const STEP_RANGE = { read: [0, 3], make: [3, 63], build: [63, 96], save: [96, 100] };
window.onProgress = (step, fraction) => {
  const order = ["read", "make", "build", "save"];
  document.querySelectorAll(".steps li").forEach((li) => {
    const i = order.indexOf(li.dataset.step), current = order.indexOf(step);
    li.classList.toggle("done", i < current || (i === current && fraction >= 1));
    li.classList.toggle("active", i === current && fraction < 1);
  });
  const [lo, hi] = STEP_RANGE[step];
  const percent = Math.round(lo + (hi - lo) * fraction);
  $("bar-fill").style.width = percent + "%";
  $("percent").textContent = percent + "%";
};

window.onDone = (result) => {
  state.busy = false;
  $("done-name").textContent = result.name;
  $("done-path").textContent = result.path;
  state.lastPath = result.path;
  show("done");
};

window.onError = (message) => {
  state.busy = false;
  $("error-text").textContent = message;
  show("error");
};

async function start() {
  if (state.busy || $("build").disabled) return;
  state.busy = true;
  window.onProgress("read", 0);
  show("progress");
  const started = await api.build(state.platinum.path, state.gen5.path, state.out);
  if (!started) state.busy = false;
}

function wire() {
  document.querySelectorAll(".slot .browse").forEach((button) =>
    button.addEventListener("click", async () => accept(button.dataset.slot, await api.pick_rom(button.dataset.slot))));
  $("change-output").addEventListener("click", async () => {
    const path = await api.pick_output(state.out);
    if (path) {
      state.out = path;
      state.outChosen = true;
      renderOutput();
    }
  });
  $("build").addEventListener("click", start);
  $("show-folder").addEventListener("click", () => api.show_in_folder(state.lastPath));
  $("again").addEventListener("click", () => show("setup"));
  $("back").addEventListener("click", () => show("setup"));

  // Dropped files: the window takes them (app.py reads their paths), a slot shows where
  let over = null;
  const mark = (slot) => {
    if (over === slot) return;
    over = slot;
    document.querySelectorAll(".slot").forEach((el) => el.classList.toggle("drag", el.dataset.slot === slot));
  };
  document.addEventListener("dragover", (e) => {
    e.preventDefault();
    const slot = e.target.closest && e.target.closest(".slot");
    mark(slot ? slot.dataset.slot : null);
  });
  document.addEventListener("dragleave", (e) => { if (!e.relatedTarget) mark(null); });
  document.addEventListener("drop", (e) => { e.preventDefault(); mark(null); });
}

async function init(theApi) {
  api = theApi;
  wire();
  renderSlot("platinum");
  renderSlot("gen5");
  renderOutput();
  const info = await api.info();
  $("version").textContent = `Version ${info.version}${info.label ? " · " + info.label : ""}`;
}

// A stand-in for Python's side, to look at the page in a browser: index.html?mock
function mockApi() {
  const roms = {
    platinum: { path: "C:\\ROMs\\Pokemon - Platinum Version (USA).nds", name: "Pokemon - Platinum Version (USA).nds",
      title: "Pokémon Platinum (USA)", ok: true, problem: "" },
    gen5: { path: "C:\\ROMs\\Pokemon - Black Version 2 (USA, Europe).nds", name: "Pokemon - Black Version 2 (USA, Europe).nds",
      title: "Pokémon Black Version 2 (USA, Europe)", ok: true, problem: "" },
  };
  return {
    info: async () => ({ version: "1.0.0", label: "preview" }),
    pick_rom: async (slot) => roms[slot],
    place: async () => ({ slot: "platinum", info: roms.platinum }),
    default_output: async () => "C:\\ROMs\\Pokemon Platinum Reforged.nds",
    pick_output: async (p) => p,
    build: async () => {
      let t = 0;
      const tick = setInterval(() => {
        t += 0.05;
        if (t < 0.1) window.onProgress("read", t / 0.1);
        else if (t < 0.6) window.onProgress("make", (t - 0.1) / 0.5);
        else if (t < 0.9) window.onProgress("build", (t - 0.6) / 0.3);
        else if (t < 1) window.onProgress("save", (t - 0.9) / 0.1);
        else {
          clearInterval(tick);
          window.onDone({ path: "C:\\ROMs\\Pokemon Platinum Reforged.nds", name: "Pokemon Platinum Reforged.nds",
            sha1: "01dad4cc4bc936725e0f0f6ba1ce15c283d94516" });
        }
      }, 120);
      return true;
    },
    show_in_folder: async () => toast("Opens the folder"),
  };
}

if (location.search.includes("mock")) {
  // ?mock&view=filled|progress|done|error shows that state at once
  window.addEventListener("DOMContentLoaded", async () => {
    const mock = mockApi();
    await init(mock);
    const view = new URLSearchParams(location.search).get("view");
    if (view && view !== "setup") {
      await accept("platinum", await mock.pick_rom("platinum"));
      await accept("gen5", await mock.pick_rom("gen5"));
    }
    if (view === "progress") {
      show("progress");
      window.onProgress("build", 0.62);
    } else if (view === "done") {
      window.onDone({ path: "C:\\ROMs\\Pokemon Platinum Reforged.nds", name: "Pokemon Platinum Reforged.nds",
        sha1: "01dad4cc4bc936725e0f0f6ba1ce15c283d94516" });
    } else if (view === "error") {
      window.onError("Pokémon Black Version 2 (USA, Europe) doesn't match a clean copy of the game (it may be " +
        "modified, or a bad dump). The part that differs: file:a/0/1/1.");
    } else if (view === "bad") {
      await accept("gen5", { path: "C:\\ROMs\\Pokemon - HeartGold.nds", name: "Pokemon - HeartGold.nds",
        title: "Pokémon HeartGold (USA)", ok: false,
        problem: "This slot needs Pokémon Black 2 or White 2 (USA, Europe)." });
    }
  });
} else {
  window.addEventListener("pywebviewready", () => init(window.pywebview.api));
}
