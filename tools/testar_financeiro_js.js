// testar_financeiro_js.js — confere ui/financeiro_calc.js × app/financeiro_dados.py::calcular.
// Uso: node tools/testar_financeiro_js.js <dados.json> <calc_python.json>
const fs = require("fs");
const { calcular } = require("../ui/financeiro_calc.js");
const dados = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const py = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const js = calcular(dados);
const dif = [];
(function cmp(a, b, cam) {
  if (typeof a === "number" && typeof b === "number") { if (Math.abs(a - b) > 0.005) dif.push(`${cam}: js=${a} py=${b}`); return; }
  if (a === null || b === null || typeof a !== "object") { if (a !== b) dif.push(`${cam}: js=${a} py=${b}`); return; }
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) cmp(a[k], b[k], `${cam}.${k}`);
})(js, py, "calc");
console.log(dif.length ? "DIFERENCAS:\n" + dif.slice(0, 10).join("\n") : "JS = Python (todas as chaves)");
process.exit(dif.length ? 1 : 0);
