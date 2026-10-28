// @ts-nocheck
// ─────────────────────────────────────────────────────────────────────────────
// Forja de Prompts — gerador de prompts de IA (React + TypeScript) — tema claro
// 34 estilos · combinação · storyboard · carrossel · timelapse/UGC fatiados ·
// cena de filme/desenho (com personagens) · engenharia reversa · livro de colorir
//
// Requisitos: React 18+ e Tailwind CSS configurados no projeto.
//
// ⚠️ IMPORTANTE — como o app fala com a IA:
// A função `askClaude` usa `window.claude.use("sample")`, que só existe DENTRO
// do ambiente de artefatos do Claude (claude.ai). Num projeto próprio (Next.js,
// Vite, etc.) esse canal NÃO existe. Para rodar fora do Claude, troque o corpo
// de `askClaude` por uma chamada ao SEU backend, que guarda a chave da API da
// Anthropic com segurança. Exemplo de substituição:
//
//   async function askClaude(input, opts) {
//     const r = await fetch("/api/generate", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ input }),
//     });
//     if (!r.ok) { const e:any = new Error("http"); e.code = "upstream_error"; throw e; }
//     const { text } = await r.json();
//     if (!text?.trim()) { const e:any = new Error("empty"); e.code = "empty_completion"; throw e; }
//     return text.trim();
//   }
//
// A chave da API NUNCA deve ficar no código do navegador — sempre num backend.
// ─────────────────────────────────────────────────────────────────────────────
// NÚCLEO IA PORTÁTIL — Forja de Prompts (versão NOVA, adaptada offline/local).
// React vem do UMD global (vendorado); geração usa o motor local (/api/forja).
const { useState, useRef, useEffect } = React;


// ── Estilos disponíveis (ordem alfabética) ────────────────────────────
const STYLES = [
  { id: "render3d", label: "3D / CGI", tag: "🧱", hint: "Render 3D realista, materiais, iluminação global" },
  { id: "anime", label: "Anime", tag: "🌸", hint: "Estilo de estúdio, cel-shading, traço, paleta" },
  { id: "ghiblivibe", label: "Anime Aconchegante", tag: "🍃", hint: "Slice of life, fundo aquarelado, luz suave, nostalgia" },
  { id: "aquarela", label: "Aquarela", tag: "🎨", hint: "Manchas suaves, papel, bordas que escorrem" },
  { id: "bodyhorror", label: "Body Horror / Terror Visceral", tag: "🩸", hint: "+18 · Atmosfera, estranhamento corporal, tensão" },
  { id: "actionfigure", label: "Boneco / Action Figure", tag: "🦸", hint: "Figura na embalagem blister, acessórios, escala" },
  { id: "cartoon", label: "Cartoon", tag: "🐰", hint: "Desenho 2D, traço expressivo, cores vivas" },
  { id: "carrossel", label: "Carrossel Instagram", tag: "🎠", hint: "Vários cards com visual + copy, gancho ao CTA", carousel: true },
  { id: "cena", label: "Cena de Filme / Desenho", tag: "🎭", hint: "Combine com um gênero · personagens + duração", scene: true },
  { id: "cinema", label: "Cinematográfico", tag: "🎞️", hint: "Widescreen, color grade, grão de cinema" },
  { id: "claymation", label: "Claymation", tag: "🟤", hint: "Stop-motion, textura de argila, marcas de dedo" },
  { id: "cyberpunk", label: "Cyberpunk", tag: "🌃", hint: "Neon, atmosfera futurista, reflexos, chuva" },
  { id: "darkfantasy", label: "Dark Fantasy", tag: "🐉", hint: "Fantasia sombria, épico, mórbido, vibe RPG" },
  { id: "editorial", label: "Editorial de Moda", tag: "👗", hint: "Vibe de revista, pose, styling, luz dramática" },
  { id: "funko", label: "Funko Pop", tag: "🧸", hint: "Vinil, cabeça grande, caixa, olhos pretos" },
  { id: "isometrico", label: "Isométrico", tag: "🧊", hint: "Cenário 3D em ângulo iso, diorama, ícones" },
  { id: "lineart", label: "Line Art / Tattoo", tag: "✒️", hint: "Traço limpo, minimalista, alto contraste" },
  { id: "colorir", label: "Livro de Colorir", tag: "🖍️", hint: "Infantil · traços simples pra pintar + historinha", coloring: true },
  { id: "logo", label: "Logo / Branding", tag: "🏷️", hint: "Marca minimalista, vetorial, variações" },
  { id: "lowpoly", label: "Low Poly", tag: "🔺", hint: "Geometria de poucos polígonos, facetada, estilizada" },
  { id: "mockup", label: "Mockup de Produto", tag: "📦", hint: "Embalagem realista, fundo de estúdio, e-commerce" },
  { id: "oleo", label: "Óleo / Clássico", tag: "🖼️", hint: "Pinceladas, claro-escuro, vibe renascentista" },
  { id: "pixar", label: "Pixar", tag: "🎬", hint: "Render animado estilizado, fofo, expressivo" },
  { id: "pixelart", label: "Pixel Art", tag: "👾", hint: "Retrô 8/16-bit, dithering, paleta limitada" },
  { id: "poster", label: "Pôster / Capa", tag: "📰", hint: "Composição de cartaz, tipografia integrada" },
  { id: "comic", label: "Quadrinhos", tag: "💥", hint: "Contornos grossos, halftone, balões, cores chapadas" },
  { id: "realismo", label: "Realismo Extremo", tag: "📷", hint: "Foto hiper-realista, pele, luz, lente, grão" },
  { id: "scifi", label: "Sci-Fi / Ficção Científica", tag: "🚀", hint: "Naves, planetas, tecnologia, futuro" },
  { id: "steampunk", label: "Steampunk", tag: "⚙️", hint: "Engrenagens, latão, vapor, vibe vitoriana" },
  { id: "storyboard", label: "Storyboard", tag: "🎬", hint: "Quebra a cena em vários quadros, com continuidade" },
  { id: "thumbnail", label: "Thumbnail YouTube", tag: "▶️", hint: "Alto contraste, expressão exagerada, texto" },
  { id: "timelapse", label: "Timelapse Acelerado", tag: "⏱️", hint: "Construção, maquiagem, montagem — do zero ao pronto", timelapse: true },
  { id: "ugc", label: "UGC / Anúncio", tag: "🎥", hint: "Vídeo de anúncio: criador mostra/usa o produto", video: true },
  { id: "vaporwave", label: "Vaporwave / Synthwave", tag: "🌴", hint: "Neon rosa-roxo, grid 80s, pôr do sol retrô" },
  { id: "vintage", label: "Vintage / Analógico", tag: "📼", hint: "Polaroid, película 70/90, luz vazada" },
];

const ASPECTS = ["1:1", "3:2", "2:3", "16:9", "9:16", "4:5"];
const TL_TOTALS = [[15,"15s"],[30,"30s"],[60,"1min"],[120,"2min"],[180,"3min"]];
const TL_CLIPS = [6, 8, 10];

// ── Categoria de cada estilo (para regras de combinação) ──────────────
const STYLE_CATEGORIES = {
  realismo: "photo", editorial: "photo", cinema: "photo", vintage: "photo", mockup: "photo",
  render3d: "3d_real",
  pixar: "3d_stylized", lowpoly: "3d_stylized", isometrico: "3d_stylized", claymation: "3d_stylized",
  anime: "illust2d", ghiblivibe: "illust2d", cartoon: "illust2d", aquarela: "illust2d",
  oleo: "illust2d", comic: "illust2d", lineart: "illust2d", pixelart: "illust2d",
  cyberpunk: "theme", darkfantasy: "theme", scifi: "theme", bodyhorror: "theme", steampunk: "theme", vaporwave: "theme",
  funko: "product", actionfigure: "product",
  logo: "design", poster: "design", thumbnail: "design",
  storyboard: "format", carrossel: "format",
  colorir: "coloring",
  cena: "scene",
  timelapse: "video",
  ugc: "video",
};

const COMPAT = {
  photo:         ["photo", "theme", "design", "format", "scene"],
  "3d_real":     ["theme", "format", "scene"],
  "3d_stylized": ["theme", "format", "scene"],
  illust2d:      ["illust2d", "theme", "design", "format", "scene"],
  theme:         ["photo", "3d_real", "3d_stylized", "illust2d", "theme", "product", "design", "format", "scene"],
  product:       ["theme"],
  design:        ["theme", "illust2d", "photo"],
  format:        ["photo", "3d_real", "3d_stylized", "illust2d", "theme"],
  scene:         ["photo", "3d_real", "3d_stylized", "illust2d", "theme"],
  coloring:      [],
  video:         [],
};

function canCombine(aId, bId) {
  if (!aId || !bId || aId === bId) return false;
  const aCat = STYLE_CATEGORIES[aId];
  const bCat = STYLE_CATEGORIES[bId];
  return !!(COMPAT[aCat] && COMPAT[aCat].includes(bCat));
}
function canCombineAny(aId) {
  const aCat = STYLE_CATEGORIES[aId];
  return ((COMPAT[aCat] && COMPAT[aCat].length) || 0) > 0;
}

