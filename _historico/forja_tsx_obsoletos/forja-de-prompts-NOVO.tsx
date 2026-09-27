// @ts-nocheck
// ─────────────────────────────────────────────────────────────────────────────
// Forja de Prompts — gerador de prompts de IA (React + TypeScript) — tema claro
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
import React, { useState, useRef, useEffect } from "react";


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
  { id: "cinema", label: "Cinematográfico", tag: "🎞️", hint: "Widescreen, color grade, grão de cinema" },
  { id: "claymation", label: "Claymation", tag: "🟤", hint: "Stop-motion, textura de argila, marcas de dedo" },
  { id: "cyberpunk", label: "Cyberpunk", tag: "🌃", hint: "Neon, atmosfera futurista, reflexos, chuva" },
  { id: "darkfantasy", label: "Dark Fantasy", tag: "🐉", hint: "Fantasia sombria, épico, mórbido, vibe RPG" },
  { id: "editorial", label: "Editorial de Moda", tag: "👗", hint: "Vibe de revista, pose, styling, luz dramática" },
  { id: "funko", label: "Funko Pop", tag: "🧸", hint: "Vinil, cabeça grande, caixa, olhos pretos" },
  { id: "isometrico", label: "Isométrico", tag: "🧊", hint: "Cenário 3D em ângulo iso, diorama, ícones" },
  { id: "lineart", label: "Line Art / Tattoo", tag: "✒️", hint: "Traço limpo, minimalista, alto contraste" },
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
  timelapse: "video",
  ugc: "video",
};

const COMPAT = {
  photo:         ["photo", "theme", "design", "format"],
  "3d_real":     ["theme", "format"],
  "3d_stylized": ["theme", "format"],
  illust2d:      ["illust2d", "theme", "design", "format"],
  theme:         ["photo", "3d_real", "3d_stylized", "illust2d", "theme", "product", "design", "format"],
  product:       ["theme"],
  design:        ["theme", "illust2d", "photo"],
  format:        ["photo", "3d_real", "3d_stylized", "illust2d", "theme"],
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
  const c = (typeof window !== "undefined") ? (window as any).claude : null;
  const sample = (c && c.use) ? await c.use("sample") : null;
  if (!sample) { const e = new Error("no-sample"); e.code = "not_granted"; throw e; }
  const res = await sample(input, opts);
  const text = ((res && res.text) || "").trim();
  if (!text) { const e = new Error("empty"); e.code = "empty_completion"; throw e; }
  return text;
}

