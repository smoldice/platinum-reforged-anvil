// The page's side of the Platinum Reforged Anvil: the ROM slots (Platinum, Black 2 or White 2, and HeartGold or
// SoulSilver if the player likes), where to save, the build and its progress.
// Python's side is window.pywebview.api (app.py Api); it calls back window.onProgress, onDone, onError, onDropped.
const $ = (id) => document.getElementById(id);
const state = { platinum: null, gen5: null, hgss: null, out: "", outChosen: false, busy: false };
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
  const remove = el.querySelector(".remove");
  if (remove) remove.hidden = !info;
}

function renderOutput() {
  // The path is shown right to left so a long one loses its start, not its file name; the marks keep its own
  // characters in order (a Linux path's leading / would otherwise show at its end)
  $("output-path").textContent = state.out ? `‎${state.out}‎` : "Choose your Platinum ROM first";
  $("output-path").title = state.out;
  $("change-output").disabled = !state.out;
  // HeartGold or SoulSilver is optional, but a file there must be one
  $("build").disabled = !(state.platinum && state.platinum.ok && state.gen5 && state.gen5.ok && state.out
    && (!state.hgss || state.hgss.ok));
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
  const [lo, hi] = STEP_RANGE[step];
  const percent = Math.round(lo + (hi - lo) * fraction);
  $("bar-fill").style.width = percent + "%";
  $("percent").textContent = percent + "%";
};

// While it works, jokes about what it's doing to the games, in a random order, a new one every few seconds
const QUIPS = [
  "Blowing on the cartridges, just in case…",
  "Pouring Black 2 into Platinum and stirring gently…",
  "Teaching Sinnoh's Pokémon to battle in Unova's style…",
  "Convincing Giratina that Gen V was its idea…",
  "Copying Black 2's homework, changing a few words…",
  "Folding Unova into Sinnoh along the dotted line…",
  "Asking Professor Rowan to sign off on the battle engine…",
  "Shaking the cartridges together until something clicks…",
  "Telling the Black 2 sprites they live in Sinnoh now…",
  "Melting down the old battle screen for scrap…",
  "Smuggling Unova's battle music past Team Galactic…",
  "Sorting the Unown into alphabetical order…",
  "Rotating the Distortion World back the right way up…",
  "Waking up the Snorlax blocking the battle engine…",
  "Hammering out the dents between Gen IV and Gen V…",
  "Polishing the Platinum until it shines…",
];
const QUIP_EVERY = 3500;
let quipTimer = null;
let quipOrder = [];

function nextQuip() {
  if (!quipOrder.length) {
    const last = $("quip").textContent;
    quipOrder = [...QUIPS].sort(() => Math.random() - 0.5);
    if (quipOrder[0] === last) quipOrder.push(quipOrder.shift());
  }
  const el = $("quip");
  el.textContent = quipOrder.shift();
  el.classList.remove("flash");
  void el.offsetWidth; // restarts the animation
  el.classList.add("flash");
}

function startQuips() {
  stopQuips();
  nextQuip();
  quipTimer = setInterval(nextQuip, QUIP_EVERY);
}

function stopQuips() {
  clearInterval(quipTimer);
  quipTimer = null;
}

window.onDone = (result) => {
  state.busy = false;
  stopQuips();
  $("done-name").textContent = result.name;
  $("done-path").textContent = result.path;
  state.lastPath = result.path;
  show("done");
};

window.onError = (message) => {
  state.busy = false;
  stopQuips();
  $("error-text").textContent = message;
  show("error");
};

async function start() {
  if (state.busy || $("build").disabled) return;
  state.busy = true;
  window.onProgress("read", 0);
  show("progress");
  startQuips();
  const started = await api.build(state.platinum.path, state.gen5.path, state.out, state.hgss ? state.hgss.path : "");
  if (!started) state.busy = false;
}

function wire() {
  document.querySelectorAll(".slot .browse:not(.remove)").forEach((button) =>
    button.addEventListener("click", async () => accept(button.dataset.slot, await api.pick_rom(button.dataset.slot))));
  document.querySelectorAll(".slot .remove").forEach((button) =>
    button.addEventListener("click", () => {
      state[button.dataset.slot] = null;
      renderSlot(button.dataset.slot);
      renderOutput();
    }));
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
  renderSlot("hgss");
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
    hgss: { path: "C:\\ROMs\\Pokemon - HeartGold Version (USA).nds", name: "Pokemon - HeartGold Version (USA).nds",
      title: "Pokémon HeartGold Version (USA)", ok: true, problem: "" },
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
      await accept("hgss", await mock.pick_rom("hgss"));
    }
    if (view === "progress") {
      show("progress");
      startQuips();
      window.onProgress("build", 0.62);
    } else if (view === "done") {
      window.onDone({ path: "C:\\ROMs\\Pokemon Platinum Reforged.nds", name: "Pokemon Platinum Reforged.nds",
        sha1: "01dad4cc4bc936725e0f0f6ba1ce15c283d94516" });
    } else if (view === "error") {
      window.onError("Pokémon Black Version 2 (USA, Europe) doesn't match a clean copy of the game (it may be " +
        "modified, or a bad dump). The part that differs: file:a/0/1/1.");
    } else if (view === "bad") {
      await accept("gen5", { path: "C:\\ROMs\\Pokemon - HeartGold.nds", name: "Pokemon - HeartGold.nds",
        title: "Pokémon HeartGold Version (USA)", ok: false,
        problem: "This slot needs Pokémon Black 2 or White 2 (USA, Europe)." });
    }
  });
} else {
  window.addEventListener("pywebviewready", () => init(window.pywebview.api));
}