// Pergunta ao Claude a partir da página publicada (capacidade "sample").
async function askClaude(input, opts) {
  // NÚCLEO: geração pelo motor local (/api/forja), não-streaming.
  // opts.images (array de data-URLs) é a única parte de opts usada: manda a
  // primeira imagem pro motor trocar pro modo VISAO de verdade. O resto de
  // opts (cache/modelTier/onText) não existe no motor local — ignorado.
  const imgs = opts && opts.images;
  const image = Array.isArray(imgs) ? imgs[0] : imgs;
  // opts.maxTokens: teto por modo. Um prompt de imagem único cabe em ~300
  // tokens; teto baixo limita o estrago se o modelo entrar em loop.
  const payload = { system: "", user: input, max_tokens: (opts && opts.maxTokens) || 1500 };
  if (image) payload.image = image;
  // opts.etapa2: 2ª passada no MESMO pedido (o servidor troca o modelo uma vez só);
  // o texto deve conter {{INVENTARIO}}, substituído pela resposta da 1ª passada.
  if (opts && opts.etapa2) { payload.user2 = opts.etapa2; payload.max_tokens2 = opts.maxTokens2 || 1000; }
  const response = await fetch("/api/forja", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  let data = null;
  try { data = await response.json(); } catch (_) {}
  if (!data || !data.ok) {
    const backendCode = data && data.error && data.error.code;
    const e = new Error((data && data.error && data.error.message) || "engine");
    e.code = backendCode === "VISION_UNAVAILABLE" ? "vision_unavailable"
      : backendCode === "VISION_TIMEOUT" ? "vision_timeout"
      : backendCode === "VISION_START_FAILED" ? "vision_start_failed" : "engine";
    throw e;
  }
  const text = ((data.text) || "").trim();
  if (!text) { const e = new Error("empty"); e.code = "empty_completion"; throw e; }
  if (opts && opts.onInventario && data.inventario) opts.onInventario(data.inventario);
  if (opts && opts.onWarning) {
    if (data.tags_trimmed) opts.onWarning("A IA repetiu tags no final do prompt; removi o excesso. Confira o resultado.");
    else if (data.truncated) opts.onWarning("A resposta atingiu o limite de tamanho e pode estar incompleta. Tente gerar de novo.");
  }
  return text;
}

// ── TEXTO LONGO (resumo de livro, artigo colado…) ───────────────────────
// O motor só deixa pra resposta o que sobra do contexto depois do pedido
// (engine_manager.stream_chat: chars/3,2 + 320 de margem). Um texto de ~1200
// palavras come quase tudo num contexto de 4096 e o carrossel saía com 2–3
// cards. Acima de IDEIA_LONGA a Forja trabalha em etapas: condensa o texto,
// planeja um ROTEIRO (1 linha por card/quadro) e escreve em lotes pequenos.
const IDEIA_LONGA = 1200; // caracteres

async function contextoMotor() {
  try {
    const d = await (await fetch("/api/status")).json();
    const n = Number(d && d.data && d.data.context_size);
    return n >= 1024 ? n : 4096;
  } catch (_) { return 4096; }
}

// Maior trecho (em caracteres) que cabe no contexto sobrando ~700 tokens de resposta.
function fatiaMax(ctx) { return Math.max(1500, Math.floor((ctx - 336 - 700) * 3.2) - 1600); }

// Quebra em pedaços de até `max` caracteres, respeitando fim de frase/parágrafo.
function fatiar(texto, max) {
  const partes = [];
  let atual = "";
  for (let frase of texto.split(/(?<=[.!?…:;])\s+|\n+/)) {
    frase = frase.trim();
    while (frase.length > max) { // frase sem pontuação maior que a fatia: corta seco
      if (atual) { partes.push(atual); atual = ""; }
      partes.push(frase.slice(0, max));
      frase = frase.slice(max);
    }
    if (!frase) continue;
    if (atual && atual.length + 1 + frase.length > max) { partes.push(atual); atual = frase; }
    else atual = atual ? atual + " " + frase : frase;
  }
  if (atual) partes.push(atual);
  return partes;
}

function promptResumo(texto, palavras) {
  return `Condense the SOURCE TEXT below into a brief of at most ${palavras} words. Keep its central theme, the main ideas in their original order, and the concrete facts, names, numbers and examples. Plain sentences only — no preamble, no headings, no commentary. Write in the same language as the source text.

SOURCE TEXT:
"""
${texto}
"""`;
}

// Reduz o texto até caber numa chamada só (textos enormes: resume por pedaços).
async function condensar(texto, ctx, aoAndar) {
  const fatia = fatiaMax(ctx);
  let material = texto;
  for (let volta = 0; volta < 4 && material.length > fatia; volta++) {
    const partes = fatiar(material, fatia);
    const palavras = Math.max(50, Math.min(250, Math.floor(fatia / partes.length / 7), Math.floor(fatia / 14)));
    const notas = [];
    for (let i = 0; i < partes.length; i++) {
      aoAndar(i + 1, partes.length);
      notas.push(await askClaude(promptResumo(partes[i], palavras), { maxTokens: 700 }));
    }
    material = notas.join("\n\n");
  }
  return material;
}

// Divide o texto em `n` partes de tamanho parecido, sem quebrar frase.
function dividir(texto, n) {
  const frases = fatiar(texto, Math.max(200, Math.ceil(texto.length / (n * 4))));
  const alvo = frases.join(" ").length / n;
  const partes = [];
  let atual = "", soma = 0;
  for (let i = 0; i < frases.length; i++) {
    atual = atual ? atual + " " + frases[i] : frases[i];
    soma += frases[i].length + 1;
    const restam = frases.length - i - 1;
    if (partes.length < n - 1 && (soma >= alvo * (partes.length + 1) || restam <= n - 1 - partes.length)) { partes.push(atual); atual = ""; }
  }
  if (atual) partes.push(atual);
  return partes;
}

// Modelo pequeno, solto, planeja tudo em cima dos primeiros parágrafos. Por isso
// o texto vai DIVIDIDO em partes numeradas e cada card/quadro recebe a sua
// (carrossel: card 1 = gancho do todo, último = CTA, os do meio = uma parte cada).
function promptRoteiro(texto, rotulo, total, carrossel) {
  const n = carrossel ? Math.max(1, total - 2) : total;
  const partes = dividir(texto, n);
  const mapa = [];
  for (let i = 1; i <= total; i++) {
    if (carrossel && i === 1) mapa.push(`${rotulo} 1: [HOOK — the big promise or most surprising idea of the whole text]`);
    else if (carrossel && i === total && total > 2) mapa.push(`${rotulo} ${i}: [CTA — the final takeaway of the whole text and what the reader should do next]`);
    else {
      const p = Math.min(partes.length, carrossel ? i - 1 : i);
      mapa.push(`${rotulo} ${i}: [the key idea of PART ${p}, with its concrete fact, name, number or example]`);
    }
  }
  return `Plan ${carrossel ? `an Instagram carousel of ${total} cards` : `a storyboard of ${total} frames`} based on the SOURCE TEXT below, which is split into ${partes.length} numbered parts.
Output EXACTLY these ${total} lines and nothing else, replacing each [bracket] (brackets and the words PART/HOOK/CTA included) with your own sentence of at most 35 words:
${mapa.join("\n")}
- Each line uses ONLY the part it names, so together the lines cover the text from beginning to end. Never repeat an idea.
- Summarize in your own words, but keep the concrete fact, name, number or example of that part — avoid generic advice.
- Write in the same language as the source text. No preamble, no commentary.

SOURCE TEXT:
${partes.map((p, i) => `[PART ${i + 1}]\n${p}`).join("\n\n")}`;
}

// `rotuloRe`: "CARD" ou "(?:QUADRO|FRAME)". Devolve as linhas do roteiro por
// número, ou null se o modelo não seguiu o formato (aí o texto bruto serve de base).
function lerRoteiro(texto, rotuloRe, total) {
  const linhas = new Array(total).fill("");
  const re = new RegExp(`^\\W*${rotuloRe}\\s*(\\d+)\\s*[:—–\\-.)]+\\s*(.+)$`, "i");
  let achou = 0;
  for (const l of texto.split("\n")) {
    const m = l.replace(/\*\*/g, "").trim().match(re);
    const n = m ? parseInt(m[1], 10) : 0;
    if (n < 1 || n > total || linhas[n - 1]) continue;
    // o modelo costuma devolver os colchetes e o rótulo do molde ("[PART 3: …]", "[HOOK — …]")
    const limpo = m[2].trim().replace(/^\[|\]$/g, "").replace(/^(PART[ES]?\s*\d+|HOOK|GANCHO|CTA)\s*[:—–\-]+\s*/i, "").trim();
    if (limpo) { linhas[n - 1] = limpo; achou++; }
  }
  return achou >= Math.ceil(total / 2) ? linhas : null;
}

// Corta o que o modelo escreveu além do lote: itens depois de `ate` e, fora do
// último lote, a legenda adiantada.
function apararLote(texto, rotuloRe, ate, ultimo) {
  const linhas = texto.split("\n");
  const cab = new RegExp(`^\\W*${rotuloRe}\\s*(\\d+)`, "i");
  for (let i = 0; i < linhas.length; i++) {
    const m = linhas[i].replace(/\*\*/g, "").match(cab);
    if ((m && parseInt(m[1], 10) > ate) || (!ultimo && /^\W*(LEGENDA|CAPTION)\b/i.test(linhas[i]))) {
      return linhas.slice(0, i).join("\n").trim();
    }
  }
  return texto.trim();
}

// Proporção padrão mais próxima da imagem (W:H) + orientação.
function proporcao(w, h) {
  const PADROES = [[1, 1], [4, 5], [3, 4], [2, 3], [10, 16], [9, 16], [5, 4], [4, 3], [3, 2], [16, 10], [16, 9], [21, 9]];
  const r = w / h;
  let melhor = PADROES[0], dist = Infinity;
  for (const p of PADROES) { const d = Math.abs(Math.log(r / (p[0] / p[1]))); if (d < dist) { dist = d; melhor = p; } }
  const orient = melhor[0] === melhor[1] ? "square" : melhor[0] > melhor[1] ? "horizontal / landscape" : "vertical / portrait";
  return { ar: `${melhor[0]}:${melhor[1]}`, orient: orient };
}

// Cena com fotos de personagem: o motor manda 1 imagem por pedido (e não desconta
// imagens do contexto), então até 4 fotos viram uma folha de referência lado a lado.
function folhaPersonagens(previews) {
  return Promise.all(previews.map((src) => new Promise((res) => {
    const img = new Image();
    img.onload = () => res(img);
    img.onerror = () => res(null);
    img.src = src;
  }))).then((imgs) => {
    imgs = imgs.filter(Boolean);
    if (!imgs.length) return previews[0];
    const LADO = 800, cols = imgs.length > 2 ? 2 : imgs.length, rows = Math.ceil(imgs.length / cols);
    const cv = document.createElement("canvas");
    cv.width = cols * LADO; cv.height = rows * LADO;
    const g = cv.getContext("2d");
    g.fillStyle = "#ffffff"; g.fillRect(0, 0, cv.width, cv.height);
    imgs.forEach((img, i) => {   // cada foto inteira (sem corte) centrada no seu quadro
      const k = Math.min(LADO / img.naturalWidth, LADO / img.naturalHeight);
      const w = img.naturalWidth * k, h = img.naturalHeight * k;
      g.drawImage(img, (i % cols) * LADO + (LADO - w) / 2, Math.floor(i / cols) * LADO + (LADO - h) / 2, w, h);
    });
    return cv.toDataURL("image/jpeg", 0.9);
  });
}

// Modo "recriar fiel": 2 passadas. A 1ª é um INVENTÁRIO objetivo do que se vê
// (ficha com campos obrigatórios: pose, roupas, local, tipo de imagem…); a 2ª
// compõe o prompt SÓ a partir do inventário + imagem. Com modelo de visão
// pequeno (Gemma 3 4B), separar "ver" de "escrever" reduz esquecimento e invenção.
// Regras adaptadas do "REIMAGINADOR DE PROMPTS VISUAIS" (docs/): MEIO e
// ORIENTAÇÃO viram escolhas fechadas no topo da ficha (o 4B confundia desenho com
// 3D e virava personagem de costas pra frente), e voltam como FATOS TRAVADOS na
// 2ª passada via {{LINHA:...}}. `estiloId` (opcional) = reimaginar no estilo
// escolhido: PRESERVA sujeito/pose/orientação/composição, TRANSFORMA só o meio.
function promptsFiel(langLine, info, alvo, estiloId) {
  const prop = info && info.ratio ? `${info.ratio.ar} (${info.ratio.orient}, ${info.w}×${info.h} px)` : "unknown";
  const etapa1 = `You are a meticulous visual analyst. Look ONLY at the attached image and write a factual INVENTORY of what is VISIBLE. Do not guess hidden things; write "not visible" when a field does not apply. Never identify real people — describe them generically. Write the field contents in ${langLine.includes("ENGLISH") ? "English" : "Brazilian Portuguese"}.
Image proportions: ${prop}.
Left/right always means SCREEN-LEFT / SCREEN-RIGHT (the viewer's point of view).

Answer with EXACTLY these labeled lines, short and concrete (no intro, no conclusion):
MEIO: write ONLY ONE of: photograph | 2D drawing / illustration | anime / manga | cartoon | comic art | painting (say which: oil, watercolor, gouache, digital) | sketch / line art | pixel art | 3D render (CGI). Look at the evidence: visible outlines and flat or cel shading = 2D, NOT 3D. Choose "3D render" only if it clearly looks modeled and rendered.
ORIENTACAO: write ONLY ONE of: facing the viewer | back to the viewer (seen from behind) | profile facing screen-left | profile facing screen-right | three-quarter front | three-quarter back. Then: face visible yes/no.
TECNICA: line work, shading type, texture, level of detail (only what is visible)
ENQUADRAMENTO: shot size (close-up, medium, full body…), camera angle (eye level, low, high, top-down), depth of field
SUJEITO: who or what, how many, apparent age range, build, skin tone, position in the frame (screen-left/center/screen-right, foreground/background)
FAIXA ETARIA: write ONLY ONE of: adults only | includes a child or teenager (looks under 18) | no people | uncertain
POSE: body position, torso direction, head direction, each visible arm and hand (what it touches or holds), legs and feet, contact points with the ground or objects. Describe only visible limbs.
EXPRESSAO: facial expression, or "not visible" if the face is hidden or turned away
ROUPAS: each piece from top to bottom — type, color, apparent material, fit, pattern; shoes; accessories
CABELO: color, length, style (as seen from this angle)
LOCAL: indoor/outdoor, kind of place, background objects and WHERE they are, floor/walls/sky
ILUMINACAO: light direction, hard/soft, time of day, color temperature, shadows
CORES: dominant colors and overall palette
TEXTO VISIVEL: exact visible text in quotes, or "none"
DETALHES MARCANTES: up to 5 distinctive details that make this image unique`;
  const regraAlvo = alvo === "sd"
    ? "FORMAT: Stable Diffusion style — comma-separated tags ordered by importance (most important first); weight the 3 most important details like (detail:1.2). No sentences."
    : alvo === "mj"
      ? "FORMAT: Midjourney style — dense descriptive phrases separated by commas. Do NOT write any --parameters (they are added automatically)."
      : "FORMAT: natural, flowing descriptive sentences (best for Flux, DALL·E, Ideogram, Gemini).";
  const estilo = estiloId && STYLES.find((s) => s.id === estiloId);
  const brief = estilo && STYLE_BRIEFS[estilo.id];
  const travas = estilo
    ? `LOCKED FACTS (must stay true in the prompt):
- New medium / style: ${brief ? brief.split(".")[0] : estilo.label} — the prompt MUST start with it.
- Original medium (REPLACE it, do not keep it): {{LINHA:MEIO}}
- Body orientation (KEEP exactly): {{LINHA:ORIENTACAO}}`
    : `LOCKED FACTS (must stay true in the prompt):
- Medium: {{LINHA:MEIO}} — the prompt MUST start with this medium.
- Body orientation: {{LINHA:ORIENTACAO}} — state it clearly near the start (e.g. "seen from behind, back to the viewer" if that is the case).`;
  const objetivo = estilo
    ? `Write a prompt that recreates the SAME scene of the attached image — same subject, pose, body orientation, framing, composition, clothing, hair, colors and setting — but rendered in a NEW STYLE:
${brief || estilo.hint}

PRESERVE: subject count, identity traits (hair, eye color, apparent age, skin tone, face shape), action, pose, orientation, expression, clothing, objects, visible text and composition.
TRANSFORM ONLY: medium, rendering, line work, texture, and lighting treatment as the new style requires.
- Use the attached image ONLY to check pose, orientation and layout — IGNORE its original medium and rendering.
- Use only the parts of the style description that fit this scene. Do NOT add packaging, signs, neon, armor, props, implants or other elements that are not in the inventory.`
    : `Write a prompt that recreates THIS EXACT image as faithfully as possible. Do not apply a new style and do not embellish it.
- Never describe a 2D drawing as 3D, CGI, a render or a photo, and never describe a photo as an illustration.`;
  const etapa2 = `You are an expert prompt engineer for AI image generators. Below is a verified INVENTORY of the attached image.
${objetivo}

${travas}

INVENTORY:
{{INVENTARIO}}

RULES:
- ${langLine}
- Order: medium/style first, then shot/camera and body orientation, the subject, the POSE (torso, head, each visible arm and hand and what it touches, legs, contact points), expression (skip it if the face is not visible), the CLOTHING piece by piece with colors, hair, the SETTING with where things are, lighting, colors.
- Use screen-left / screen-right for positions in the frame.
- Use ONLY facts from the inventory. Do NOT add objects, people, text or details that are not there. Do NOT invent hidden parts. Keep every distinctive detail.
- If there is visible text, quote it exactly; otherwise do not mention text.
- No empty quality words (masterpiece, 8K, award-winning). ${estilo && STYLE_CATEGORIES[estilo.id] === "photo" ? "" : "Camera brands and lens names only if the result is a photograph."}
- The image proportion is ${prop}; compose for it.
- 150–250 words. Never name or guess real people.
- ${REGRA_MENORES}
- ${regraAlvo}

Return EXACTLY this structure and nothing else:
PROMPT:
[the prompt]
NEGATIVE PROMPT:
[comma-separated things that would break fidelity — e.g. wrong body orientation, ${estilo ? "the original medium" : "a different medium"}, different pose, extra people, different clothing colors. Never list something that IS in the image. Max 25 words]`;
  return { etapa1, etapa2 };
}

// Rede de segurança determinística sobre a saída do modelo pequeno: se o
// inventário diz "de costas" e o prompt não diz, injeta; se é 2D e o prompt
// fala em 3D/render, tira (tags) ou avisa (texto corrido) e reforça o negative.
const RE_COSTAS = /\b(back to the (viewer|camera)|from behind|seen from (the )?(back|behind)|back view|rear view|facing away|three-quarter back|de costas|de tr[aá]s|vista traseira|vista de costas)\b/i;
const RE_2D = /(drawing|illustration|anime|manga|cartoon|comic|sketch|line art|painting|watercolor|gouache|pixel|desenho|ilustra|quadrinho|pintura|aquarela|guache|esbo[cç]o)/i;
const RE_3D = /(\b3d\b|\bcgi\b|octane|unreal engine|blender|ray[- ]?trac|subsurface|photo-?realis|hyper-?realis|fotorrealis|hiper-?realis|\brender(ed|ing)?\b|renderiza)/i;

// Regra editorial sobre MENORES (REIMAGINADOR, seção 12): BLOQUEIO TOTAL. A Forja não
// produz prompt com criança ou adolescente (quem é ou aparenta ter menos de 18), em nenhum
// estilo — decisão do usuário em 10/10/2026, "só por garantia" (uma versão por conteúdo,
// que liberava cena comum, chegou a ser feita e foi descartada no mesmo dia).
// Duas camadas: a regra vai no prompt (o modelo responde só BLOQUEADO_MENORES) e uma
// checagem determinística por cima (ideia digitada / linhas do inventário).
const BLOQ_MENORES = "BLOQUEADO_MENORES";
const REGRA_MENORES = `MINORS POLICY (applies to EVERY style — cartoon, anime, comics and 3D included): never write a prompt that depicts anyone who is or appears to be under 18 (babies, children, teenagers), whatever the scene. If the request or the image involves such a person, output ONLY the single word ${BLOQ_MENORES} and nothing else.`;
// sem palavras ambíguas ("menor preço", "garota" adulta, "livro infantil")
const RE_MENOR = /(?<!\p{L})(child(ren)?|kids?|toddlers?|bab(y|ies)|newborns?|infants?|minors?|teen(ager)?s?|pre-?teens?|school ?(girl|boy)s?|little (girl|boy)s?|under ?18|underage|crian[cç]as?|beb[eê]s?|rec[eé]m-?nascid[oa]s?|menin(inh)?[oa]s?|garotinh[oa]s?|adolescentes?|menor(es)? de idade|colegia(l|is)|novinh[oa]s?|lolis?|shotas?)(?!\p{L})/iu;
const MSG_MENORES = "🚫 A Forja não gera prompts com crianças ou adolescentes (menores de 18 anos), em nenhum estilo.";
const MSG_MENORES_IMG = MSG_MENORES + " Se a imagem só tem adultos, a IA pode ter errado a idade — tente de novo ou use outra imagem.";

function idadeMenor(txt) {
  if (!txt) return false;
  if (RE_MENOR.test(txt)) return true;
  for (const m of txt.matchAll(/(\d{1,2})(?:\s*(?:-|–|to|a|ou|or)\s*\d{1,2})?\s*(?:years?(?:[- ]old)?|y\/?o|anos)/gi)) {
    if (Number(m[1]) < 18) return true;      // "8-10 years old", "15 anos"
  }
  return false;
}

// Lê o inventário da 1ª passada: true = há criança/adolescente na imagem (bloquear)
function temMenor(inventario) {
  const faixa = linhaInv(inventario, "FAIXA ETARIA");
  const escolhida = faixa && !faixa.includes("|") ? faixa : "";   // às vezes o modelo copia o menu inteiro
  return /child|teen|under ?18|crian|adolesc|menor/i.test(escolhida) || idadeMenor(linhaInv(inventario, "SUJEITO"));
}

function linhaInv(inv, rotulo) {
  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toUpperCase().trim();
  for (const bruta of (inv || "").split("\n")) {
    const l = bruta.trim().replace(/^[-*•#\s]+/, "").replace(/\*\*/g, "");
    const i = l.indexOf(":");
    if (i > 0 && norm(l.slice(0, i)) === norm(rotulo)) return l.slice(i + 1).trim();
  }
  return "";
}

function reforcarFiel(text, inventario, alvo, outLang, estiloId) {
  const avisos = [];
  const m = text.match(/^([\s\S]*?PROMPT:\s*\n?)([\s\S]*?)(\n\s*NEGATIVE PROMPT:\s*\n?)([\s\S]*)$/i);
  const so = m ? null : text.match(/^([\s\S]*?PROMPT:\s*\n?)([\s\S]*)$/i);   // veio sem NEGATIVE PROMPT
  let [cab, corpo, sepNeg, neg] = m ? [m[1], m[2], m[3], m[4]] : so ? [so[1], so[2], "\n\nNEGATIVE PROMPT:\n", ""] : ["", text, "\n\nNEGATIVE PROMPT:\n", ""];
  const extrasNeg = [];
  const orient = linhaInv(inventario, "ORIENTACAO");
  // a opção só vale se o modelo escolheu UMA (às vezes ele copia o menu inteiro com "|")
  if (orient && !orient.includes("|") && RE_COSTAS.test(orient) && !RE_COSTAS.test(corpo)) {
    const pre = alvo === "sd" ? "(from behind:1.3), (back view:1.2), " : alvo === "mj" ? "back view, seen from behind, " : outLang === "en" ? "Back view: the subject is seen from behind, facing away from the viewer. " : "Vista de costas: o personagem é visto por trás, de costas para o observador. ";
    corpo = pre + corpo.trimStart();
    extrasNeg.push(outLang === "en" ? "front view, facing the camera, visible face" : "vista frontal, de frente para a câmera, rosto visível");
    avisos.push("O inventário viu o personagem de costas e o prompt não dizia isso — reforcei no início.");
  }
  const meio = linhaInv(inventario, "MEIO");
  if (!estiloId && meio && !meio.includes("|") && RE_2D.test(meio) && !RE_3D.test(meio)) {
    if (alvo !== "geral") {
      const partes = corpo.split(",");
      const limpas = partes.filter((p) => !RE_3D.test(p));
      if (limpas.length < partes.length) { corpo = limpas.join(",").trim(); avisos.push("Tirei termos de 3D/render do prompt: a imagem é 2D."); }
    } else if (RE_3D.test(corpo)) {
      avisos.push("A imagem é 2D mas o prompt cita 3D/render/foto — revise esses termos antes de usar.");
    }
    extrasNeg.push(outLang === "en" ? "3D render, CGI, photorealistic, photograph" : "render 3D, CGI, fotorrealista, fotografia");
  }
  if (extrasNeg.length) neg = [neg.trim().replace(/[,\s]+$/, ""), ...extrasNeg].filter(Boolean).join(", ");
  return { text: neg.trim() ? `${cab}${corpo.trim()}${sepNeg}${neg.trim()}` : `${cab}${corpo.trim()}`, avisos };
}

// Traduz o código de erro da capacidade em uma mensagem amigável.
function sampleErrMsg(e) {
  const c = e && e.code;
  if (c === "cancelled") return "";
  if (c === "not_granted" || c === "sampling_disabled" || c === "not_declared" || c === "capability_disabled" || c === "capability_removed")
    return "A geração por IA precisa da sua permissão. Abra o app publicado no Claude e permita o uso quando perguntado (ou recarregue a página se já recusou).";
  if (c === "rate_limited") return "Muitas gerações seguidas. Espere alguns segundos e tente de novo.";
  if (c === "images_unavailable") return "Este visualizador não consegue enviar imagens. Abra o link do app no navegador pra usar a engenharia reversa.";
  if (c === "vision_unavailable") return "O modo de visão (Gemma 3 4B) ainda não foi calibrado nesta máquina. Baixe o modelo e rode a calibração do modo VISAO antes de usar a engenharia reversa.";
  if (c === "vision_timeout") return "O modelo de visão demorou demais para carregar (o disco estava lento ou faltou memória livre). Feche outros programas pesados e tente de novo — a segunda carga costuma ser mais rápida.";
  if (c === "vision_start_failed") return "O modelo de visão não conseguiu iniciar. Detalhe: " + (e.message || "sem detalhe") + " — veja logs\\v0_6\\llama-server.log.";
  if (c === "image_rejected") return "Não consegui usar essa imagem. Tente outra (JPG, PNG ou WebP, até 20 MB).";
  if (c === "prompt_too_large") return "O pedido ficou grande demais. Reduza o texto, os quadros/cards ou os segmentos.";
  if (c === "refused") return "A IA não conseguiu responder a esse pedido. Ajuste a ideia e tente de novo.";
  if (c === "session_expired") return "Sua sessão do Claude expirou. Entre de novo e tente outra vez.";
  return "Algo deu errado ao gerar. Tente de novo em alguns segundos.";
}

// ── Instruções por estilo ─────────────────────────────────────────────
const STYLE_BRIEFS = {
  render3d: "REALISTIC 3D / CGI render. Describe physically-based materials (PBR) with accurate roughness, metalness and reflections, high-resolution textures, ray-traced global illumination and soft shadows, studio or HDRI environment lighting, precise geometry, subtle ambient occlusion, and a clean polished production-render quality (Blender/Octane/Redshift feel) — not cartoonish.",
  anime: "ANIME / MANGA illustration. Reference a fitting art direction (e.g. modern Kyoto Animation softness, Makoto Shinkai luminous skies, Studio Trigger dynamic energy, 90s retro cel) WITHOUT naming copyrighted characters. Describe line work, cel-shading or soft gradients, expressive eyes, hair rendering, color palette, background art style, and emotional tone.",
  ghiblivibe: "COZY HAND-PAINTED ANIME in a warm slice-of-life tradition (do NOT name any studio). Describe lush hand-painted watercolor-style backgrounds, soft natural lighting and golden warmth, gentle rolling landscapes, fluffy clouds and detailed nature (grass, trees, food, small everyday objects), soft rounded character design with simple expressive faces, a nostalgic peaceful wholesome mood, and a tender, comforting storybook atmosphere.",
  aquarela: "WATERCOLOR painting. Describe soft translucent washes, organic bleeding edges where pigments diffuse, visible cold-press paper texture and grain, gentle gradients, white paper showing through highlights, delicate granulation, loose expressive brush strokes, and a light airy color palette. Mention controlled wet-on-wet blooms and a hand-painted artisanal feel.",
  bodyhorror: "BODY HORROR / VISCERAL HORROR art (mature, 18+). This is the cinematic/surreal-art horror genre in the tradition of practical-effects creature films and unsettling fine-art horror. Build DREAD through atmosphere rather than shock: describe uncanny anatomical distortion, biomechanical or grotesque transformation, eerie textures (slick, fibrous, calcified), oppressive shadow and fog, sickly desaturated or bruised color palettes, decay and wrongness, claustrophobic framing, and a deeply disturbing surreal mood. Keep it artful and suggestive — favor implication, silhouette and the half-seen over explicit gratuitous gore. No real identifiable people; no minors under any circumstance.",
  actionfigure: "COLLECTIBLE ACTION FIGURE of the subject, shown as a real toy product. Describe articulated plastic figure, realistic scale (e.g. 6-inch), it sitting inside a blister/clamshell retail packaging with cardback, accessories laid out beside it, the product/brand-style logo area, plastic and paint texture, and clean product photography lighting. Make it clearly look like merchandise, not a real person.",
  cartoon: "CARTOON 2D illustration (Western animated style, distinct from anime). Describe bold clean outlines, simplified exaggerated shapes, bouncy expressive character design, flat bright saturated colors, minimal shading or simple cel shading, playful energetic poses, and a fun lighthearted TV/web-cartoon feel. Avoid naming copyrighted characters.",
  carrossel: "INSTAGRAM CAROUSEL — a swipeable sequence of square/vertical cards designed for social engagement and saves, NOT a single image or a movie scene. Each card pairs a VISUAL (image prompt) with punchy on-card COPY. The sequence follows a proven arc: a scroll-stopping HOOK card, several value/story cards that build momentum and keep people swiping, and a final CTA card. Keep a consistent visual identity across all cards (same palette, type feel, framing) so it looks like one cohesive set. Copy must be short, high-contrast and readable on a phone.",
  cinema: "CINEMATIC FILM STILL. Describe an anamorphic widescreen frame, filmic color grading (teal-orange or moody desaturated), shallow depth of field with creamy bokeh, motivated practical lighting, atmospheric haze, fine film grain, lens flares, and the composed mood of a frame pulled from a feature film.",
  cena: "MOVIE / CARTOON SCENE — a short piece of a story told as video, NOT a single still. Think like a director: stage the action across the shot with clear blocking, purposeful camera work (shot size, angle, movement — pan, dolly, handheld), motivated lighting, mood and pacing. Keep the character(s) consistent and the setting coherent. Combine with a chosen genre/look (the blended style defines the aesthetic — cinematic, anime, cyberpunk, dark fantasy, etc.).",
  claymation: "CLAYMATION / STOP-MOTION look. Describe characters and objects sculpted from modeling clay or plasticine, soft matte clay texture with subtle fingerprints and tool marks, slightly imperfect handmade shapes, miniature set with practical props, soft diffuse studio lighting, shallow depth of field, and a charming tactile handcrafted feel.",
  cyberpunk: "CYBERPUNK scene. Describe neon signage, holographic reflections, wet reflective streets, volumetric haze, teal-and-magenta color contrast, futuristic wardrobe and tech, cinematic atmosphere and dramatic mood lighting.",
  darkfantasy: "DARK FANTASY art. Describe a grim, epic and atmospheric medieval-fantasy world, ornate armor and weapons, brooding monstrous or ethereal figures, gothic ruins and twisted landscapes, dramatic chiaroscuro and volumetric god rays, muted desaturated palette with deep shadows and embers, painterly concept-art rendering, and an ominous mythic mood (soulslike / grimdark RPG concept-art feel).",
  editorial: "HIGH-FASHION EDITORIAL photography. Describe a magazine-cover aesthetic, striking confident pose, designer styling and wardrobe, professional studio or location set, dramatic directional lighting and bold shadows, glossy color grading, beauty-retouch skin, and a luxurious aspirational mood worthy of Vogue-style editorial — without naming real people.",
  funko: "FUNKO POP collectible vinyl figure. Describe the signature Funko look: oversized square head, small body, large solid black dot eyes (no pupils), simplified glossy vinyl finish, minimal facial detail. Mention the figure standing, soft studio product lighting, and optionally the classic Funko window box packaging with the character art. Translate the subject's identity into iconic, simplified Funko features.",
  isometrico: "ISOMETRIC 3D render. Describe a precise isometric camera angle (no perspective convergence), tidy miniature-diorama composition, clean stylized geometry, soft ambient occlusion, a vibrant or pastel flat color palette, gentle gradients and soft shadows, and a polished design-asset look ideal for icons, app art, games or infographics.",
  lineart: "LINE ART / TATTOO design. Describe clean confident single-weight or tapered line work, minimalist high-contrast black-on-white composition, no or very limited shading, elegant negative space, smooth flowing curves, fine detail, and a crisp vector-like illustrative quality suitable for a tattoo flash or editorial linework.",
  colorir: "CHILDREN'S COLORING BOOK page. Clean bold BLACK OUTLINES only on a pure WHITE background — NO color, NO shading, NO gradients, NO fills. Thick, smooth, simple lines a young child can color inside; large open areas; rounded friendly shapes; cute, wholesome, age-appropriate characters and settings; minimal background clutter. Think a printable coloring sheet. Keep every character's design consistent and recognizable from page to page. Absolutely wholesome and safe for small children — nothing scary, violent or adult.",
  logo: "LOGO / BRAND IDENTITY design. Describe a clean minimalist vector logo, simple memorable iconography, balanced negative space, a tight modern color palette, scalable flat design, crisp geometry, and a professional brand mark presented on a clean background. Keep it iconic and uncluttered.",
  lowpoly: "LOW POLY 3D art. Describe deliberately faceted low-polygon geometry with visible flat triangular surfaces, simplified stylized forms, flat or gradient color fills per face, crisp edges, minimal texture, soft even lighting, and a clean modern geometric aesthetic popular in indie games and design.",
  mockup: "PRODUCT MOCKUP photography. Describe the product as a realistic packaged item (box, bottle, pouch, label, etc.), clean seamless studio background or minimal lifestyle surface, soft even product lighting with gentle reflections and subtle shadow, sharp focus, professional e-commerce / packaging-design presentation, and accurate material texture (glass, plastic, paper, foil).",
  oleo: "CLASSICAL OIL PAINTING. Describe thick visible impasto brushwork, rich layered glazes, dramatic chiaroscuro lighting, deep saturated earthy tones, canvas texture, masterful rendering of form and fabric, and an Old-Masters / Renaissance or Baroque mood. Convey a museum-quality painterly finish.",
  pixar: "STYLIZED 3D ANIMATED MOVIE render (Pixar/DreamWorks feel). Describe appealing exaggerated-but-charming proportions, large expressive eyes, soft subsurface skin, rounded friendly shapes, polished materials, cinematic three-point lighting, global illumination, gentle depth of field, and a warm, heartfelt, family-film rendered finish.",
  pixelart: "PIXEL ART. Describe a retro 8-bit or 16-bit aesthetic, crisp visible square pixels, a limited and deliberate color palette, dithering for gradients and texture, clean outlines, isometric or side-on game perspective when relevant, and a nostalgic video-game sprite feel. Keep details readable at low resolution.",
  poster: "POSTER / COVER ART design. Describe a striking key-art composition, strong focal hierarchy, integrated bold typography and title treatment, dramatic lighting and color theme, layered depth, and a polished movie-poster or album-cover aesthetic that reads instantly and looks print-ready.",
  comic: "COMIC BOOK / GRAPHIC NOVEL illustration. Describe bold confident ink outlines, dynamic action posing, halftone Ben-Day dots and cross-hatching for shading, flat saturated color fills, dramatic perspective and foreshortening, expressive linework, panel-art energy, and optional speech bubbles or onomatopoeia. Reference a fitting era (golden-age, modern American, European bande dessinée) WITHOUT naming copyrighted characters.",
  realismo: "EXTREME PHOTOREALISM. Specify a real camera body and lens (e.g. Sony A7 IV, 85mm f/1.4), aperture and depth of field, shutter/ISO when relevant, type and direction of lighting (golden hour, softbox, rim light), realistic skin texture with pores and subtle imperfections, fabric and material detail, color grading, film grain, and photographic mood. Avoid any cartoon or illustrated language.",
  scifi: "SCIENCE FICTION concept art. Describe advanced futuristic technology, spacecraft or starships, alien worlds and skylines, sleek hard-surface machinery and hardware, holographic interfaces, vast scale and dramatic perspective, cinematic lighting with cool metallic tones and glowing accents, atmospheric depth, and a polished blockbuster-sci-fi concept-art finish.",
  steampunk: "STEAMPUNK aesthetic. Describe Victorian-era retro-futurism powered by steam and clockwork: polished brass and copper, intricate exposed gears and cogs, riveted iron, pressure gauges, pipes and valves, leather and mahogany, goggles and ornate mechanical contraptions, warm sepia and bronze tones, gaslight glow, billowing steam and a richly detailed industrial-fantasy mood.",
  storyboard: "STORYBOARD MODE. This is a sequential shot-by-shot breakdown of a scene, NOT a single image. Break the user's idea into a clear narrative sequence of distinct frames/shots. Keep strong CONTINUITY across all frames: the same character(s) with consistent appearance and wardrobe, consistent setting, lighting and visual style throughout, so the frames read as one coherent scene. Vary the cinematography frame to frame (establishing wide, medium, close-up, over-the-shoulder, low/high angle, reaction shot) to tell the story with good visual rhythm.",
  thumbnail: "YOUTUBE THUMBNAIL design. Describe a high-impact attention-grabbing composition, an exaggerated expressive face or hero subject, punchy saturated colors and strong contrast, a bold separating outline around the subject, space reserved for big readable headline text, dramatic lighting, and a click-worthy scroll-stopping energy.",
  timelapse: "ACCELERATED TIMELAPSE video. A fixed, locked-off camera compresses hours or days into seconds, showing a subject being built, made, applied or transformed from start to finish. Describe smooth flicker-free time compression, hands and people reduced to blurred streaks, the sun arcing overhead with shadows sweeping across the scene, clouds streaking past, light shifting through the day, and IDENTICAL framing held from the first frame to the last so the transformation reads clearly. The payoff is the finished result revealed and held steady at the end.",
  ugc: "AUTHENTIC UGC (user-generated content) ADVERTISING VIDEO — looks like a real everyday creator filming on their phone, NOT a polished studio commercial. The talent is relatable and natural, talking directly to camera while holding, wearing, using, or showing off the product. Setting is casual and real (bedroom, kitchen, bathroom mirror, car, store aisle, street). Handheld slightly shaky framing, vertical phone footage, natural/window lighting, candid energy, genuine reactions. Build it as a short ad with a clear arc: a scroll-stopping HOOK in the first 2 seconds, a quick PROBLEM or desire, the PRODUCT shown solving it with real close-ups/demonstration, and a punchy CALL-TO-ACTION at the end.",
  vaporwave: "VAPORWAVE / SYNTHWAVE aesthetic. Describe a retro-futuristic 80s/90s digital dreamscape: glowing pink-and-purple neon, magenta-cyan gradients, a luminous laser grid floor receding to the horizon, a giant retro sun with horizontal stripes, chrome and glassy reflective surfaces, palm trees and geometric shapes, VHS scanlines and glitch artifacts, and a nostalgic dreamy synthwave mood.",
  vintage: "VINTAGE / ANALOG photography. Describe an aged film look — Polaroid or 35mm 70s/90s aesthetic, faded warm or slightly off colors, light leaks, soft focus and vignetting, visible film grain and dust, slightly washed contrast, and a nostalgic retro snapshot mood.",
};

function App() {
  const [idea, setIdea] = useState("");
  const [mode, setMode] = useState("generate");
  const [revImage, setRevImage] = useState(null);
  const [revFocus, setRevFocus] = useState("faithful");
  const [revTarget, setRevTarget] = useState("geral");   // formato do prompt no modo fiel
  const [revStyle, setRevStyle] = useState("");          // "" = manter o estilo original; senão id de STYLES
  const [brand, setBrand] = useState("");
  const [audience, setAudience] = useState("");
  const [adScript, setAdScript] = useState("");
  const [charDesc, setCharDesc] = useState("");
  const [charImages, setCharImages] = useState([]);
  const [frameCount, setFrameCount] = useState(4);
  const [cardCount, setCardCount] = useState(6);
  const [colorPages, setColorPages] = useState(6);
  const [carouselGoal, setCarouselGoal] = useState("sell");
  const [tlTotal, setTlTotal] = useState(30);
  const [tlClip, setTlClip] = useState(8);
  const [showPage, setShowPage] = useState(false);
  const [frameImages, setFrameImages] = useState({});
  const [style, setStyle] = useState("realismo");
  const [secondary, setSecondary] = useState(null);
  const [combineOpen, setCombineOpen] = useState(false);
  const [aspect, setAspect] = useState("3:2");
  const [outLang, setOutLang] = useState("en");
  const [loading, setLoading] = useState(false);
  const [etapa, setEtapa] = useState("");                 // progresso do texto longo (várias chamadas)
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const outRef = useRef(null);

  const segCount = Math.max(1, Math.ceil(tlTotal / ((style === "ugc" || style === "cena" || secondary === "cena") ? 8 : tlClip)));

  useEffect(() => {
    if (!canCombineAny(style)) {
      setCombineOpen(false);
      setSecondary(null);
    } else if (secondary && !canCombine(style, secondary)) {
      setSecondary(null);
    }
  }, [style]);

  useEffect(() => {
    if (result && outRef.current) {
      outRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  async function generate() {
    if (!idea.trim()) { setError("Escreva uma ideia primeiro ✍️"); return; }
    const pedido = `${idea} ${adScript || ""} ${charDesc || ""}`;
    if (RE_MENOR.test(pedido)) { setResult(""); setError(MSG_MENORES); return; }
    setError(""); setResult(""); setCopied(false); setShowPage(false); setFrameImages({}); setLoading(true);

    const chosen = STYLES.find((s) => s.id === style);
    const chosen2 = secondary ? STYLES.find((s) => s.id === secondary) : null;
    const isVideo = !!chosen.video;
    const isTimelapse = !!chosen.timelapse;
    const isScene = !!chosen.scene || !!(chosen2 && chosen2.scene);
    const isMotion = isVideo || isTimelapse || isScene;
    const isStoryboard = style === "storyboard" || secondary === "storyboard";
    const isColoring = !!chosen.coloring;
    const isCarousel = !!chosen.carousel || (secondary && STYLES.find((s) => s.id === secondary)?.carousel);
    const lookObj = isStoryboard ? (style === "storyboard" ? chosen2 : chosen) : null;
    const carLook = isCarousel ? (chosen.carousel ? chosen2 : chosen) : null;
    const sceneLook = isScene ? (chosen.scene ? chosen2 : chosen) : null;
    const ugcClip = 8; // UGC/Cena: tamanho fixo de clipe (teto comum das IAs); o usuário só define a duração total
    const clipLen = (isVideo || isScene) ? ugcClip : tlClip;
    const nSeg = Math.max(1, Math.ceil(tlTotal / clipLen));

    const langLine = outLang === "en"
      ? "Write the entire final prompt in ENGLISH (best for AI generators)."
      : "Escreva o prompt final inteiro em PORTUGUÊS do Brasil.";
    const langDirective = outLang === "en"
      ? "CRITICAL OUTPUT LANGUAGE: Write the ENTIRE output in ENGLISH ONLY — every word, including all section labels, spoken lines and captions. This is mandatory even though the user's idea is written in Portuguese. Do NOT output any Portuguese."
      : "IDIOMA DE SAÍDA OBRIGATÓRIO: Escreva TODA a resposta em PORTUGUÊS do Brasil — cada palavra, incluindo rótulos de seção, falas e legendas.";

    const imageReqs = `OUTPUT REQUIREMENTS:
- ${langLine}
- Return ONLY the final prompt text. No explanations, no preamble, no headings, no markdown, no quotes.
- Make it richly detailed: subject, appearance, wardrobe, pose/expression, environment, composition/framing, lighting, color palette, mood, texture/material detail, and rendering/technical specs appropriate to the style.
- Be concrete and visual. Prefer specific nouns and adjectives over vague ones.
- Keep it as a flowing, comma-and-clause description (one cohesive block), 90–160 words.
- After the description, write ONE final line of tags and then STOP. That line starts with --ar ${aspect} followed by AT MOST 5 short tags (1–3 words each) that fit the chosen style. Format example only (pick your own tags for THIS style): --ar ${aspect} --film grain --shallow dof
- Never repeat or rephrase a tag, never turn these instructions into tags, and write nothing after the tag line.
- If the subject implies a real, identifiable person, render them as a generic/fictional likeness — never name real public figures.`;

    const ugcCatBlock = `RESULT / DEMONSTRATION SHOTS (very important): infer the product CATEGORY from the idea and brand, and ALWAYS include the close-up shots that actually SELL that category — showing the product in use and its visible RESULT, not just the package. Apply the matching ones:
- Makeup / cosmetics → macro close-ups of application on skin, lips with light catching the shine, eyes, plus a clear BEFORE-and-AFTER of the treated area.
- Skincare → extreme close-up of skin texture before, the product's spread on skin, and an after glow/hydration result.
- Perfume → close-up of the bottle, the spray gesture and mist, wrist/neck application.
- Hair → close-up of hair texture, the application, and the after shine/volume/movement.
- Food / drink → appetizing macro, steam/pour/texture, and a real bite or sip with genuine reaction.
- Apparel → close-up of fabric texture and stitching, the fit/drape on the body, and movement.
- Tech → close-up of the screen/buttons/key feature actually working, hands interacting.
- Cleaning / home → before-and-after of the surface, the product visibly working.
If the category is unclear, default to: product close-up + the product clearly in use + the visible benefit it delivers.`;

    const videoReqs = nSeg <= 1
      ? `OUTPUT REQUIREMENTS (this is a VIDEO ad prompt for tools like Sora, Veo, Runway, Kling):
- ${langLine}
- Return ONLY the structured prompt below. No extra commentary before or after.
- Structure it EXACTLY with these labeled sections, each on its own lines:

CONCEITO: one sentence describing the overall ad and the creator/talent (relatable, fictional, never a named real person).
REFERÊNCIA: an explicit instruction telling the video tool to use the user's ATTACHED REFERENCE IMAGE as the exact product — keep its real shape, color, logo, label, and proportions consistent across every shot; do not redesign or invent a different product.
FORMATO: vertical ${aspect}, total duration ~${tlTotal}s, authentic phone-shot UGC look.
CENAS: a numbered shot list (4–6 shots). For EACH shot give: the visual (setting, framing, camera move, how the product is held/worn/used, lighting) AND the spoken line the creator says, written naturally and casually. Include at least one slow, stable CLOSE-UP of the product on a clean/uncluttered background.

${ugcCatBlock}
TEXTO NA TELA: 2–4 short on-screen captions/overlays (hook + key benefit + CTA).
ÁUDIO: voiceover tone, ambient sound, and a music vibe suggestion.
CTA: the final spoken + on-screen call to action.

- Keep the energy authentic and conversational, not corporate.
- If a real, identifiable person is implied, use a generic fictional creator — never name real public figures.`
      : `OUTPUT REQUIREMENTS (UGC video ad, SPLIT INTO ${nSeg} SEGMENTS for AI video tools that only make short clips like Sora, Veo, Runway, Kling):
- ${langLine}
- The full ad lasts ~${tlTotal}s and is divided into ${nSeg} short segments (each a few seconds, well within what AI video tools allow), generated separately and stitched together in an editor afterward.
- Return ONLY the structured output below. No extra commentary.

First, one shared block so every segment stays consistent:

BASE (comum a todos os segmentos):
- CRIADOR(A): describe the fictional creator once — look, age range, wardrobe, vibe — so they stay IDENTICAL in every segment (this is critical for the clips to feel like one video).
- PRODUTO/REFERÊNCIA: instruct the tool to use the user's ATTACHED REFERENCE IMAGE as the exact product, keeping its shape, color, logo and label consistent across every segment; never redesign it.
- FORMATO: vertical ${aspect}, authentic phone-shot UGC look, handheld, natural lighting.
- ARCO GERAL: one sentence describing the ad's arc across all segments — hook → problem/desire → product solving it with demo → CTA.

Then produce EXACTLY ${nSeg} segments. Format each one EXACTLY like this, on its own lines:

SEGMENTO 1 de ${nSeg}  ·  (~${tlClip}s)
🎬 CLIPE: a self-contained short UGC clip prompt (a few seconds) ready to paste — restate the creator + product briefly so it works alone, then the visual (setting, framing, how the product is held/used, lighting) for THIS segment.
🗣️ FALA: the exact spoken line(s) the creator says in this segment, natural and casual.
📝 TEXTO NA TELA: the on-screen caption for this segment (if any).
🔗 CONTINUIDADE: one line on what carries over (same outfit, same room, same product state) so the next clip matches seamlessly.

(repeat for SEGMENTO 2 de ${nSeg}, … up to SEGMENTO ${nSeg} de ${nSeg}. Distribute the ad's arc across the segments: the FIRST segment opens with a scroll-stopping HOOK, the middle segments show the problem and the product solving it, and the LAST segment ends with a punchy CTA.)

${ugcCatBlock}
Spread these demonstration close-ups across the segments where they fit naturally.

- ÁUDIO (uma linha no fim): overall voiceover tone and a music vibe for the whole ad.
- CRITICAL CONTINUITY: the creator, wardrobe, room and product must look IDENTICAL across all segments so the stitched clips feel like one seamless video.
- Keep the energy authentic and conversational, not corporate.
- If a Marca/Produto or Público-alvo is provided, weave it into the script and CTA and tailor the creator to the audience.
- If a real, identifiable person is implied, use a generic fictional creator — never name real public figures.`;

    const timelapseReqs = nSeg <= 1
      ? `OUTPUT REQUIREMENTS (accelerated TIMELAPSE video prompt for tools like Sora, Veo, Runway, Kling):
- ${langLine}
- Return ONLY the structured prompt below. No extra commentary.
- Structure EXACTLY with these labeled sections, each on its own lines:

CONCEITO: one sentence describing what is built/made/transformed and the arc from start to finished result.
FORMATO: ${aspect}, accelerated timelapse, ~${tlTotal}s of screen time compressing hours/days of real time.
CÂMERA: a LOCKED-OFF tripod camera holding the exact same framing for the entire sequence — state the precise angle, height, distance and lens.
ETAPAS: a numbered list of 5–8 chronological stages; for EACH, what changes in frame and roughly how long it holds.
MOVIMENTO: time-compression cues — hands/people as blurred streaks, sun arcing, shadows sweeping, clouds racing, light ramping cold→warm→night, flicker-free.
ILUMINAÇÃO: the lighting setup and how it evolves.
ÁUDIO: music vibe plus ambient/whoosh accents.
FINAL: the finished result held steady for a satisfying reveal.

TRANSFORMATION STAGES BY CATEGORY (infer from the idea): Construction → empty lot, foundation, framing, walls/roof, façade, interior, landscaping, reveal. Makeup → bare face, primer/base, contour, eyes, lips, setting, final. Car → chassis, teardown, engine, bodywork, primer, paint, wheels, interior, reveal. PC → parts on desk, motherboard, CPU/RAM, cooler, case, GPU, cable management, RGB boot. Food → ingredients, prep, cooking with steam, plating, finished dish. Painting → blank canvas, sketch, blocking, color, details, signed piece. Renovation → before room, demolition, paint, furniture, styling, final tour. If unclear: before → accelerated work → after held steady.
- CRITICAL: state that the framing stays IDENTICAL from first to last.
- If a real person is implied, use a generic fictional person — never name real public figures.`
      : `OUTPUT REQUIREMENTS (accelerated TIMELAPSE, SPLIT INTO ${nSeg} SEGMENTS for AI video tools that only make ${tlClip}s clips like Sora, Veo, Runway, Kling):
- ${langLine}
- The full timelapse lasts ~${tlTotal}s and is divided into ${nSeg} segments of ~${tlClip}s each, generated separately and stitched together in an editor afterward.
- Return ONLY the structured output below. No extra commentary.

First, one shared block so every segment stays consistent:

BASE (comum a todos os segmentos):
- CÂMERA: a LOCKED-OFF tripod camera with the EXACT SAME framing, angle, height, distance and lens across every segment — the single most important rule for the pieces to stitch seamlessly.
- CENÁRIO/ESTILO: the fixed setting, palette and lighting logic that must stay identical across all segments.
- ARCO GERAL: one sentence describing the whole transformation from the very first frame to the very last finished result.

Then produce EXACTLY ${nSeg} segments. Format each one EXACTLY like this, on its own lines:

SEGMENTO 1 de ${nSeg}  ·  (tempo ~00:00–00:${String(tlClip).padStart(2,"0")})
🎬 CLIPE: a self-contained ~${tlClip}s timelapse prompt ready to paste — restate the locked camera + setting so it works alone, then describe exactly which stage(s) of the transformation happen in THIS segment.
▶️ FRAME INICIAL: describe the exact opening state of this segment (what already exists on screen).
⏹️ FRAME FINAL: describe the exact ending state — this MUST become the FRAME INICIAL of the next segment, so the cut is invisible.
🔗 CONTINUIDADE: one line noting what to carry over (progress level, light/time-of-day, shadow position) so the next clip matches.

(repeat for SEGMENTO 2 de ${nSeg}, … up to SEGMENTO ${nSeg} de ${nSeg}, each covering ~${tlClip}s, so the segments together tell the full ~${tlTotal}s transformation in order)

- CRITICAL CONTINUITY: each segment's FRAME INICIAL must exactly match the previous segment's FRAME FINAL — same camera, same framing, progress only ever moving forward. The lighting/time-of-day should advance smoothly and consistently from segment to segment.
- Spread the transformation stages evenly so the LAST segment ends on the finished result held steady.
- Use the right stages for the inferred CATEGORY (construction, makeup, car, PC, food, painting, renovation, etc.).
- ${langLine}
- If a real person is implied, use a generic fictional person — never name real public figures.`;

    // (de, ate): lote a escrever. Fora do texto longo é sempre o conjunto inteiro
    // (1..total); no texto longo cada chamada escreve só um pedaço do roteiro.
    const carouselReqs = (de, ate) => `OUTPUT REQUIREMENTS (INSTAGRAM CAROUSEL of ${cardCount} cards):
- ${langLine}
- Return ONLY the carousel below. No preamble or commentary.
- GOAL: ${carouselGoal === "sell" ? "storytelling that sells a product/offer — build desire and lead to a purchase/action." : "educational value — teach something useful and highly saveable (tips, steps, mistakes, how-to)."}
- ${de === 1 && ate === cardCount ? `Produce EXACTLY ${cardCount} cards.` : `The carousel has ${cardCount} cards in total; the others are written separately. In THIS reply write ONLY CARD ${de}${ate > de ? ` to CARD ${ate}` : ""}, each one developing its own line of the ROTEIRO in the user request.`} Format each EXACTLY like this:

CARD ${de} — [role, e.g. "Gancho" / "Hook"]
🖼️ VISUAL: [ready-to-paste image prompt for this card's background — subject, composition, style, colors, mood, leaving space for the text overlay. 35–60 words${carLook ? `, in the ${carLook.label} visual style` : ""}.]
✍️ TEXTO: [the exact on-card copy — a bold short headline plus optional 1–2 supporting lines. Punchy, phone-readable.]

(repeat up to CARD ${ate}${ate < cardCount ? ", then STOP" : ""})

- ARC: Card 1 is a scroll-stopping HOOK. Middle cards deliver the story/value. The LAST card is a clear CTA.
- Keep a CONSISTENT visual identity across all cards.
- ${ate === cardCount ? "After the cards add: LEGENDA: [a ready-to-post caption with a hook first line, the core message, light relevant hashtags, and a call to action.]" : "Do NOT write the LEGENDA/caption in this reply."}
- If a Marca/Produto or Público-alvo is provided, tailor copy and offer to them.
- If a real person is implied, use a generic fictional persona — never name real public figures.`;

    // NÚCLEO: as fotos dos personagens vão juntas numa folha só (o motor de visão aceita 1 imagem).
    const sceneReqs = `OUTPUT REQUIREMENTS (MOVIE / CARTOON SCENE prompt for AI video tools like Sora, Veo, Runway, Kling — the scene lasts ~${tlTotal}s${nSeg > 1 ? `, SPLIT INTO ${nSeg} short stitchable segments (~${ugcClip}s each) generated separately and joined in an editor` : ""}):
- ${langLine}
- Return ONLY the structured output below. No preamble or commentary.
${charImages.length ? `- A REFERENCE SHEET with ${charImages.length > 1 ? `${charImages.length} character images side by side` : "the character image"} is attached: base every character's appearance on it and keep it consistent in every segment; do not redesign them.\n` : ""}${charDesc.trim() ? "- Use the character description(s) the user provided.\n" : ""}- First a shared block so every part stays consistent:

BASE (comum a toda a cena):
- PERSONAGENS: describe each character in vivid detail (appearance, wardrobe, vibe)${charImages.length ? ", based on the ATTACHED REFERENCE IMAGES" : ""} so they stay IDENTICAL throughout; restate them in each segment.
- CENÁRIO/ESTILO: the fixed setting, genre, mood and visual style of the scene.
- ARCO DA CENA: one sentence describing the scene's beginning → middle → end.
${nSeg > 1 ? `
Then produce EXACTLY ${nSeg} segments. Format each EXACTLY like this:

SEGMENTO 1 de ${nSeg}  ·  (~${ugcClip}s)
🎬 CLIPE: a self-contained cinematic clip prompt ready to paste — restate the character(s), setting and style, then the shot: camera (shot size, angle, movement), blocking/action, lighting and mood for THIS beat.
💬 AÇÃO/DIÁLOGO: the key action and any spoken lines in this beat (natural, in character).
🔗 CONTINUIDADE: one line on what carries to the next segment (positions, time of day, light, emotional beat) so the cuts flow.

(repeat up to SEGMENTO ${nSeg} de ${nSeg}, so the segments tell the scene in order)
- CRITICAL CONTINUITY: identical characters, setting and style across all segments; the action moves forward beat to beat.` : `
Then write the scene as ONE cohesive, richly detailed cinematic clip prompt ready to paste: restate the character(s), setting and style, then the shot — camera (size, angle, movement), blocking/action, lighting, mood — plus a line of AÇÃO/DIÁLOGO for what happens and anything spoken.`}
- If a real, identifiable person is implied, render a generic fictional likeness — never name real public figures.`;

    const coloringReqs = `OUTPUT REQUIREMENTS (CHILDREN'S COLORING BOOK — a little illustrated story of ${colorPages} pages to color):
- ${langLine}
- Return ONLY the coloring book below. No preamble or commentary.
- First a short shared block:

TÍTULO: a short, sweet title for the story.
HISTÓRIA: one or two simple sentences telling the whole little story arc (beginning → middle → happy ending).
PERSONAGENS: briefly describe the 1–3 recurring characters (simple, cute, friendly) so they stay IDENTICAL on every page.

- Then produce EXACTLY ${colorPages} pages. Format each EXACTLY like this:

PÁGINA 1 — [short scene label]
🖍️ DESENHO: [a ready-to-paste COLORING-BOOK image prompt for this page — bold clean BLACK OUTLINES on pure WHITE, no color, no shading, thick simple lines with large open areas a young child can color; describe the characters (restate their look so the page stands alone), what they are doing, and the simple setting. Age-appropriate and wholesome. 35–70 words. End on a new line with: black and white line art, coloring book page, thick outlines, no shading, --ar ${aspect}]
📖 HISTÓRIA: [one very simple sentence of the story for THIS page, easy for a small child to follow.]

(repeat up to PÁGINA ${colorPages}, so the pages tell the little story in order and end happily)

- CONTINUITY IS CRITICAL: the same characters keep an identical, simple, recognizable design on every page; restate it each time.
- Keep it ABSOLUTELY wholesome and safe for small children: gentle, friendly, nothing scary, dark, violent or adult. Simple everyday adventures (friendship, animals, nature, bedtime, play).
- The book is FOR small children, but its characters are animals, creatures, toys or adults — never children or teenagers (see the MINORS POLICY).
- Every DESENHO must be pure black-outline line art with NO color or shading — a printable coloring sheet.`;

    const storyboardReqs = (de, ate) => `OUTPUT REQUIREMENTS (STORYBOARD — a sequence of ${frameCount} frames):
- ${langLine}
- Return ONLY the storyboard below. No preamble or commentary.
- ${de === 1 && ate === frameCount ? `Produce EXACTLY ${frameCount} frames.` : `The storyboard has ${frameCount} frames in total; the others are written separately. In THIS reply write ONLY QUADRO ${de}${ate > de ? ` to QUADRO ${ate}` : ""}, each one developing its own line of the ROTEIRO in the user request.`} Format each EXACTLY like this:

QUADRO ${de} — [short shot label, e.g. "Plano geral / estabelecimento"]
[A rich, self-contained image prompt for this frame — subject, appearance, wardrobe, action/expression, environment, camera framing and angle, lighting, color palette, mood, and the visual/rendering style. Ready to paste. 45–80 words.]
--ar ${aspect}

(repeat up to QUADRO ${ate}${ate < frameCount ? ", then STOP" : ""})

- CONTINUITY IS CRITICAL: the same character(s) keep identical appearance and wardrobe across every frame; consistent setting, lighting and art style. Restate the key identity details in each frame's prompt so each stands alone.
- Vary the cinematography across frames for good storytelling rhythm.
- Each frame's prompt must be concrete and visual${lookObj ? `, in the ${lookObj.label} style` : ""}.
- If a real person is implied, render a generic fictional likeness — never name real public figures.`;

    let styleBlock;
    if (isColoring) {
      styleBlock = `TARGET: A CHILDREN'S COLORING BOOK with a simple story.\nCOLORING RULES: ${STYLE_BRIEFS.colorir}`;
    } else if (isScene) {
      styleBlock = sceneLook
        ? `TARGET: A MOVIE / CARTOON SCENE in the ${sceneLook.label} style/genre.\nSCENE RULES: ${STYLE_BRIEFS.cena}\n\nSTYLE / GENRE RULES (this defines the aesthetic):\n${STYLE_BRIEFS[sceneLook.id]}`
        : `TARGET: A MOVIE / CARTOON SCENE.\nSCENE RULES: ${STYLE_BRIEFS.cena}\n\nVISUAL STYLE: choose a fitting cinematic look.`;
    } else if (isCarousel) {
      styleBlock = carLook
        ? `TARGET: An INSTAGRAM CAROUSEL with each card's visual in the ${carLook.label} style.\nCAROUSEL RULES: ${STYLE_BRIEFS.carrossel}\n\nVISUAL STYLE RULES:\n${STYLE_BRIEFS[carLook.id]}`
        : `TARGET: An INSTAGRAM CAROUSEL.\nCAROUSEL RULES: ${STYLE_BRIEFS.carrossel}\n\nVISUAL STYLE: clean, modern, cohesive social-media look across all cards.`;
    } else if (isStoryboard) {
      styleBlock = lookObj
        ? `TARGET: A STORYBOARD in the ${lookObj.label} visual style.\nSTORYBOARD RULES: ${STYLE_BRIEFS.storyboard}\n\nVISUAL STYLE RULES:\n${STYLE_BRIEFS[lookObj.id]}`
        : `TARGET: A STORYBOARD.\nSTORYBOARD RULES: ${STYLE_BRIEFS.storyboard}\n\nVISUAL STYLE: clean neutral cinematic look consistent across all frames.`;
    } else if (chosen2) {
      styleBlock = `TARGET STYLE: ${chosen.label} BLENDED WITH ${chosen2.label}.\nPRIMARY STYLE RULES:\n${STYLE_BRIEFS[style]}\n\nSECONDARY STYLE RULES:\n${STYLE_BRIEFS[secondary]}\n\nBLENDING: The primary style defines the medium and execution. The secondary contributes subject, mood, palette or motifs, harmonizing without breaking the primary medium.`;
    } else {
      styleBlock = `TARGET STYLE: ${chosen.label}.\nSTYLE RULES: ${STYLE_BRIEFS[style]}`;
    }

    const job = isColoring ? `a production-ready CHILDREN'S COLORING BOOK of ${colorPages} line-art pages with a simple story`
      : isScene ? (nSeg <= 1 ? "ONE production-ready movie/cartoon scene prompt" : `a production-ready movie/cartoon scene SPLIT INTO ${nSeg} stitchable segments`)
      : isCarousel ? `a production-ready INSTAGRAM CAROUSEL of ${cardCount} cards`
      : isStoryboard ? `a production-ready STORYBOARD of ${frameCount} sequential image prompts`
      : isVideo ? (nSeg <= 1 ? "ONE production-ready video ad prompt" : `a production-ready UGC video ad SPLIT INTO ${nSeg} stitchable segments`)
      : isTimelapse ? (nSeg <= 1 ? "ONE production-ready accelerated timelapse video prompt" : `a production-ready accelerated timelapse SPLIT INTO ${nSeg} stitchable segments`)
      : "ONE extremely detailed, vivid, production-ready image prompt";

    const emLotes = isCarousel || isStoryboard;
    const total = isCarousel ? cardCount : frameCount;
    const reqsDe = (de, ate) => isColoring ? coloringReqs : isScene ? sceneReqs : isCarousel ? carouselReqs(de, ate) : isStoryboard ? storyboardReqs(de, ate) : isVideo ? videoReqs : isTimelapse ? timelapseReqs : imageReqs;

    const systemDe = (de, ate) => `You are an elite prompt engineer for AI ${isMotion ? "video" : "image"} generators${isCarousel ? " and a social-media copywriter" : ""}${isColoring ? " and a gentle children's storyteller" : ""}${isScene ? " and a film director" : ""}.\nYour job: turn a short user idea into ${job}.\n\n${langDirective}\n\n${styleBlock}\n\n${reqsDe(de, ate)}\n\n${REGRA_MENORES}\n\n${langDirective}`;

    const extras = [];
    if (brand.trim()) extras.push(`Marca/Produto: "${brand.trim()}"`);
    if (audience.trim()) extras.push(`Público-alvo: "${audience.trim()}"`);
    if (isVideo && adScript.trim()) extras.push(`Mensagem/roteiro que o usuário QUER no anúncio (use como base obrigatória, adaptando o tom para UGC): "${adScript.trim()}"`);
    if (isScene && charDesc.trim()) extras.push(`Descrição do(s) personagem(ns) (mantenha consistente em toda a cena): "${charDesc.trim()}"`);
    const extrasTxt = extras.length ? "\n" + extras.join("\n") : "";
    const pedido1 = (ideia) => `${systemDe(1, total)}\n\n=== PEDIDO DO USUÁRIO ===\nIdeia do usuário: "${ideia}"${extrasTxt}`;
    const single = !emLotes && !isMotion && !isColoring;
    const optsFinal = { cache: false, modelTier: "default", maxTokens: single ? 500 : (isColoring || isScene) ? 2000 : 1500, onWarning: setError, onText: ({ text }) => setResult(text) };

    try {
      // com foto de personagem a cena vai pro modo VISAO (as fotos viram uma folha só)
      if (isScene && charImages.length) optsFinal.images = [await folhaPersonagens(charImages.map((c) => c.preview))];

      if (idea.trim().length <= IDEIA_LONGA) {
        const text = await askClaude(pedido1(idea.trim()), optsFinal);
        if (text.includes(BLOQ_MENORES)) { setResult(""); setError(MSG_MENORES); }
        else setResult(text);
        return;
      }

      // TEXTO LONGO: condensar → (roteiro → lotes) — ver bloco "TEXTO LONGO" no topo.
      const ctx = await contextoMotor();
      setEtapa("LENDO O TEXTO...");
      const material = await condensar(idea.trim(), ctx, (i, n) => setEtapa(`LENDO O TEXTO · ${i}/${n}...`));

      if (!emLotes) {
        setEtapa("RESUMINDO...");
        const brief = material.length > IDEIA_LONGA ? await askClaude(promptResumo(material, 180), { maxTokens: 500 }) : material;
        setEtapa("");
        const text = await askClaude(pedido1(brief), optsFinal);
        if (text.includes(BLOQ_MENORES)) { setResult(""); setError(MSG_MENORES); }
        else setResult(text);
        return;
      }

      const rotulo = isCarousel ? "CARD" : "QUADRO";
      const rotuloRe = isCarousel ? "CARD" : "(?:QUADRO|FRAME)";
      const nomes = isCarousel ? "CARDS" : "QUADROS";
      setEtapa(`PLANEJANDO ${total} ${nomes}...`);
      const bruto = await askClaude(promptRoteiro(material, rotulo, total, isCarousel), { maxTokens: 700 });
      const linhas = lerRoteiro(bruto, rotuloRe, total);
      const roteiro = linhas
        ? linhas.map((l, i) => `${rotulo} ${i + 1}: ${l || "(continue the sequence naturally)"}`).join("\n")
        : bruto;
      // o molde dos cards/quadros pede um papel curto no cabeçalho; sem isto o modelo copia "[PART 3]"
      const papel = `\n(In each header write a short ${isCarousel ? "role of your own — e.g. Gancho, Problema, Dica, Exemplo, CTA" : "shot label of your own — e.g. Plano geral, Plano médio, Close-up"} — never the words PART or ROTEIRO.)`;

      // Tamanho do lote: quantos itens cabem no que sobra do contexto (no máx. 3 —
      // modelo pequeno perde o formato e a contagem em respostas compridas).
      const porItem = isCarousel ? 210 : 190;
      const livre = ctx - 336 - Math.ceil((systemDe(1, total).length + roteiro.length + extrasTxt.length + 1400) / 3.2);
      const lote = Math.max(1, Math.min(3, Math.floor((livre - 280) / porItem)));

      let acumulado = "", referencia = "";
      for (let de = 1; de <= total; de += lote) {
        const ate = Math.min(total, de + lote - 1);
        const ultimo = ate === total;
        setEtapa(`${nomes} ${de}${ate > de ? `–${ate}` : ""} DE ${total}...`);
        const entrada = `${systemDe(de, ate)}\n\n=== PEDIDO DO USUÁRIO ===\nROTEIRO (planejado a partir do texto longo do usuário — uma linha por ${rotulo}):\n${roteiro}${papel}${extrasTxt}`
          + (referencia ? `\n\nALREADY WRITTEN — ${rotulo} 1, for reference only (keep the SAME visual identity, characters and style; do NOT rewrite it):\n${referencia}` : "");
        let parte;
        try {
          parte = await askClaude(entrada, { maxTokens: Math.min(2000, (ate - de + 1) * porItem + (ultimo ? 280 : 0) + 120), onWarning: setError });
        } catch (e) {
          if (!acumulado) throw e;
          setError(`A geração parou no ${rotulo} ${de} de ${total}. O que já estava pronto ficou abaixo — tente gerar de novo.`);
          return;
        }
        if (parte.includes(BLOQ_MENORES)) { setResult(""); setError(MSG_MENORES); return; }
        parte = apararLote(parte, rotuloRe, ate, ultimo) || parte;
        if (!referencia) referencia = parte.split(new RegExp(`\\n(?=\\W*${rotuloRe}\\s*\\d+)`, "i"))[0].slice(0, 700);
        acumulado = acumulado ? `${acumulado}\n\n${parte}` : parte;
        setResult(acumulado);
      }
      // O último lote às vezes termina no CTA e esquece a legenda: pede só ela.
      if (isCarousel && !/^\W*(LEGENDA|CAPTION)\b/im.test(acumulado)) {
        setEtapa("LEGENDA...");
        try {
          const leg = await askClaude(`You are a social-media copywriter. ${outLang === "en" ? "Write in ENGLISH." : "Escreva em PORTUGUÊS do Brasil."}\nWrite ONLY the ready-to-post Instagram caption for the carousel planned below: a hook first line, the core message in 2–3 short sentences, a call to action and 3–5 relevant hashtags. No preamble, no card list.\n\nROTEIRO:\n${roteiro}${extrasTxt}`, { maxTokens: 320 });
          if (!leg.includes(BLOQ_MENORES)) setResult(`${acumulado}\n\nLEGENDA: ${leg.replace(/^\W*(LEGENDA|CAPTION)\s*:?\s*/i, "")}`);
        } catch (_) {}
      }
    } catch (e) {
      setResult("");
      setError(sampleErrMsg(e));
    } finally {
      setEtapa("");
      setLoading(false);
    }
  }

  function handleRevImage(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      const img = new Image();
      img.onload = () => {
        // proporção REAL da imagem (vai pro prompt e pro --ar do Midjourney)
        const w = img.naturalWidth, h = img.naturalHeight;
        let preview = dataUrl;
        // imagens enormes: reduz antes de enviar (o modelo de visão enxerga ~896 px de qualquer jeito)
        const MAX = 1600;
        if (Math.max(w, h) > MAX) {
          const k = MAX / Math.max(w, h), cv = document.createElement("canvas");
          cv.width = Math.round(w * k); cv.height = Math.round(h * k);
          cv.getContext("2d").drawImage(img, 0, 0, cv.width, cv.height);
          preview = cv.toDataURL("image/jpeg", 0.92);
        }
        setRevImage({ file: file, preview: preview, w: w, h: h, ratio: proporcao(w, h) });
        setError("");
      };
      img.onerror = () => { setRevImage({ file: file, preview: dataUrl }); setError(""); };
      img.src = dataUrl;
    };
    reader.readAsDataURL(file);
  }

  function handleCharImages(fileList) {
    if (!fileList || !fileList.length) return;
    const files = Array.from(fileList).slice(0, 4);
    Promise.all(files.map((f) => new Promise((res) => {
      const r = new FileReader();
      r.onload = (e) => res({ file: f, preview: e.target.result });
      r.readAsDataURL(f);
    }))).then((imgs) => setCharImages((prev) => [...prev, ...imgs].slice(0, 4)));
  }

  async function reverseEngineer() {
    if (!revImage) { setError("Envie uma imagem primeiro 🖼️"); return; }
    setError(""); setResult(""); setCopied(false); setShowPage(false); setFrameImages({}); setLoading(true);

    const langLine = outLang === "en" ? "Write the entire output in ENGLISH (best for AI generators)." : "Escreva toda a saída em PORTUGUÊS do Brasil.";
    const focusLine = revFocus === "faithful"
      ? "GOAL: reverse-engineer a prompt that would RECREATE this exact image as faithfully as possible."
      : "GOAL: extract mainly the STYLE, technique, lighting and mood of this image so the user can apply that look to a DIFFERENT subject.";

    const system = `You are an expert reverse-prompt engineer for AI image generators. Analyze the given image deeply and produce a prompt that could reproduce its look.\n\n${focusLine}\n\n${langLine}\n\nReturn your answer in EXACTLY this structure:\n\nPROMPT:\n[One cohesive, comma-separated prompt block ready to paste — 80–150 words, covering subject, style/medium, composition, lighting, color, mood and technical cues. End with fitting tags on a new line.]\n\nANÁLISE:\n• Estilo/Meio: [...]\n• Cenário/Local: [...]\n• Composição/Enquadramento: [...]\n• Personagens/Sujeito: [describe people GENERICALLY, never identify real individuals]\n• Iluminação: [...]\n• Cores/Paleta: [...]\n• Clima/Atmosfera: [...]\n• Técnica/Render: [...]\n\nRULES:\n- ${langLine}\n- Keep the labels PROMPT: and ANÁLISE: exactly.\n- NEVER name or guess the identity of any real person.\n- ${REGRA_MENORES}\n- Be concrete; infer plausible technical details from visual evidence.`;

    const input = `${system}\n\nAnalise a imagem anexada seguindo exatamente a estrutura e as regras acima.`;

    if (revFocus === "faithful") {
      // 2 passadas: inventário (ver) → prompt (escrever), num pedido só ao motor local
      const { etapa1, etapa2 } = promptsFiel(langLine, revImage, revTarget, revStyle);
      let inventario = "";
      try {
        let text = await askClaude(etapa1, {
          images: [revImage.preview], maxTokens: 900, etapa2: etapa2, maxTokens2: 1000,
          onWarning: setError, onInventario: (inv) => { inventario = inv; },
        });
        if (temMenor(inventario) || text.includes(BLOQ_MENORES)) {
          setResult(""); setError(MSG_MENORES_IMG);
          return;
        }
        const reforco = reforcarFiel(text, inventario, revTarget, outLang, revStyle);
        text = reforco.text;
        const ar = revImage.ratio ? revImage.ratio.ar : "";
        if (revTarget === "mj" && ar) {
          // --ar exato, deterministico (o modelo nao escreve parametros)
          text = text.replace(/(PROMPT:\s*\n?)([\s\S]*?)(\n\s*NEGATIVE PROMPT:|$)/i,
            (m, a, corpo, b) => `${a}${corpo.trim().replace(/\s*--\S+.*$/gm, "")} --ar ${ar}\n${b}`);
        }
        const dica = outLang === "en"
          ? "TIP: text alone does not lock the exact pose or face. For maximum fidelity, also give the original image to your generator as a reference (image-to-image, ControlNet/OpenPose for the pose, or a character/style reference)."
          : "DICA: só texto não fixa a pose nem o rosto exatos. Para fidelidade máxima, use também a imagem original como referência no seu gerador (image-to-image, ControlNet/OpenPose para a pose, ou referência de personagem/estilo).";
        const cab = outLang === "en" ? "INVENTORY (what the AI saw — check it):" : "INVENTÁRIO (o que a IA viu — confira):";
        const estiloObj = revStyle && STYLES.find((s) => s.id === revStyle);
        const linhaEstilo = estiloObj ? `\n\nESTILO: reimaginado como ${estiloObj.label} (pose, orientação e composição preservadas)` : "";
        const linhaAvisos = reforco.avisos.length ? `\n\nAJUSTES AUTOMÁTICOS:\n• ${reforco.avisos.join("\n• ")}` : "";
        setResult(`${text.trim()}${ar ? `\n\nPROPORÇÃO: ${ar} (${revImage.w}×${revImage.h})` : ""}${linhaEstilo}${linhaAvisos}\n\n${cab}\n${inventario.trim()}\n\n${dica}`);
      } catch (e) {
        setResult("");
        setError(sampleErrMsg(e));
      } finally {
        setLoading(false);
      }
      return;
    }

    try {
      const text = await askClaude(input, {
        images: [revImage.preview],
        cache: false,
        modelTier: "default",
        maxTokens: 900,
        onWarning: setError,
        onText: ({ text }) => setResult(text),
      });
      if (text.includes(BLOQ_MENORES)) { setResult(""); setError(MSG_MENORES_IMG); }
      else setResult(text);
    } catch (e) {
      setResult("");
      setError(sampleErrMsg(e));
    } finally {
      setLoading(false);
    }
  }

  function parseFrames(text) {
    if (!text) return [];
    const parts = text.split(/(?=(?:QUADRO|PÁGINA|PAGINA)\s*\d+)/i).filter((p) => /^(?:QUADRO|PÁGINA|PAGINA)\s*\d+/i.test(p.trim()));
    return parts.map((block, i) => {
      const lines = block.trim().split("\n");
      const header = (lines[0] || "").trim() || `${i + 1}`;
      const body = lines.slice(1).join("\n").trim();
      const m = header.match(/(?:QUADRO|PÁGINA|PAGINA)\s*(\d+)\s*[—\-–:]*\s*(.*)/i);
      return { num: (m && m[1]) || String(i + 1), label: ((m && m[2]) || "").trim(), prompt: body };
    });
  }

  function handleFrameImage(idx, file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => setFrameImages((prev) => ({ ...prev, [idx]: e.target.result }));
    reader.readAsDataURL(file);
  }

  function copyResult() {
    if (!result) return;
    const ta = document.createElement("textarea");
    ta.value = result;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); setCopied(true); setTimeout(() => setCopied(false), 1800); } catch (e) {}
    document.body.removeChild(ta);
  }

  const primaryObj = STYLES.find((s) => s.id === style);
  const secondaryObj = secondary ? STYLES.find((s) => s.id === secondary) : null;
  const allowCombine = canCombineAny(style) && !(primaryObj && primaryObj.video);
  const storyboardActive = style === "storyboard" || secondary === "storyboard";
  const carouselActive = (primaryObj && primaryObj.carousel) || (secondaryObj && secondaryObj.carousel);
  const timelapseActive = primaryObj && primaryObj.timelapse;
  const coloringActive = primaryObj && primaryObj.coloring;
  const ugcActive = primaryObj && primaryObj.video;
  const sceneActive = (primaryObj && primaryObj.scene) || (secondaryObj && secondaryObj.scene);
  const pageAssembly = storyboardActive || coloringActive;
  const fmtDur = (s) => (s % 60 === 0 && s >= 60 ? (s / 60) + "min" : s + "s");

  const L = { mono: { fontFamily: "'DM Mono', monospace" }, black: { fontFamily: "'Archivo Black', sans-serif" }, sans: { fontFamily: "'DM Sans', sans-serif" } };

  return (
    <div className="min-h-screen w-full text-[#f4ede0]" style={{ background: "#0f0d0a", ...L.sans }}>
      <style>{`
        /* fontes: do sistema (offline; Google Fonts removido) */
        @keyframes pulseDot { 0%,100%{opacity:.25;transform:scale(.8)} 50%{opacity:1;transform:scale(1.2)} }
        @keyframes riseIn { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
        .rise { animation: riseIn .5s cubic-bezier(.2,.8,.2,1) both; }
        .grain:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.04;z-index:50;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}
      `}</style>
      <div className="grain" />
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-32 -left-24 h-96 w-96 rounded-full blur-3xl" style={{ background: "radial-gradient(circle,#ff7a18,transparent 70%)", opacity: .06 }} />
        <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full blur-3xl" style={{ background: "radial-gradient(circle,#ff7a18,transparent 70%)", opacity: .05 }} />
      </div>

      <div className="relative z-10 mx-auto max-w-3xl px-5 py-10 sm:py-14">
        <header className="mb-9">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#ff7a18]/30 bg-[#ff7a18]/10 px-3 py-1 text-xs tracking-wide" style={L.mono}>
            <span className="h-2 w-2 rounded-full bg-[#ff7a18]" style={{ animation: "pulseDot 1.6s infinite" }} />
            GERADOR DE PROMPTS · IA
          </div>
          <h1 className="text-4xl leading-[0.95] sm:text-6xl" style={{ ...L.black, letterSpacing: "-0.02em" }}>
            FORJA DE<br /><span className="text-[#ff7a18]">PROMPTS</span>
          </h1>
          <p className="mt-3 max-w-lg text-sm text-[#8c8475] sm:text-base">
            Digite uma ideia simples, escolha o estilo (ou misture dois!) e receba um prompt cinematográfico, detalhado e pronto pra colar.
          </p>
        </header>

        <div className="mb-6 grid grid-cols-2 gap-2 rounded-2xl border border-[#2a2620] bg-[#161310] p-1.5">
          {[["generate", "⚒ Gerar", "ideia → prompt"], ["reverse", "🔍 Engenharia reversa", "imagem → prompt"]].map(([v, label, sub]) => (
            <button key={v} onClick={() => { setMode(v); setResult(""); setError(""); }}
              className={`rounded-xl px-3 py-2.5 text-center transition ${mode === v ? "bg-[#ff7a18] text-[#1a1206]" : "text-[#8c8475] hover:text-[#f4ede0]"}`}>
              <div className="text-sm font-bold" style={L.black}>{label}</div>
              <div className={`text-[10px] ${mode === v ? "text-[#1a1206]/70" : "text-[#6e675b]"}`} style={L.mono}>{sub}</div>
            </button>
          ))}
        </div>

        {mode === "generate" && (<>
          <label className="mb-2 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Sua ideia</label>
          <textarea value={idea} onChange={(e) => setIdea(e.target.value)}
            placeholder={primaryObj && primaryObj.video ? "ex: anúncio de um sérum facial; criadora mostrando o resultado na pele..." : timelapseActive ? "ex: construção de uma casa do zero num terreno vazio... / maquiagem completa do rosto limpo até o look final... / montagem de um PC gamer na bancada..." : carouselActive ? "ex: 5 erros que estão matando suas vendas no Instagram... / como meu produto transformou a rotina de skincare da cliente..." : coloringActive ? "ex: um ursinho que perde seu balão e faz amigos pra encontrá-lo... / a coelhinha que planta uma horta com os amigos..." : sceneActive ? "ex: o herói encara o vilão no topo da torre enquanto a chuva cai... / dois amigos fogem correndo de um robô gigante pelo beco..." : "ex: uma guerreira ruiva sob a chuva numa cidade antiga..."}
            rows={3} className="w-full resize-none rounded-2xl border border-[#2a2620] bg-[#141210] p-4 text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" />
          {idea.trim().length > IDEIA_LONGA && (
            <p className="mt-2 text-[11px] leading-snug text-[#8c8475]" style={L.mono}>
              📚 Texto longo: a Forja primeiro condensa o texto{carouselActive || storyboardActive ? `, planeja um roteiro e escreve os ${carouselActive ? "cards" : "quadros"} em lotes` : " e depois escreve o prompt"}. Leva mais tempo que uma ideia curta.
            </p>
          )}

          {primaryObj && primaryObj.video && (
            <p className="mt-2 rounded-xl border border-[#ff7a18]/25 bg-[#ff7a18]/5 px-3 py-2 text-[12px] leading-snug text-[#8c8475]">
              💡 O roteiro já inclui a instrução de <b>usar a foto do produto como referência</b>. Anexe a imagem do produto na ferramenta de vídeo usando o recurso de <i>imagem de referência / image-to-video</i>.
            </p>
          )}
          {timelapseActive && (
            <p className="mt-2 rounded-xl border border-[#ff7a18]/25 bg-[#ff7a18]/5 px-3 py-2 text-[12px] leading-snug text-[#8c8475]">
              ⏱️ Detecta o <b>tipo de projeto</b> e monta as etapas certas, com <b>câmera travada</b>. Timelapses longos são <b>fatiados em segmentos</b> que emendam, respeitando o limite de clipe das IAs.
            </p>
          )}

          {(( primaryObj && primaryObj.video) || carouselActive) && (
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Marca / Produto <span className="text-[#6e675b] normal-case">(opcional)</span></label>
                <input value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="ex: Loja Aurora — jaqueta corta-vento" className="w-full rounded-xl border border-[#2a2620] bg-[#141210] px-3 py-2.5 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Público-alvo <span className="text-[#6e675b] normal-case">(opcional)</span></label>
                <input value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="ex: mulheres 25-40 que treinam ao ar livre" className="w-full rounded-xl border border-[#2a2620] bg-[#141210] px-3 py-2.5 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" />
              </div>
            </div>
          )}

          {primaryObj && primaryObj.video && (
            <div className="mt-3">
              <label className="mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Texto / Mensagem do anúncio <span className="text-[#6e675b] normal-case">(opcional)</span></label>
              <textarea value={adScript} onChange={(e) => setAdScript(e.target.value)} placeholder="ex: Fale sobre o desconto de 30% só essa semana; mencione que tem frete grátis; termine com 'corre que acaba rápido!'" rows={3} className="w-full resize-none rounded-xl border border-[#2a2620] bg-[#141210] p-3 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" />
              <p className="mt-1.5 text-[11px] leading-snug text-[#8c8475]" style={L.mono}>Deixe vazio pra IA criar o roteiro do zero, ou escreva as falas/pontos que devem aparecer.</p>
            </div>
          )}

          {sceneActive && (
            <div className="mt-3 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-1.5 block text-xs uppercase tracking-widest text-[#ff9a6a]" style={L.mono}>🎭 Personagens <span className="text-[#6e675b] normal-case">(opcional)</span></label>
              <textarea value={charDesc} onChange={(e) => setCharDesc(e.target.value)} placeholder="ex: Léo, detetive de 40 anos, barba grisalha, sobretudo marrom. Mia, raposa laranja falante com lenço azul." rows={2} className="w-full resize-none rounded-xl border border-[#2a2620] bg-[#141210] p-3 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" />
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {charImages.map((c, i) => (
                  <div key={i} className="relative h-16 w-16 overflow-hidden rounded-lg border-2 border-[#2a2620]">
                    <img src={c.preview} alt="" className="h-full w-full object-cover" />
                    <button onClick={() => setCharImages((prev) => prev.filter((_, j) => j !== i))} className="absolute right-0 top-0 flex h-5 w-5 items-center justify-center bg-[#0f0d0a]/80 text-[11px] font-black text-white">×</button>
                  </div>
                ))}
                {charImages.length < 4 && (
                  <label className="flex h-16 w-16 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-[#4a4338] text-center text-[#8c8475] transition hover:border-[#ff7a18]/60">
                    <span className="text-lg leading-none">＋</span>
                    <span className="mt-0.5 text-[9px]" style={L.mono}>imagem</span>
                    <input type="file" accept="image/*" multiple className="hidden" onChange={(e) => handleCharImages(e.target.files)} />
                  </label>
                )}
              </div>
              <p className="mt-2 text-[11px] leading-snug text-[#8c8475]">Suba fotos de referência dos personagens (até 4) <b>e/ou</b> descreva-os. A IA usa isso pra manter a mesma cara em toda a cena.</p>
            </div>
          )}

          <label className="mb-2 mt-7 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Estilo principal</label>
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
            {STYLES.map((s) => {
              const active = s.id === style;
              return (
                <button key={s.id} onClick={() => { setStyle(s.id); if (s.video) setAspect("9:16"); if (s.timelapse) setAspect("16:9"); if (s.carousel) setAspect("4:5"); if (s.coloring) setAspect("2:3"); if (s.scene) setAspect("16:9"); }}
                  className={`group relative rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 shadow-[0_0_20px_rgba(255,122,24,0.25)] -translate-y-0.5" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}`}>
                  {active && <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ff7a18] text-[11px] font-black text-[#1a1206]">✓</span>}
                  <div className="flex items-center gap-2"><span className="text-lg">{s.tag}</span><span className={`text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}`}>{s.label}</span></div>
                  <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}`}>{s.hint}</p>
                </button>
              );
            })}
          </div>

          {allowCombine && (
            <div className="mt-5">
              <button onClick={() => { if (combineOpen) { setCombineOpen(false); setSecondary(null); } else setCombineOpen(true); }}
                className={`flex w-full items-center justify-center gap-2 rounded-2xl border-2 px-4 py-3 text-sm font-bold transition ${combineOpen || secondary ? "border-[#ff7a18] bg-[#ff7a18]/10 text-[#ff9a6a]" : "border-dashed border-[#4a4338] bg-transparent text-[#8c8475] hover:border-[#ff7a18]/60 hover:text-[#ff9a6a]"}`} style={L.mono}>
                {combineOpen || secondary ? "✕ Remover combinação" : "+ Combinar com outro estilo"}
              </button>
              {combineOpen && (
                <div className="rise mt-4">
                  <label className="mb-2 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Segundo estilo (mistura)</label>
                  <p className="mb-3 text-[11px] text-[#8c8475]" style={L.mono}>Opções esmaecidas são incompatíveis com <span className="text-[#ff9a6a]">{primaryObj && primaryObj.label}</span>.</p>
                  <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                    {STYLES.map((s) => {
                      if (s.id === style) return null;
                      const compatible = canCombine(style, s.id);
                      const active = s.id === secondary;
                      return (
                        <button key={s.id} disabled={!compatible} onClick={() => setSecondary(s.id)} title={compatible ? "" : `Incompatível com ${primaryObj && primaryObj.label}`}
                          className={`group relative rounded-2xl border-2 p-3 text-left transition ${!compatible ? "cursor-not-allowed border-[#2a2620] bg-[#0f0d0a] opacity-30" : active ? "border-[#ff7a18] bg-[#ff7a18]/15 ring-2 ring-[#ff7a18]/40 shadow-[0_0_20px_rgba(255,209,102,0.2)] -translate-y-0.5" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}`}>
                          {active && <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ff7a18] text-[11px] font-black text-[#1a1206]">✓</span>}
                          <div className="flex items-center gap-2"><span className="text-lg">{s.tag}</span><span className={`text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}`}>{s.label}</span></div>
                          <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}`}>{s.hint}</p>
                        </button>
                      );
                    })}
                  </div>
                  {secondaryObj && (
                    <div className="rise mt-4 rounded-xl border border-[#ff7a18]/30 bg-gradient-to-r from-[#ff7a18]/10 to-[#ff7a18]/10 px-4 py-3 text-sm">
                      <span className="text-[#8c8475]">Misturando:</span> <span className="font-bold text-[#ff7a18]">{primaryObj.tag} {primaryObj.label}</span><span className="mx-2 text-[#ff9a6a]">+</span><span className="font-bold text-[#ff9a6a]">{secondaryObj.tag} {secondaryObj.label}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {(timelapseActive || (primaryObj && primaryObj.video) || sceneActive) && (
            <div className="rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#ff9a6a]" style={L.mono}>⏱️ {sceneActive ? "Duração aproximada da cena" : "Duração total do vídeo"}</label>
              <div className="flex flex-wrap items-center gap-1.5">
                {TL_TOTALS.map(([v, l]) => (
                  <button key={v} onClick={() => setTlTotal(v)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === tlTotal ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{l}</button>
                ))}
                {(ugcActive || sceneActive) && (
                  <span className="ml-1 inline-flex items-center gap-1.5 rounded-lg border-2 border-[#2a2620] px-2 py-1" style={L.mono}>
                    <span className="text-[11px] text-[#8c8475]">ou</span>
                    <input
                      type="number" min="5" max="600" step="1" value={tlTotal}
                      onChange={(e) => { const n = parseInt(e.target.value, 10); if (!isNaN(n)) setTlTotal(Math.min(600, Math.max(5, n))); }}
                      className="w-16 bg-transparent text-center text-xs font-bold text-[#ff9a6a] outline-none"
                    />
                    <span className="text-[11px] text-[#8c8475]">seg</span>
                  </span>
                )}
              </div>
              {timelapseActive && (<>
                <label className="mb-2 mt-5 block text-xs uppercase tracking-widest text-[#ff9a6a]" style={L.mono}>Duração de cada clipe da IA</label>
                <div className="flex flex-wrap gap-1.5">
                  {TL_CLIPS.map((n) => (
                    <button key={n} onClick={() => setTlClip(n)} className={`rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === tlClip ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{n}s</button>
                  ))}
                </div>
              </>)}
              <p className="mt-3 text-[11px] leading-snug text-[#8c8475]">
                {segCount <= 1 ? (<>Cabe em <b className="text-[#ff9a6a]">1 clipe</b> só — roteiro único.</>) : timelapseActive ? (<>Vai gerar <b className="text-[#ff9a6a]">{segCount} segmentos</b> de ~{tlClip}s que emendam, cada um com frame inicial/final pra continuidade perfeita. Você gera clipe por clipe e junta no editor.</>) : sceneActive ? (<>Pra ~{fmtDur(tlTotal)}, vai gerar <b className="text-[#ff9a6a]">{segCount} segmentos</b> curtos que emendam, com os mesmos personagens e cenário. Você gera clipe por clipe e junta no editor.</>) : (<>Pra ~{fmtDur(tlTotal)}, vai gerar <b className="text-[#ff9a6a]">{segCount} segmentos</b> curtos que emendam, com a mesma criadora e produto em todos. Você gera clipe por clipe e junta no editor.</>)}
              </p>
            </div>
          )}

          {coloringActive && (
            <div className="rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#ff9a6a]" style={L.mono}>🖍️ Quantas páginas?</label>
              <div className="flex flex-wrap gap-1.5">
                {[4, 6, 8, 10, 12].map((n) => (
                  <button key={n} onClick={() => setColorPages(n)} className={`rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === colorPages ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{n}</button>
                ))}
              </div>
              <p className="mt-2.5 text-[11px] leading-snug text-[#8c8475]">Gera um livrinho de <b className="text-[#ff9a6a]">{colorPages} páginas</b> pra colorir, com uma historinha simples e os mesmos personagens. Cada página vem com o desenho (traço pra pintar) e uma frase da história. Use <b className="text-[#ff9a6a]">📖 Montar página</b> no resultado pra montar o livro impresso.</p>
            </div>
          )}

          {storyboardActive && (
            <div className="rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#ff9a6a]" style={L.mono}>🎬 Quantos quadros?</label>
              <div className="flex flex-wrap gap-1.5">
                {[3, 4, 5, 6, 7, 8].map((n) => (
                  <button key={n} onClick={() => setFrameCount(n)} className={`rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === frameCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{n}</button>
                ))}
              </div>
              <p className="mt-2.5 text-[11px] leading-snug text-[#8c8475]">O storyboard gera <b className="text-[#ff9a6a]">{frameCount} prompts</b> em sequência, com continuidade. {secondaryObj ? "" : "💡 Combine com um estilo visual pra definir o look dos quadros."}</p>
            </div>
          )}

          {carouselActive && (
            <div className="rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#ff9a6a]" style={L.mono}>🎠 Objetivo do carrossel</label>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {[["sell", "🛍️ Storytelling / Venda", "Cria desejo e leva à ação"], ["educate", "💡 Educativo / Dicas", "Ensina algo salvável"]].map(([v, label, sub]) => {
                  const active = carouselGoal === v;
                  return (
                    <button key={v} onClick={() => setCarouselGoal(v)} className={`rounded-xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}`}>
                      <div className={`text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}`}>{label}</div>
                      <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}`}>{sub}</p>
                    </button>
                  );
                })}
              </div>
              <label className="mb-2 mt-5 block text-xs uppercase tracking-widest text-[#ff9a6a]" style={L.mono}>Quantos cards?</label>
              <div className="flex flex-wrap gap-1.5">
                {[3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <button key={n} onClick={() => setCardCount(n)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${n === cardCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{n}</button>
                ))}
              </div>
              <p className="mt-2.5 text-[11px] leading-snug text-[#8c8475]">Gera <b className="text-[#ff9a6a]">{cardCount} cards</b> (visual + copy) do gancho ao CTA, mais uma legenda pronta pra postar. {secondaryObj ? "" : "💡 Combine com um estilo visual pra definir o look dos cards."}</p>
            </div>
          )}

          <div className="mt-7 flex flex-wrap items-end gap-6">
            <div>
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Proporção</label>
              <div className="flex flex-wrap gap-1.5">
                {ASPECTS.map((a) => (
                  <button key={a} onClick={() => setAspect(a)} className={`rounded-lg border-2 px-2.5 py-1.5 text-xs font-bold transition ${a === aspect ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{a}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Idioma do prompt</label>
              <div className="flex gap-1.5">
                {[["en", "Inglês"], ["pt", "Português"]].map(([v, l]) => (
                  <button key={v} onClick={() => setOutLang(v)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{l}</button>
                ))}
              </div>
            </div>
          </div>

          <button onClick={generate} disabled={loading} className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60" style={{ ...L.black, letterSpacing: "0.01em" }}>
            {loading ? (<><span className="h-2 w-2 rounded-full bg-[#1a1206]" style={{ animation: "pulseDot 1s infinite" }} />{etapa || "FORJANDO..."}</>) : (<>⚒ GERAR PROMPT</>)}
          </button>
          {error && <p className="mt-3 text-center text-sm text-[#ff8c3a]">{error}</p>}
        </>)}

        {mode === "reverse" && (
          <div>
            <label className="mb-2 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Imagem de referência</label>
            <label className="relative block cursor-pointer">
              <div className="flex min-h-[180px] items-center justify-center rounded-2xl border-2 border-dashed border-[#4a4338] bg-[#161310] bg-contain bg-center bg-no-repeat p-4 transition hover:border-[#ff7a18]/60" style={revImage ? { backgroundImage: `url(${revImage.preview})`, minHeight: "280px" } : {}}>
                {!revImage && (<div className="text-center"><div className="text-4xl">🖼️</div><div className="mt-2 text-sm font-bold text-[#8c8475]">Clique pra enviar uma imagem</div><div className="mt-1 text-[11px] text-[#8c8475]" style={L.mono}>PNG, JPG ou WEBP</div></div>)}
              </div>
              <input type="file" accept="image/*" className="hidden" onChange={(e) => handleRevImage(e.target.files && e.target.files[0])} />
            </label>
            {revImage && <button onClick={() => setRevImage(null)} className="mt-2 text-[11px] text-[#8c8475] underline transition hover:text-[#ff8c3a]" style={L.mono}>remover imagem</button>}

            <label className="mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Foco da análise</label>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {[["faithful", "🎯 Recriar fiel", "Reproduz a imagem o mais parecido possível"], ["style", "🎨 Capturar estilo", "Extrai só o 'look' pra usar em outra ideia"]].map(([v, label, sub]) => {
                const active = revFocus === v;
                return (
                  <button key={v} onClick={() => setRevFocus(v)} className={`rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 -translate-y-0.5" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}`}>
                    <div className={`text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}`}>{label}</div>
                    <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}`}>{sub}</p>
                  </button>
                );
              })}
            </div>

            {revFocus === "faithful" && (<>
              <label className="mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Formato do prompt</label>
              <div className="flex flex-wrap gap-1.5">
                {[["geral", "Texto corrido (Flux, DALL·E, Ideogram)"], ["mj", "Midjourney (--ar)"], ["sd", "Stable Diffusion (tags)"]].map(([v, l]) => (
                  <button key={v} onClick={() => setRevTarget(v)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === revTarget ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{l}</button>
                ))}
              </div>
              <p className="mt-2 text-[11px] leading-snug text-[#8c8475]" style={L.mono}>
                Fiel = 2 passadas: a IA primeiro faz um inventário do que vê (tipo de imagem, enquadramento, pose, roupas, local, luz…) e depois escreve o prompt só com isso. Leva ~2× mais tempo.
                {revImage && revImage.ratio ? ` Proporção detectada: ${revImage.ratio.ar} (${revImage.w}×${revImage.h}).` : ""}
              </p>

              <label className="mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Estilo do resultado</label>
              <select value={revStyle} onChange={(e) => setRevStyle(e.target.value)} className="w-full rounded-lg border-2 border-[#2a2620] bg-[#161310] px-3 py-2 text-sm font-bold text-[#bdb3a3] outline-none transition hover:border-[#4a4338] focus:border-[#ff7a18]" style={L.mono}>
                <option value="">🎯 Manter o estilo original da imagem</option>
                {STYLES.filter((s) => !["format", "video", "scene", "coloring"].includes(STYLE_CATEGORIES[s.id])).map((s) => (
                  <option key={s.id} value={s.id}>{s.tag} {s.label} — {s.hint}</option>
                ))}
              </select>
              <p className="mt-2 text-[11px] leading-snug text-[#8c8475]" style={L.mono}>
                {revStyle
                  ? "Reimaginar: mantém sujeito, pose, orientação (frente/costas), roupas, cores e composição; troca só o meio/estilo."
                  : "Original: o prompt descreve o meio que a IA viu (desenho continua desenho, foto continua foto)."}
              </p>
            </>)}

            <label className="mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>Idioma do resultado</label>
            <div className="flex gap-1.5">
              {[["en", "Inglês"], ["pt", "Português"]].map(([v, l]) => (
                <button key={v} onClick={() => setOutLang(v)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`} style={L.mono}>{l}</button>
              ))}
            </div>

            <button onClick={reverseEngineer} disabled={loading} className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60" style={{ ...L.black, letterSpacing: "0.01em" }}>
              {loading ? (<><span className="h-2 w-2 rounded-full bg-[#1a1206]" style={{ animation: "pulseDot 1s infinite" }} />ANALISANDO...</>) : (<>🔍 EXTRAIR PROMPT</>)}
            </button>
            {error && <p className="mt-3 text-center text-sm text-[#ff8c3a]">{error}</p>}
          </div>
        )}

        {result && (
          <div ref={outRef} className="rise mt-9 rounded-2xl border border-[#2a2620] bg-[#141210] p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>
                {mode === "reverse" ? "Prompt extraído da imagem" : (primaryObj && primaryObj.video) ? (segCount > 1 ? `Anúncio · ${segCount} segmentos` : "Roteiro do anúncio") : timelapseActive ? (segCount > 1 ? `Timelapse · ${segCount} segmentos` : "Roteiro do timelapse") : sceneActive ? (segCount > 1 ? `Cena · ${segCount} segmentos` : "Cena gerada") : coloringActive ? `Livro de colorir · ${colorPages} páginas` : carouselActive ? `Carrossel · ${cardCount} cards` : storyboardActive ? `Storyboard · ${frameCount} quadros` : "Prompt gerado"}
              </span>
              <div className="flex items-center gap-2">
                {mode === "generate" && pageAssembly && (
                  <button onClick={() => setShowPage((v) => !v)} className="rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#ff9a6a] transition hover:bg-[#ff7a18]/20">{showPage ? "✕ Fechar página" : "📖 Montar página"}</button>
                )}
                <button onClick={copyResult} className="rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#ff9a6a] transition hover:bg-[#ff7a18]/20">{copied ? "✓ Copiado!" : "Copiar"}</button>
              </div>
            </div>
            <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-[#bdb3a3]" style={L.mono}>{result}</p>
          </div>
        )}

        {result && pageAssembly && showPage && mode === "generate" && (
          <div className="rise mt-6">
            <div className="mb-3 flex items-center justify-between"><span className="text-xs uppercase tracking-widest text-[#8c8475]" style={L.mono}>📖 Prancha · clique num quadro pra adicionar a imagem</span></div>
            <div className="rounded-2xl bg-[#1f1c17] p-3 sm:p-4 shadow-2xl">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {parseFrames(result).map((f, i) => (
                  <div key={i} className="overflow-hidden rounded-sm border-[3px] border-[#111] bg-white">
                    <label className="relative block cursor-pointer">
                      <div className="flex aspect-video items-center justify-center border-b-[3px] border-[#111] bg-[#d9d3c6] bg-cover bg-center" style={frameImages[i] ? { backgroundImage: `url(${frameImages[i]})` } : {}}>
                        {!frameImages[i] && (<div className="text-center"><div className="text-2xl">🖼️</div><div className="mt-1 text-[11px] font-bold text-[#8c8475]" style={L.mono}>clique pra colar a imagem</div></div>)}
                        <span className="absolute left-0 top-0 bg-[#111] px-2 py-0.5 text-xs font-black text-[#ff9a6a]" style={L.black}>{f.num}</span>
                      </div>
                      <input type="file" accept="image/*" className="hidden" onChange={(e) => handleFrameImage(i, e.target.files && e.target.files[0])} />
                    </label>
                    <div className="p-2.5">
                      {f.label && <div className="mb-1 text-[11px] font-black uppercase tracking-wide text-[#111]" style={L.black}>{f.label}</div>}
                      <p className="text-[11px] leading-snug text-[#333]" style={L.mono}>{f.prompt}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <p className="mt-2.5 text-center text-[11px] text-[#8c8475]" style={L.mono}>💡 Gere cada imagem no seu app favorito usando os prompts, depois clique nos quadros pra montar sua HQ. Use o print da tela pra salvar a prancha.</p>
          </div>
        )}

        <footer className="mt-12 text-center text-[11px] text-[#6e675b]" style={L.mono}>feito com IA · cole o resultado no seu gerador de imagens favorito</footer>
      </div>
    </div>
  );
}

// NÚCLEO: montagem sob demanda dentro da view "Forja" (React UMD global).
window.__mountForja = function () {
  var el = document.getElementById("forja-root");
  if (!el || el.__mounted) return;
  el.__mounted = true;
  ReactDOM.createRoot(el).render(React.createElement(App));
};
