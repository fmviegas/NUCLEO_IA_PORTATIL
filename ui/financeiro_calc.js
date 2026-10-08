/* financeiro_calc.js — cálculo AO VIVO do módulo Financeiro no painel.
   Espelho de app/financeiro_dados.py::calcular (que espelha as fórmulas da planilha).
   tools/testar_financeiro_modulo.py confere Python × Excel; tools/testar_financeiro_js.js
   confere este arquivo × Python. Mude os três juntos. */
(function (raiz) {
  const r2 = (x) => Math.round((x + Number.EPSILON) * 100) / 100;
  const soma = (a) => a.reduce((s, x) => s + (Number(x) || 0), 0);

  function calcular(d) {
    const meses = [];
    let saldoAnt = null, investido = 0;
    d.meses.forEach((m, i) => {
      const u5 = r2(soma(m.entradas.map(l => l.valor)));
      const u6 = r2(soma(m.saidas.map(l => l.valor)));
      const u7 = r2(u5 - u6);
      const u8 = Number(m.investimento) || 0;
      const u9 = i === 0 ? (Number(m.saldo_inicial) || 0) : saldoAnt;
      const u10 = r2((u7 + u9) - u8);
      saldoAnt = u10;
      investido = r2(investido + u8);
      meses.push({
        entradas: u5, saidas: u6, diferenca: u7, investimento: u8,
        saldo_anterior: r2(u9), saldo_global: u10, investido_acumulado: investido,
        pct_entradas: m.entradas.map(l => u5 ? (Number(l.valor) || 0) / u5 : null),
        pct_saidas: m.saidas.map(l => u6 ? (Number(l.valor) || 0) / u6 : null),
        a_pagar: r2(soma(m.saidas.filter(l => l.pago === "Não").map(l => l.valor))),
        a_receber: r2(soma(m.entradas.filter(l => l.recebido === "Não").map(l => l.valor))),
      });
    });
    const tot = {};
    for (const k of ["entradas", "saidas", "diferenca", "investimento"]) tot[k] = r2(soma(meses.map(m => m[k])));
    const cartaoLinhas = d.cartao.map(c => {
      const total = r2(soma(c.meses));
      const vt = Number(c.valor_total) || 0;
      return { total, confere: !vt ? null : (Math.abs(vt - total) < 0.005 ? "OK" : r2(vt - total)) };
    });
    const cartaoMeses = [...Array(12).keys()].map(k => r2(soma(d.cartao.map(c => c.meses[k]))));
    const contas = d.contas.map(c => {
      let ant = Number(c.saldo_inicial) || 0;
      return c.meses.map(mm => {
        const liq = r2((ant + (Number(mm.entrada) || 0)) - (Number(mm.saida) || 0));
        const linha = { saldo_anterior: r2(ant), liquido: liq };
        ant = liq;
        return linha;
      });
    });
    return {
      meses, totais: tot, saldo_final: meses[11].saldo_global,
      cartao: { linhas: cartaoLinhas, meses: cartaoMeses, total: r2(soma(cartaoMeses)),
                divergentes: cartaoLinhas.filter(l => l.confere !== null && l.confere !== "OK").length },
      contas,
    };
  }

  const api = { calcular };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.FinCalc = api;
})(typeof window !== "undefined" ? window : globalThis);
