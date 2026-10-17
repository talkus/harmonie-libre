/* SOL v0.5: original Python only, isolated browser worker. No voting logic in JS. */
'use strict';
const COMMIT = '112ce958e21a874416b76c4cfa7753019d265ea9';
const BASE = `https://raw.githubusercontent.com/talkus/harmonie-libre/${COMMIT}/conscience-c/sol/v05-global-parity/`;
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/';
const FILES = Object.freeze({
  'sol_parite_equidistance_globale_candidate_v05.py': '044fb876a4f135b001b17b7d876181714dbd39caced93d1e2f9a28a69a3f1024',
  'sol_strat3_parite_equidistance_globale_v0_4.py': '62ed25ccc287d2b2080d501e413ebb135e3107d48a5af1ade9c615c7d7f3df3a',
  'sol_strat3_multiechelle_v0_3_optimized.py': '725edc6e40b72c8ca45fe45a4e7c63719e3ff38d53e37d18ab76e6c63da3e6ba',
  'sol_improvements_v0_4_axes.py': '3c869ba97451bc71f6c8badaa8d8e16298ab8e56a39b67306537183e0745bda3',
  'api/index.py': '792b3cdcb9924508a2e67ae2a8aa7b8f77714d0f300e97b528df00f65c9c8ef9'
});
let runtime = null;
let bootPromise = null;
function log(message) { self.postMessage({type:'progress', message}); }
function hex(buffer) { return [...new Uint8Array(buffer)].map(b=>b.toString(16).padStart(2,'0')).join(''); }
async function boot() {
  if (bootPromise) return bootPromise;
  bootPromise = (async () => {
    if (!self.crypto || !self.crypto.subtle) throw Error('SHA-256 indisponible');
    const root = '/home/pyodide/sol-v05';
    const sources = {};
    for (const [path, sha] of Object.entries(FILES)) {
      log(`Source Python : ${path}`);
      const res = await fetch(BASE + path, {cache:'no-store'});
      if (!res.ok) throw Error(`Téléchargement refusé (${res.status}) : ${path}`);
      const bytes = new Uint8Array(await res.arrayBuffer());
      const got = hex(await crypto.subtle.digest('SHA-256', bytes));
      if (got !== sha) throw Error(`Empreinte SHA-256 incorrecte pour ${path}. Calcul refusé.`);
      sources[path] = bytes;
    }
    log('Intégrité validée ; chargement de Python (WebAssembly)…');
    importScripts(PYODIDE + 'pyodide.js');
    runtime = await self.loadPyodide({indexURL:PYODIDE});
    runtime.FS.mkdirTree(root + '/api');
    for (const [path, bytes] of Object.entries(sources)) runtime.FS.writeFile(root + '/' + path, bytes);
    runtime.FS.writeFile(root + '/api/__init__.py', '');
    const version = await runtime.runPythonAsync(`import sys, hashlib, json\nsys.path.insert(0, ${JSON.stringify(root)})\nfrom api.index import evaluate\nassert hashlib.sha256(open(${JSON.stringify(root + '/sol_parite_equidistance_globale_candidate_v05.py')}, 'rb').read()).hexdigest() == '044fb876a4f135b001b17b7d876181714dbd39caced93d1e2f9a28a69a3f1024'\nsys.version.split()[0]`);
    return {sha256:FILES['sol_parite_equidistance_globale_candidate_v05.py'],commit:COMMIT,python:version,sourceCount:Object.keys(FILES).length};
  })();
  return bootPromise;
}
self.onmessage = async ({data}) => {
  if (data.type === 'init') {
    try {const info = await boot(); self.postMessage({type:'ready',info});}
    catch (error) {self.postMessage({type:'unavailable',message:String(error?.message||error)});}
  } else if (data.type === 'evaluate') {
    const id = data.id;
    if (!runtime) {self.postMessage({type:'result',id,ok:false,error:'Python non initialisé.'});return;}
    try {
      runtime.globals.set('_sol_input_json', JSON.stringify(data.payload));
      const output = await runtime.runPythonAsync(`try:\n  _sol_result_json = json.dumps({'ok': True, 'data': evaluate(json.loads(_sol_input_json))}, ensure_ascii=False, allow_nan=False)\nexcept Exception as _sol_error:\n  _sol_result_json = json.dumps({'ok': False, 'error': str(_sol_error)[:220]}, ensure_ascii=False)\n_sol_result_json`);
      self.postMessage({type:'result',id,...JSON.parse(output)});
    } catch(error) {self.postMessage({type:'result',id,ok:false,error:String(error?.message||error)});}
  }
};