// Traduz o código de erro da capacidade em uma mensagem amigável.
function sampleErrMsg(e) {
  const c = e && e.code;
  if (c === "cancelled") return "";
  if (c === "not_granted" || c === "sampling_disabled" || c === "not_declared" || c === "capability_disabled" || c === "capability_removed")
    return "A geração por IA precisa da sua permissão. Abra o app publicado no Claude e permita o uso quando perguntado (ou recarregue a página se já recusou).";
  if (c === "rate_limited") return "Muitas gerações seguidas. Espere alguns segundos e tente de novo.";
  if (c === "images_unavailable") return "Este visualizador não consegue enviar imagens. Abra o link do app no navegador pra usar a engenharia reversa.";
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
  claymation: "CLAYMATION / STOP-MOTION look. Describe characters and objects sculpted from modeling clay or plasticine, soft matte clay texture with subtle fingerprints and tool marks, slightly imperfect handmade shapes, miniature set with practical props, soft diffuse studio lighting, shallow depth of field, and a charming tactile handcrafted feel.",
  cyberpunk: "CYBERPUNK scene. Describe neon signage, holographic reflections, wet reflective streets, volumetric haze, teal-and-magenta color contrast, futuristic wardrobe and tech, cinematic atmosphere and dramatic mood lighting.",
  darkfantasy: "DARK FANTASY art. Describe a grim, epic and atmospheric medieval-fantasy world, ornate armor and weapons, brooding monstrous or ethereal figures, gothic ruins and twisted landscapes, dramatic chiaroscuro and volumetric god rays, muted desaturated palette with deep shadows and embers, painterly concept-art rendering, and an ominous mythic mood (soulslike / grimdark RPG concept-art feel).",
  editorial: "HIGH-FASHION EDITORIAL photography. Describe a magazine-cover aesthetic, striking confident pose, designer styling and wardrobe, professional studio or location set, dramatic directional lighting and bold shadows, glossy color grading, beauty-retouch skin, and a luxurious aspirational mood worthy of Vogue-style editorial — without naming real people.",
  funko: "FUNKO POP collectible vinyl figure. Describe the signature Funko look: oversized square head, small body, large solid black dot eyes (no pupils), simplified glossy vinyl finish, minimal facial detail. Mention the figure standing, soft studio product lighting, and optionally the classic Funko window box packaging with the character art. Translate the subject's identity into iconic, simplified Funko features.",
  isometrico: "ISOMETRIC 3D render. Describe a precise isometric camera angle (no perspective convergence), tidy miniature-diorama composition, clean stylized geometry, soft ambient occlusion, a vibrant or pastel flat color palette, gentle gradients and soft shadows, and a polished design-asset look ideal for icons, app art, games or infographics.",
  lineart: "LINE ART / TATTOO design. Describe clean confident single-weight or tapered line work, minimalist high-contrast black-on-white composition, no or very limited shading, elegant negative space, smooth flowing curves, fine detail, and a crisp vector-like illustrative quality suitable for a tattoo flash or editorial linework.",
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

export default function App() {
  const [idea, setIdea] = useState("");
  const [mode, setMode] = useState("generate");
  const [revImage, setRevImage] = useState(null);
  const [revFocus, setRevFocus] = useState("faithful");
  const [brand, setBrand] = useState("");
  const [audience, setAudience] = useState("");
  const [adScript, setAdScript] = useState("");
  const [frameCount, setFrameCount] = useState(4);
  const [cardCount, setCardCount] = useState(6);
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
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const outRef = useRef(null);

  const segCount = Math.max(1, Math.ceil(tlTotal / tlClip));

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
    setError(""); setResult(""); setCopied(false); setShowPage(false); setFrameImages({}); setLoading(true);

    const chosen = STYLES.find((s) => s.id === style);
    const chosen2 = secondary ? STYLES.find((s) => s.id === secondary) : null;
    const isVideo = !!chosen.video;
    const isTimelapse = !!chosen.timelapse;
    const isMotion = isVideo || isTimelapse;
    const isStoryboard = style === "storyboard" || secondary === "storyboard";
    const isCarousel = !!chosen.carousel || (secondary && STYLES.find((s) => s.id === secondary)?.carousel);
    const lookObj = isStoryboard ? (style === "storyboard" ? chosen2 : chosen) : null;
    const carLook = isCarousel ? (chosen.carousel ? chosen2 : chosen) : null;
    const nSeg = Math.max(1, Math.ceil(tlTotal / tlClip));

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
- End the prompt with technical tags on a new line, including: --ar ${aspect} plus 3-6 fitting quality/style keywords for the chosen style.
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
      : `OUTPUT REQUIREMENTS (UGC video ad, SPLIT INTO ${nSeg} SEGMENTS for AI video tools that only make ${tlClip}s clips like Sora, Veo, Runway, Kling):
- ${langLine}
- The full ad lasts ~${tlTotal}s and is divided into ${nSeg} segments of ~${tlClip}s each, generated separately and stitched together in an editor afterward.
- Return ONLY the structured output below. No extra commentary.

First, one shared block so every segment stays consistent:

BASE (comum a todos os segmentos):
- CRIADOR(A): describe the fictional creator once — look, age range, wardrobe, vibe — so they stay IDENTICAL in every segment (this is critical for the clips to feel like one video).
- PRODUTO/REFERÊNCIA: instruct the tool to use the user's ATTACHED REFERENCE IMAGE as the exact product, keeping its shape, color, logo and label consistent across every segment; never redesign it.
- FORMATO: vertical ${aspect}, authentic phone-shot UGC look, handheld, natural lighting.
- ARCO GERAL: one sentence describing the ad's arc across all segments — hook → problem/desire → product solving it with demo → CTA.

Then produce EXACTLY ${nSeg} segments. Format each one EXACTLY like this, on its own lines:

SEGMENTO 1 de ${nSeg}  ·  (~${tlClip}s)
🎬 CLIPE: a self-contained ~${tlClip}s UGC prompt ready to paste — restate the creator + product briefly so it works alone, then the visual (setting, framing, how the product is held/used, lighting) for THIS segment.
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

    const carouselReqs = `OUTPUT REQUIREMENTS (INSTAGRAM CAROUSEL of ${cardCount} cards):
- ${langLine}
- Return ONLY the carousel below. No preamble or commentary.
- GOAL: ${carouselGoal === "sell" ? "storytelling that sells a product/offer — build desire and lead to a purchase/action." : "educational value — teach something useful and highly saveable (tips, steps, mistakes, how-to)."}
- Produce EXACTLY ${cardCount} cards. Format each EXACTLY like this:

CARD 1 — [role, e.g. "Gancho" / "Hook"]
🖼️ VISUAL: [ready-to-paste image prompt for this card's background — subject, composition, style, colors, mood, leaving space for the text overlay. 35–60 words${carLook ? `, in the ${carLook.label} visual style` : ""}.]
✍️ TEXTO: [the exact on-card copy — a bold short headline plus optional 1–2 supporting lines. Punchy, phone-readable.]

(repeat up to CARD ${cardCount})

- ARC: Card 1 is a scroll-stopping HOOK. Middle cards deliver the story/value. The LAST card is a clear CTA.
- Keep a CONSISTENT visual identity across all cards.
- After the cards add: LEGENDA: [a ready-to-post caption with a hook first line, the core message, light relevant hashtags, and a call to action.]
- If a Marca/Produto or Público-alvo is provided, tailor copy and offer to them.
- If a real person is implied, use a generic fictional persona — never name real public figures.`;

    const storyboardReqs = `OUTPUT REQUIREMENTS (STORYBOARD — a sequence of ${frameCount} frames):
- ${langLine}
- Return ONLY the storyboard below. No preamble or commentary.
- Produce EXACTLY ${frameCount} frames. Format each EXACTLY like this:

QUADRO 1 — [short shot label, e.g. "Plano geral / estabelecimento"]
[A rich, self-contained image prompt for this frame — subject, appearance, wardrobe, action/expression, environment, camera framing and angle, lighting, color palette, mood, and the visual/rendering style. Ready to paste. 45–80 words.]
--ar ${aspect}

(repeat up to QUADRO ${frameCount})

- CONTINUITY IS CRITICAL: the same character(s) keep identical appearance and wardrobe across every frame; consistent setting, lighting and art style. Restate the key identity details in each frame's prompt so each stands alone.
- Vary the cinematography across frames for good storytelling rhythm.
- Each frame's prompt must be concrete and visual${lookObj ? `, in the ${lookObj.label} style` : ""}.
- If a real person is implied, render a generic fictional likeness — never name real public figures.`;

    let styleBlock;
    if (isCarousel) {
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

    const job = isCarousel ? `a production-ready INSTAGRAM CAROUSEL of ${cardCount} cards`
      : isStoryboard ? `a production-ready STORYBOARD of ${frameCount} sequential image prompts`
      : isVideo ? (nSeg <= 1 ? "ONE production-ready video ad prompt" : `a production-ready UGC video ad SPLIT INTO ${nSeg} stitchable segments`)
      : isTimelapse ? (nSeg <= 1 ? "ONE production-ready accelerated timelapse video prompt" : `a production-ready accelerated timelapse SPLIT INTO ${nSeg} stitchable segments`)
      : "ONE extremely detailed, vivid, production-ready image prompt";

    const reqs = isCarousel ? carouselReqs : isStoryboard ? storyboardReqs : isVideo ? videoReqs : isTimelapse ? timelapseReqs : imageReqs;

    const system = `You are an elite prompt engineer for AI ${isMotion ? "video" : "image"} generators${isCarousel ? " and a social-media copywriter" : ""}.\nYour job: turn a short user idea into ${job}.\n\n${langDirective}\n\n${styleBlock}\n\n${reqs}\n\n${langDirective}`;

    const extras = [];
    if (brand.trim()) extras.push(`Marca/Produto: "${brand.trim()}"`);
    if (audience.trim()) extras.push(`Público-alvo: "${audience.trim()}"`);
    if (isVideo && adScript.trim()) extras.push(`Mensagem/roteiro que o usuário QUER no anúncio (use como base obrigatória, adaptando o tom para UGC): "${adScript.trim()}"`);
    const userMsg = `Ideia do usuário: "${idea.trim()}"${extras.length ? "\n" + extras.join("\n") : ""}`;
    const input = `${system}\n\n=== PEDIDO DO USUÁRIO ===\n${userMsg}`;

    try {
      const text = await askClaude(input, {
        cache: false,
        modelTier: "default",
        onText: ({ text }) => setResult(text),
      });
      setResult(text);
    } catch (e) {
      setResult("");
      setError(sampleErrMsg(e));
    } finally {
      setLoading(false);
    }
  }

  function handleRevImage(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setRevImage({ file: file, preview: e.target.result });
      setError("");
    };
    reader.readAsDataURL(file);
  }

  async function reverseEngineer() {
    if (!revImage) { setError("Envie uma imagem primeiro 🖼️"); return; }
    setError(""); setResult(""); setCopied(false); setShowPage(false); setFrameImages({}); setLoading(true);

    const langLine = outLang === "en" ? "Write the entire output in ENGLISH (best for AI generators)." : "Escreva toda a saída em PORTUGUÊS do Brasil.";
    const focusLine = revFocus === "faithful"
      ? "GOAL: reverse-engineer a prompt that would RECREATE this exact image as faithfully as possible."
      : "GOAL: extract mainly the STYLE, technique, lighting and mood of this image so the user can apply that look to a DIFFERENT subject.";

    const system = `You are an expert reverse-prompt engineer for AI image generators. Analyze the given image deeply and produce a prompt that could reproduce its look.\n\n${focusLine}\n\n${langLine}\n\nReturn your answer in EXACTLY this structure:\n\nPROMPT:\n[One cohesive, comma-separated prompt block ready to paste — 80–150 words, covering subject, style/medium, composition, lighting, color, mood and technical cues. End with fitting tags on a new line.]\n\nANÁLISE:\n• Estilo/Meio: [...]\n• Cenário/Local: [...]\n• Composição/Enquadramento: [...]\n• Personagens/Sujeito: [describe people GENERICALLY, never identify real individuals]\n• Iluminação: [...]\n• Cores/Paleta: [...]\n• Clima/Atmosfera: [...]\n• Técnica/Render: [...]\n\nRULES:\n- ${langLine}\n- Keep the labels PROMPT: and ANÁLISE: exactly.\n- NEVER name or guess the identity of any real person.\n- Be concrete; infer plausible technical details from visual evidence.`;

    const input = `${system}\n\nAnalise a imagem anexada seguindo exatamente a estrutura e as regras acima.`;

    try {
      const text = await askClaude(input, {
        images: revImage.file,
        cache: false,
        modelTier: "default",
        onText: ({ text }) => setResult(text),
      });
      setResult(text);
    } catch (e) {
      setResult("");
      setError(sampleErrMsg(e));
    } finally {
      setLoading(false);
    }
  }

  function parseFrames(text) {
    if (!text) return [];
    const parts = text.split(/(?=QUADRO\s*\d+)/i).filter((p) => p.trim());
    return parts.map((block, i) => {
      const lines = block.trim().split("\n");
      const header = (lines[0] || "").trim() || `QUADRO ${i + 1}`;
      const body = lines.slice(1).join("\n").trim();
      const m = header.match(/QUADRO\s*(\d+)\s*[—\-–:]*\s*(.*)/i);
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

  const L = { mono: { fontFamily: "'DM Mono', monospace" }, black: { fontFamily: "'Archivo Black', sans-serif" }, sans: { fontFamily: "'DM Sans', sans-serif" } };

  return (
    <div className="min-h-screen w-full text-[#26201b]" style={{ background: "#faf8f5", ...L.sans }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap');
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
          <p className="mt-3 max-w-lg text-sm text-[#5f5849] sm:text-base">
            Digite uma ideia simples, escolha o estilo (ou misture dois!) e receba um prompt cinematográfico, detalhado e pronto pra colar.
          </p>
        </header>

        <div className="mb-6 grid grid-cols-2 gap-2 rounded-2xl border border-[#e4ded4] bg-[#f6f3ee] p-1.5">
          {[["generate", "⚒ Gerar", "ideia → prompt"], ["reverse", "🔍 Engenharia reversa", "imagem → prompt"]].map(([v, label, sub]) => (
            <button key={v} onClick={() => { setMode(v); setResult(""); setError(""); }}
              className={`rounded-xl px-3 py-2.5 text-center transition ${mode === v ? "bg-[#ff7a18] text-[#1a1206]" : "text-[#6b6456] hover:text-[#26201b]"}`}>
              <div className="text-sm font-bold" style={L.black}>{label}</div>
              <div className={`text-[10px] ${mode === v ? "text-[#1a1206]/70" : "text-[#9a9184]"}`} style={L.mono}>{sub}</div>
            </button>
          ))}
        </div>

        {mode === "generate" && (<>
          <label className="mb-2 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Sua ideia</label>
          <textarea value={idea} onChange={(e) => setIdea(e.target.value)}
            placeholder={primaryObj && primaryObj.video ? "ex: anúncio de um sérum facial; criadora mostrando o resultado na pele..." : timelapseActive ? "ex: construção de uma casa do zero num terreno vazio... / maquiagem completa do rosto limpo até o look final... / montagem de um PC gamer na bancada..." : carouselActive ? "ex: 5 erros que estão matando suas vendas no Instagram... / como meu produto transformou a rotina de skincare da cliente..." : "ex: uma guerreira ruiva sob a chuva numa cidade antiga..."}
            rows={3} className="w-full resize-none rounded-2xl border border-[#e4ded4] bg-[#ffffff] p-4 text-[#26201b] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#94897a]" />

          {primaryObj && primaryObj.video && (
            <p className="mt-2 rounded-xl border border-[#ff7a18]/25 bg-[#ff7a18]/5 px-3 py-2 text-[12px] leading-snug text-[#6a5f3f]">
              💡 O roteiro já inclui a instrução de <b>usar a foto do produto como referência</b>. Anexe a imagem do produto na ferramenta de vídeo usando o recurso de <i>imagem de referência / image-to-video</i>.
            </p>
          )}
          {timelapseActive && (
            <p className="mt-2 rounded-xl border border-[#ff7a18]/25 bg-[#ff7a18]/5 px-3 py-2 text-[12px] leading-snug text-[#6a5f3f]">
              ⏱️ Detecta o <b>tipo de projeto</b> e monta as etapas certas, com <b>câmera travada</b>. Timelapses longos são <b>fatiados em segmentos</b> que emendam, respeitando o limite de clipe das IAs.
            </p>
          )}

          {(( primaryObj && primaryObj.video) || carouselActive) && (
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Marca / Produto <span className="text-[#9a9184] normal-case">(opcional)</span></label>
                <input value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="ex: Loja Aurora — jaqueta corta-vento" className="w-full rounded-xl border border-[#e4ded4] bg-[#ffffff] px-3 py-2.5 text-sm text-[#26201b] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#94897a]" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Público-alvo <span className="text-[#9a9184] normal-case">(opcional)</span></label>
                <input value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="ex: mulheres 25-40 que treinam ao ar livre" className="w-full rounded-xl border border-[#e4ded4] bg-[#ffffff] px-3 py-2.5 text-sm text-[#26201b] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#94897a]" />
              </div>
            </div>
          )}

          {primaryObj && primaryObj.video && (
            <div className="mt-3">
              <label className="mb-1.5 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Texto / Mensagem do anúncio <span className="text-[#9a9184] normal-case">(opcional)</span></label>
              <textarea value={adScript} onChange={(e) => setAdScript(e.target.value)} placeholder="ex: Fale sobre o desconto de 30% só essa semana; mencione que tem frete grátis; termine com 'corre que acaba rápido!'" rows={3} className="w-full resize-none rounded-xl border border-[#e4ded4] bg-[#ffffff] p-3 text-sm text-[#26201b] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#94897a]" />
              <p className="mt-1.5 text-[11px] leading-snug text-[#94897a]" style={L.mono}>Deixe vazio pra IA criar o roteiro do zero, ou escreva as falas/pontos que devem aparecer.</p>
            </div>
          )}

          <label className="mb-2 mt-7 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Estilo principal</label>
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
            {STYLES.map((s) => {
              const active = s.id === style;
              return (
                <button key={s.id} onClick={() => { setStyle(s.id); if (s.video) setAspect("9:16"); if (s.timelapse) setAspect("16:9"); if (s.carousel) setAspect("4:5"); }}
                  className={`group relative rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 shadow-[0_0_20px_rgba(255,122,24,0.25)] -translate-y-0.5" : "border-[#e4ded4] bg-[#f6f3ee] hover:border-[#c9c1b4]"}`}>
                  {active && <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ff7a18] text-[11px] font-black text-[#1a1206]">✓</span>}
                  <div className="flex items-center gap-2"><span className="text-lg">{s.tag}</span><span className={`text-sm font-bold ${active ? "text-[#c2410c]" : ""}`}>{s.label}</span></div>
                  <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#6a5f3f]" : "text-[#6b6456]"}`}>{s.hint}</p>
                </button>
              );
            })}
          </div>

          {allowCombine && (
            <div className="mt-5">
              <button onClick={() => { if (combineOpen) { setCombineOpen(false); setSecondary(null); } else setCombineOpen(true); }}
                className={`flex w-full items-center justify-center gap-2 rounded-2xl border-2 px-4 py-3 text-sm font-bold transition ${combineOpen || secondary ? "border-[#ff7a18] bg-[#ff7a18]/10 text-[#c2410c]" : "border-dashed border-[#c9c1b4] bg-transparent text-[#5f5849] hover:border-[#ff7a18]/60 hover:text-[#c2410c]"}`} style={L.mono}>
                {combineOpen || secondary ? "✕ Remover combinação" : "+ Combinar com outro estilo"}
              </button>
              {combineOpen && (
                <div className="rise mt-4">
                  <label className="mb-2 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Segundo estilo (mistura)</label>
                  <p className="mb-3 text-[11px] text-[#94897a]" style={L.mono}>Opções esmaecidas são incompatíveis com <span className="text-[#c2410c]">{primaryObj && primaryObj.label}</span>.</p>
                  <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                    {STYLES.map((s) => {
                      if (s.id === style) return null;
                      const compatible = canCombine(style, s.id);
                      const active = s.id === secondary;
                      return (
                        <button key={s.id} disabled={!compatible} onClick={() => setSecondary(s.id)} title={compatible ? "" : `Incompatível com ${primaryObj && primaryObj.label}`}
                          className={`group relative rounded-2xl border-2 p-3 text-left transition ${!compatible ? "cursor-not-allowed border-[#eee9e1] bg-[#faf8f5] opacity-30" : active ? "border-[#ff7a18] bg-[#ff7a18]/15 ring-2 ring-[#ff7a18]/40 shadow-[0_0_20px_rgba(255,209,102,0.2)] -translate-y-0.5" : "border-[#e4ded4] bg-[#f6f3ee] hover:border-[#c9c1b4]"}`}>
                          {active && <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ff7a18] text-[11px] font-black text-[#1a1206]">✓</span>}
                          <div className="flex items-center gap-2"><span className="text-lg">{s.tag}</span><span className={`text-sm font-bold ${active ? "text-[#c2410c]" : ""}`}>{s.label}</span></div>
                          <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#6a5f3f]" : "text-[#6b6456]"}`}>{s.hint}</p>
                        </button>
                      );
                    })}
                  </div>
                  {secondaryObj && (
                    <div className="rise mt-4 rounded-xl border border-[#ff7a18]/30 bg-gradient-to-r from-[#ff7a18]/10 to-[#ff7a18]/10 px-4 py-3 text-sm">
                      <span className="text-[#6b6456]">Misturando:</span> <span className="font-bold text-[#ff7a18]">{primaryObj.tag} {primaryObj.label}</span><span className="mx-2 text-[#c2410c]">+</span><span className="font-bold text-[#c2410c]">{secondaryObj.tag} {secondaryObj.label}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {(timelapseActive || (primaryObj && primaryObj.video)) && (
            <div className="rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#c2410c]" style={L.mono}>⏱️ Duração total do vídeo</label>
              <div className="flex flex-wrap gap-1.5">
                {TL_TOTALS.map(([v, l]) => (
                  <button key={v} onClick={() => setTlTotal(v)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === tlTotal ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#c2410c] ring-2 ring-[#ff7a18]/30" : "border-[#e4ded4] text-[#6b6456] hover:border-[#c9c1b4]"}`} style={L.mono}>{l}</button>
                ))}
              </div>
              <label className="mb-2 mt-5 block text-xs uppercase tracking-widest text-[#c2410c]" style={L.mono}>Duração de cada clipe da IA</label>
              <div className="flex flex-wrap gap-1.5">
                {TL_CLIPS.map((n) => (
                  <button key={n} onClick={() => setTlClip(n)} className={`rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === tlClip ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#c2410c] ring-2 ring-[#ff7a18]/30" : "border-[#e4ded4] text-[#6b6456] hover:border-[#c9c1b4]"}`} style={L.mono}>{n}s</button>
                ))}
              </div>
              <p className="mt-3 text-[11px] leading-snug text-[#5f5849]">
                {segCount <= 1 ? (<>Cabe em <b className="text-[#c2410c]">1 clipe</b> só — roteiro único.</>) : timelapseActive ? (<>Vai gerar <b className="text-[#c2410c]">{segCount} segmentos</b> de ~{tlClip}s que emendam, cada um com frame inicial/final pra continuidade perfeita. Você gera clipe por clipe e junta no editor.</>) : (<>Vai gerar <b className="text-[#c2410c]">{segCount} segmentos</b> de ~{tlClip}s que emendam, com a mesma criadora e produto em todos. Você gera clipe por clipe e junta no editor.</>)}
              </p>
            </div>
          )}

          {storyboardActive && (
            <div className="rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#c2410c]" style={L.mono}>🎬 Quantos quadros?</label>
              <div className="flex flex-wrap gap-1.5">
                {[3, 4, 5, 6, 7, 8].map((n) => (
                  <button key={n} onClick={() => setFrameCount(n)} className={`rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === frameCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#c2410c] ring-2 ring-[#ff7a18]/30" : "border-[#e4ded4] text-[#6b6456] hover:border-[#c9c1b4]"}`} style={L.mono}>{n}</button>
                ))}
              </div>
              <p className="mt-2.5 text-[11px] leading-snug text-[#5f5849]">O storyboard gera <b className="text-[#c2410c]">{frameCount} prompts</b> em sequência, com continuidade. {secondaryObj ? "" : "💡 Combine com um estilo visual pra definir o look dos quadros."}</p>
            </div>
          )}

          {carouselActive && (
            <div className="rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4">
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#c2410c]" style={L.mono}>🎠 Objetivo do carrossel</label>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {[["sell", "🛍️ Storytelling / Venda", "Cria desejo e leva à ação"], ["educate", "💡 Educativo / Dicas", "Ensina algo salvável"]].map(([v, label, sub]) => {
                  const active = carouselGoal === v;
                  return (
                    <button key={v} onClick={() => setCarouselGoal(v)} className={`rounded-xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40" : "border-[#e4ded4] bg-[#f6f3ee] hover:border-[#c9c1b4]"}`}>
                      <div className={`text-sm font-bold ${active ? "text-[#c2410c]" : ""}`}>{label}</div>
                      <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#6a5f3f]" : "text-[#6b6456]"}`}>{sub}</p>
                    </button>
                  );
                })}
              </div>
              <label className="mb-2 mt-5 block text-xs uppercase tracking-widest text-[#c2410c]" style={L.mono}>Quantos cards?</label>
              <div className="flex flex-wrap gap-1.5">
                {[3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <button key={n} onClick={() => setCardCount(n)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${n === cardCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#c2410c] ring-2 ring-[#ff7a18]/30" : "border-[#e4ded4] text-[#6b6456] hover:border-[#c9c1b4]"}`} style={L.mono}>{n}</button>
                ))}
              </div>
              <p className="mt-2.5 text-[11px] leading-snug text-[#5f5849]">Gera <b className="text-[#c2410c]">{cardCount} cards</b> (visual + copy) do gancho ao CTA, mais uma legenda pronta pra postar. {secondaryObj ? "" : "💡 Combine com um estilo visual pra definir o look dos cards."}</p>
            </div>
          )}

          <div className="mt-7 flex flex-wrap items-end gap-6">
            <div>
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Proporção</label>
              <div className="flex flex-wrap gap-1.5">
                {ASPECTS.map((a) => (
                  <button key={a} onClick={() => setAspect(a)} className={`rounded-lg border-2 px-2.5 py-1.5 text-xs font-bold transition ${a === aspect ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#c2410c] ring-2 ring-[#ff7a18]/30" : "border-[#e4ded4] text-[#6b6456] hover:border-[#c9c1b4]"}`} style={L.mono}>{a}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="mb-2 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Idioma do prompt</label>
              <div className="flex gap-1.5">
                {[["en", "Inglês"], ["pt", "Português"]].map(([v, l]) => (
                  <button key={v} onClick={() => setOutLang(v)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#c2410c] ring-2 ring-[#ff7a18]/30" : "border-[#e4ded4] text-[#6b6456] hover:border-[#c9c1b4]"}`} style={L.mono}>{l}</button>
                ))}
              </div>
            </div>
          </div>

          <button onClick={generate} disabled={loading} className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60" style={{ ...L.black, letterSpacing: "0.01em" }}>
            {loading ? (<><span className="h-2 w-2 rounded-full bg-[#1a1206]" style={{ animation: "pulseDot 1s infinite" }} />FORJANDO...</>) : (<>⚒ GERAR PROMPT</>)}
          </button>
          {error && <p className="mt-3 text-center text-sm text-[#d1490b]">{error}</p>}
        </>)}

        {mode === "reverse" && (
          <div>
            <label className="mb-2 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Imagem de referência</label>
            <label className="relative block cursor-pointer">
              <div className="flex min-h-[180px] items-center justify-center rounded-2xl border-2 border-dashed border-[#c9c1b4] bg-[#f6f3ee] bg-contain bg-center bg-no-repeat p-4 transition hover:border-[#ff7a18]/60" style={revImage ? { backgroundImage: `url(${revImage.preview})`, minHeight: "280px" } : {}}>
                {!revImage && (<div className="text-center"><div className="text-4xl">🖼️</div><div className="mt-2 text-sm font-bold text-[#5f5849]">Clique pra enviar uma imagem</div><div className="mt-1 text-[11px] text-[#94897a]" style={L.mono}>PNG, JPG ou WEBP</div></div>)}
              </div>
              <input type="file" accept="image/*" className="hidden" onChange={(e) => handleRevImage(e.target.files && e.target.files[0])} />
            </label>
            {revImage && <button onClick={() => setRevImage(null)} className="mt-2 text-[11px] text-[#6b6456] underline transition hover:text-[#d1490b]" style={L.mono}>remover imagem</button>}

            <label className="mb-2 mt-6 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Foco da análise</label>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {[["faithful", "🎯 Recriar fiel", "Reproduz a imagem o mais parecido possível"], ["style", "🎨 Capturar estilo", "Extrai só o 'look' pra usar em outra ideia"]].map(([v, label, sub]) => {
                const active = revFocus === v;
                return (
                  <button key={v} onClick={() => setRevFocus(v)} className={`rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 -translate-y-0.5" : "border-[#e4ded4] bg-[#f6f3ee] hover:border-[#c9c1b4]"}`}>
                    <div className={`text-sm font-bold ${active ? "text-[#c2410c]" : ""}`}>{label}</div>
                    <p className={`mt-1 text-[11px] leading-snug ${active ? "text-[#6a5f3f]" : "text-[#6b6456]"}`}>{sub}</p>
                  </button>
                );
              })}
            </div>

            <label className="mb-2 mt-6 block text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>Idioma do resultado</label>
            <div className="flex gap-1.5">
              {[["en", "Inglês"], ["pt", "Português"]].map(([v, l]) => (
                <button key={v} onClick={() => setOutLang(v)} className={`rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#c2410c] ring-2 ring-[#ff7a18]/30" : "border-[#e4ded4] text-[#6b6456] hover:border-[#c9c1b4]"}`} style={L.mono}>{l}</button>
              ))}
            </div>

            <button onClick={reverseEngineer} disabled={loading} className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60" style={{ ...L.black, letterSpacing: "0.01em" }}>
              {loading ? (<><span className="h-2 w-2 rounded-full bg-[#1a1206]" style={{ animation: "pulseDot 1s infinite" }} />ANALISANDO...</>) : (<>🔍 EXTRAIR PROMPT</>)}
            </button>
            {error && <p className="mt-3 text-center text-sm text-[#d1490b]">{error}</p>}
          </div>
        )}

        {result && (
          <div ref={outRef} className="rise mt-9 rounded-2xl border border-[#e4ded4] bg-[#ffffff] p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>
                {mode === "reverse" ? "Prompt extraído da imagem" : (primaryObj && primaryObj.video) ? (segCount > 1 ? `Anúncio · ${segCount} segmentos` : "Roteiro do anúncio") : timelapseActive ? (segCount > 1 ? `Timelapse · ${segCount} segmentos` : "Roteiro do timelapse") : carouselActive ? `Carrossel · ${cardCount} cards` : storyboardActive ? `Storyboard · ${frameCount} quadros` : "Prompt gerado"}
              </span>
              <div className="flex items-center gap-2">
                {mode === "generate" && storyboardActive && (
                  <button onClick={() => setShowPage((v) => !v)} className="rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#c2410c] transition hover:bg-[#ff7a18]/20">{showPage ? "✕ Fechar página" : "📖 Montar página"}</button>
                )}
                <button onClick={copyResult} className="rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#c2410c] transition hover:bg-[#ff7a18]/20">{copied ? "✓ Copiado!" : "Copiar"}</button>
              </div>
            </div>
            <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-[#2a241d]" style={L.mono}>{result}</p>
          </div>
        )}

        {result && storyboardActive && showPage && mode === "generate" && (
          <div className="rise mt-6">
            <div className="mb-3 flex items-center justify-between"><span className="text-xs uppercase tracking-widest text-[#6b6456]" style={L.mono}>📖 Prancha · clique num quadro pra adicionar a imagem</span></div>
            <div className="rounded-2xl bg-[#e8e2d5] p-3 sm:p-4 shadow-2xl">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {parseFrames(result).map((f, i) => (
                  <div key={i} className="overflow-hidden rounded-sm border-[3px] border-[#111] bg-white">
                    <label className="relative block cursor-pointer">
                      <div className="flex aspect-video items-center justify-center border-b-[3px] border-[#111] bg-[#d9d3c6] bg-cover bg-center" style={frameImages[i] ? { backgroundImage: `url(${frameImages[i]})` } : {}}>
                        {!frameImages[i] && (<div className="text-center"><div className="text-2xl">🖼️</div><div className="mt-1 text-[11px] font-bold text-[#6b6455]" style={L.mono}>clique pra colar a imagem</div></div>)}
                        <span className="absolute left-0 top-0 bg-[#111] px-2 py-0.5 text-xs font-black text-[#c2410c]" style={L.black}>{f.num}</span>
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
            <p className="mt-2.5 text-center text-[11px] text-[#94897a]" style={L.mono}>💡 Gere cada imagem no seu app favorito usando os prompts, depois clique nos quadros pra montar sua HQ. Use o print da tela pra salvar a prancha.</p>
          </div>
        )}

        <footer className="mt-12 text-center text-[11px] text-[#9a9184]" style={L.mono}>feito com IA · cole o resultado no seu gerador de imagens favorito</footer>
      </div>
    </div>
  );
}

