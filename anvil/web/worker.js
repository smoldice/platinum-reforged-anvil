// Anvil in a browser: the worker that runs Anvil's own Python (Pyodide, from its CDN) away from the page's thread.
// The page sends the player's files as they choose them; each is mounted read-only (Emscripten's WORKERFS), so Python
// reads only the parts it needs, never the whole 512 MB of Black 2. The ROM comes back in pieces, in order, as it's
// made ("chunk"), for the page to put together into the download. Messages: {id, type, ...} in, {id, result} or
// {id, error} out, and {type: "progress"} and {type: "chunk"} as a build goes. A module worker (web.js), which
// imports Pyodide as Pyodide documents it for workers.
const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

let pyodide = null;
let web = null;
let mounts = 0;
const plain = (proxy) => {
  const value = proxy.toJs({ dict_converter: Object.fromEntries });
  proxy.destroy();
  return value;
};

async function start() {
  const { loadPyodide } = await import(PYODIDE + "pyodide.mjs");
  pyodide = await loadPyodide({ indexURL: PYODIDE });
  await pyodide.loadPackage("pillow");
  // Anvil's Python, the converters it runs and its bundle, laid out as in the repo (make_site.py)
  const zip = await (await fetch("anvil.zip")).arrayBuffer();
  pyodide.unpackArchive(zip, "zip", { extractDir: "/anvil" });
  pyodide.runPython("import sys; sys.path.insert(0, '/anvil/anvil')");
  web = pyodide.pyimport("reforged_anvil.web");
  return plain(web.info());
}

function mount(file) {
  const dir = `/roms/${++mounts}`;
  pyodide.FS.mkdirTree(dir);
  pyodide.FS.mount(pyodide.FS.filesystems.WORKERFS, { files: [file] }, dir);
  return `${dir}/${file.name}`;
}

function build({ platinum, gen5, hgss }) {
  const write = (data) => {
    const bytes = data.toJs();
    data.destroy();
    postMessage({ type: "chunk", bytes }, [bytes.buffer]);
  };
  const progress = (step, fraction) => postMessage({ type: "progress", step, fraction });
  return plain(web.build(platinum, gen5, write, progress, hgss || ""));
}

const handlers = {
  start,
  describe: ({ file, slot }) => plain(web.describe_file(mount(file), slot, file.name)),
  place: ({ file }) => plain(web.place_file(mount(file), file.name)),
  build,
};

onmessage = async ({ data }) => {
  try {
    postMessage({ id: data.id, result: await handlers[data.type](data) });
  } catch (e) {
    postMessage({ id: data.id, error: String(e && e.message || e) });
  }
};
