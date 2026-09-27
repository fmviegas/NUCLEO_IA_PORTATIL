const { useState, useRef, useEffect } = React;
const STYLES = [
  { id: "render3d", label: "3D / CGI", tag: "\u{1F9F1}", hint: "Render 3D realista, materiais, ilumina\xE7\xE3o global" },
  { id: "anime", label: "Anime", tag: "\u{1F338}", hint: "Estilo de est\xFAdio, cel-shading, tra\xE7o, paleta" },
  { id: "ghiblivibe", label: "Anime Aconchegante", tag: "\u{1F343}", hint: "Slice of life, fundo aquarelado, luz suave, nostalgia" },
  { id: "aquarela", label: "Aquarela", tag: "\u{1F3A8}", hint: "Manchas suaves, papel, bordas que escorrem" },
  { id: "bodyhorror", label: "Body Horror / Terror Visceral", tag: "\u{1FA78}", hint: "+18 \xB7 Atmosfera, estranhamento corporal, tens\xE3o" },
  { id: "actionfigure", label: "Boneco / Action Figure", tag: "\u{1F9B8}", hint: "Figura na embalagem blister, acess\xF3rios, escala" },
  { id: "cartoon", label: "Cartoon", tag: "\u{1F430}", hint: "Desenho 2D, tra\xE7o expressivo, cores vivas" },
  { id: "carrossel", label: "Carrossel Instagram", tag: "\u{1F3A0}", hint: "V\xE1rios cards com visual + copy, gancho ao CTA", carousel: true },
  { id: "cinema", label: "Cinematogr\xE1fico", tag: "\u{1F39E}\uFE0F", hint: "Widescreen, color grade, gr\xE3o de cinema" },
  { id: "claymation", label: "Claymation", tag: "\u{1F7E4}", hint: "Stop-motion, textura de argila, marcas de dedo" },
  { id: "cyberpunk", label: "Cyberpunk", tag: "\u{1F303}", hint: "Neon, atmosfera futurista, reflexos, chuva" },
  { id: "darkfantasy", label: "Dark Fantasy", tag: "\u{1F409}", hint: "Fantasia sombria, \xE9pico, m\xF3rbido, vibe RPG" },
  { id: "editorial", label: "Editorial de Moda", tag: "\u{1F457}", hint: "Vibe de revista, pose, styling, luz dram\xE1tica" },
  { id: "funko", label: "Funko Pop", tag: "\u{1F9F8}", hint: "Vinil, cabe\xE7a grande, caixa, olhos pretos" },
  { id: "isometrico", label: "Isom\xE9trico", tag: "\u{1F9CA}", hint: "Cen\xE1rio 3D em \xE2ngulo iso, diorama, \xEDcones" },
  { id: "lineart", label: "Line Art / Tattoo", tag: "\u2712\uFE0F", hint: "Tra\xE7o limpo, minimalista, alto contraste" },
  { id: "logo", label: "Logo / Branding", tag: "\u{1F3F7}\uFE0F", hint: "Marca minimalista, vetorial, varia\xE7\xF5es" },
  { id: "lowpoly", label: "Low Poly", tag: "\u{1F53A}", hint: "Geometria de poucos pol\xEDgonos, facetada, estilizada" },
  { id: "mockup", label: "Mockup de Produto", tag: "\u{1F4E6}", hint: "Embalagem realista, fundo de est\xFAdio, e-commerce" },
  { id: "oleo", label: "\xD3leo / Cl\xE1ssico", tag: "\u{1F5BC}\uFE0F", hint: "Pinceladas, claro-escuro, vibe renascentista" },
  { id: "pixar", label: "Pixar", tag: "\u{1F3AC}", hint: "Render animado estilizado, fofo, expressivo" },
  { id: "pixelart", label: "Pixel Art", tag: "\u{1F47E}", hint: "Retr\xF4 8/16-bit, dithering, paleta limitada" },
  { id: "poster", label: "P\xF4ster / Capa", tag: "\u{1F4F0}", hint: "Composi\xE7\xE3o de cartaz, tipografia integrada" },
  { id: "comic", label: "Quadrinhos", tag: "\u{1F4A5}", hint: "Contornos grossos, halftone, bal\xF5es, cores chapadas" },
  { id: "realismo", label: "Realismo Extremo", tag: "\u{1F4F7}", hint: "Foto hiper-realista, pele, luz, lente, gr\xE3o" },
  { id: "scifi", label: "Sci-Fi / Fic\xE7\xE3o Cient\xEDfica", tag: "\u{1F680}", hint: "Naves, planetas, tecnologia, futuro" },
  { id: "steampunk", label: "Steampunk", tag: "\u2699\uFE0F", hint: "Engrenagens, lat\xE3o, vapor, vibe vitoriana" },
  { id: "storyboard", label: "Storyboard", tag: "\u{1F3AC}", hint: "Quebra a cena em v\xE1rios quadros, com continuidade" },
  { id: "thumbnail", label: "Thumbnail YouTube", tag: "\u25B6\uFE0F", hint: "Alto contraste, express\xE3o exagerada, texto" },
  { id: "timelapse", label: "Timelapse Acelerado", tag: "\u23F1\uFE0F", hint: "Constru\xE7\xE3o, maquiagem, montagem \u2014 do zero ao pronto", timelapse: true },
  { id: "ugc", label: "UGC / An\xFAncio", tag: "\u{1F3A5}", hint: "V\xEDdeo de an\xFAncio: criador mostra/usa o produto", video: true },
  { id: "vaporwave", label: "Vaporwave / Synthwave", tag: "\u{1F334}", hint: "Neon rosa-roxo, grid 80s, p\xF4r do sol retr\xF4" },
  { id: "vintage", label: "Vintage / Anal\xF3gico", tag: "\u{1F4FC}", hint: "Polaroid, pel\xEDcula 70/90, luz vazada" }
];
const ASPECTS = ["1:1", "3:2", "2:3", "16:9", "9:16", "4:5"];
const TL_TOTALS = [[15, "15s"], [30, "30s"], [60, "1min"], [120, "2min"], [180, "3min"]];
const TL_CLIPS = [6, 8, 10];
const STYLE_CATEGORIES = {
  realismo: "photo",
  editorial: "photo",
  cinema: "photo",
  vintage: "photo",
  mockup: "photo",
  render3d: "3d_real",
  pixar: "3d_stylized",
  lowpoly: "3d_stylized",
  isometrico: "3d_stylized",
  claymation: "3d_stylized",
  anime: "illust2d",
  ghiblivibe: "illust2d",
  cartoon: "illust2d",
  aquarela: "illust2d",
  oleo: "illust2d",
  comic: "illust2d",
  lineart: "illust2d",
  pixelart: "illust2d",
  cyberpunk: "theme",
  darkfantasy: "theme",
  scifi: "theme",
  bodyhorror: "theme",
  steampunk: "theme",
  vaporwave: "theme",
  funko: "product",
  actionfigure: "product",
  logo: "design",
  poster: "design",
  thumbnail: "design",
  storyboard: "format",
  carrossel: "format",
  timelapse: "video",
  ugc: "video"
};
const COMPAT = {
  photo: ["photo", "theme", "design", "format"],
  "3d_real": ["theme", "format"],
  "3d_stylized": ["theme", "format"],
  illust2d: ["illust2d", "theme", "design", "format"],
  theme: ["photo", "3d_real", "3d_stylized", "illust2d", "theme", "product", "design", "format"],
  product: ["theme"],
  design: ["theme", "illust2d", "photo"],
  format: ["photo", "3d_real", "3d_stylized", "illust2d", "theme"],
  video: []
};
function canCombine(aId, bId) {
  if (!aId || !bId || aId === bId) return false;
  const aCat = STYLE_CATEGORIES[aId];
  const bCat = STYLE_CATEGORIES[bId];
  return !!(COMPAT[aCat] && COMPAT[aCat].includes(bCat));
}
function canCombineAny(aId) {
  const aCat = STYLE_CATEGORIES[aId];
  return (COMPAT[aCat] && COMPAT[aCat].length || 0) > 0;
}
async function askClaude(input, opts) {
  const response = await fetch("/api/forja", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ system: "", user: input, max_tokens: 1500 })
  });
  let data = null;
  try {
    data = await response.json();
  } catch (_) {
  }
  if (!data || !data.ok) {
    const e = new Error(data && data.error && data.error.message || "engine");
    e.code = "engine";
    throw e;
  }
  const text = (data.text || "").trim();
  if (!text) {
    const e = new Error("empty");
    e.code = "empty_completion";
    throw e;
  }
  return text;
}
function sampleErrMsg(e) {
  const c = e && e.code;
  if (c === "cancelled") return "";
  if (c === "not_granted" || c === "sampling_disabled" || c === "not_declared" || c === "capability_disabled" || c === "capability_removed")
    return "A gera\xE7\xE3o por IA precisa da sua permiss\xE3o. Abra o app publicado no Claude e permita o uso quando perguntado (ou recarregue a p\xE1gina se j\xE1 recusou).";
  if (c === "rate_limited") return "Muitas gera\xE7\xF5es seguidas. Espere alguns segundos e tente de novo.";
  if (c === "images_unavailable") return "Este visualizador n\xE3o consegue enviar imagens. Abra o link do app no navegador pra usar a engenharia reversa.";
  if (c === "image_rejected") return "N\xE3o consegui usar essa imagem. Tente outra (JPG, PNG ou WebP, at\xE9 20 MB).";
  if (c === "prompt_too_large") return "O pedido ficou grande demais. Reduza o texto, os quadros/cards ou os segmentos.";
  if (c === "refused") return "A IA n\xE3o conseguiu responder a esse pedido. Ajuste a ideia e tente de novo.";
  if (c === "session_expired") return "Sua sess\xE3o do Claude expirou. Entre de novo e tente outra vez.";
  return "Algo deu errado ao gerar. Tente de novo em alguns segundos.";
}
const STYLE_BRIEFS = {
  render3d: "REALISTIC 3D / CGI render. Describe physically-based materials (PBR) with accurate roughness, metalness and reflections, high-resolution textures, ray-traced global illumination and soft shadows, studio or HDRI environment lighting, precise geometry, subtle ambient occlusion, and a clean polished production-render quality (Blender/Octane/Redshift feel) \u2014 not cartoonish.",
  anime: "ANIME / MANGA illustration. Reference a fitting art direction (e.g. modern Kyoto Animation softness, Makoto Shinkai luminous skies, Studio Trigger dynamic energy, 90s retro cel) WITHOUT naming copyrighted characters. Describe line work, cel-shading or soft gradients, expressive eyes, hair rendering, color palette, background art style, and emotional tone.",
  ghiblivibe: "COZY HAND-PAINTED ANIME in a warm slice-of-life tradition (do NOT name any studio). Describe lush hand-painted watercolor-style backgrounds, soft natural lighting and golden warmth, gentle rolling landscapes, fluffy clouds and detailed nature (grass, trees, food, small everyday objects), soft rounded character design with simple expressive faces, a nostalgic peaceful wholesome mood, and a tender, comforting storybook atmosphere.",
  aquarela: "WATERCOLOR painting. Describe soft translucent washes, organic bleeding edges where pigments diffuse, visible cold-press paper texture and grain, gentle gradients, white paper showing through highlights, delicate granulation, loose expressive brush strokes, and a light airy color palette. Mention controlled wet-on-wet blooms and a hand-painted artisanal feel.",
  bodyhorror: "BODY HORROR / VISCERAL HORROR art (mature, 18+). This is the cinematic/surreal-art horror genre in the tradition of practical-effects creature films and unsettling fine-art horror. Build DREAD through atmosphere rather than shock: describe uncanny anatomical distortion, biomechanical or grotesque transformation, eerie textures (slick, fibrous, calcified), oppressive shadow and fog, sickly desaturated or bruised color palettes, decay and wrongness, claustrophobic framing, and a deeply disturbing surreal mood. Keep it artful and suggestive \u2014 favor implication, silhouette and the half-seen over explicit gratuitous gore. No real identifiable people; no minors under any circumstance.",
  actionfigure: "COLLECTIBLE ACTION FIGURE of the subject, shown as a real toy product. Describe articulated plastic figure, realistic scale (e.g. 6-inch), it sitting inside a blister/clamshell retail packaging with cardback, accessories laid out beside it, the product/brand-style logo area, plastic and paint texture, and clean product photography lighting. Make it clearly look like merchandise, not a real person.",
  cartoon: "CARTOON 2D illustration (Western animated style, distinct from anime). Describe bold clean outlines, simplified exaggerated shapes, bouncy expressive character design, flat bright saturated colors, minimal shading or simple cel shading, playful energetic poses, and a fun lighthearted TV/web-cartoon feel. Avoid naming copyrighted characters.",
  carrossel: "INSTAGRAM CAROUSEL \u2014 a swipeable sequence of square/vertical cards designed for social engagement and saves, NOT a single image or a movie scene. Each card pairs a VISUAL (image prompt) with punchy on-card COPY. The sequence follows a proven arc: a scroll-stopping HOOK card, several value/story cards that build momentum and keep people swiping, and a final CTA card. Keep a consistent visual identity across all cards (same palette, type feel, framing) so it looks like one cohesive set. Copy must be short, high-contrast and readable on a phone.",
  cinema: "CINEMATIC FILM STILL. Describe an anamorphic widescreen frame, filmic color grading (teal-orange or moody desaturated), shallow depth of field with creamy bokeh, motivated practical lighting, atmospheric haze, fine film grain, lens flares, and the composed mood of a frame pulled from a feature film.",
  claymation: "CLAYMATION / STOP-MOTION look. Describe characters and objects sculpted from modeling clay or plasticine, soft matte clay texture with subtle fingerprints and tool marks, slightly imperfect handmade shapes, miniature set with practical props, soft diffuse studio lighting, shallow depth of field, and a charming tactile handcrafted feel.",
  cyberpunk: "CYBERPUNK scene. Describe neon signage, holographic reflections, wet reflective streets, volumetric haze, teal-and-magenta color contrast, futuristic wardrobe and tech, cinematic atmosphere and dramatic mood lighting.",
  darkfantasy: "DARK FANTASY art. Describe a grim, epic and atmospheric medieval-fantasy world, ornate armor and weapons, brooding monstrous or ethereal figures, gothic ruins and twisted landscapes, dramatic chiaroscuro and volumetric god rays, muted desaturated palette with deep shadows and embers, painterly concept-art rendering, and an ominous mythic mood (soulslike / grimdark RPG concept-art feel).",
  editorial: "HIGH-FASHION EDITORIAL photography. Describe a magazine-cover aesthetic, striking confident pose, designer styling and wardrobe, professional studio or location set, dramatic directional lighting and bold shadows, glossy color grading, beauty-retouch skin, and a luxurious aspirational mood worthy of Vogue-style editorial \u2014 without naming real people.",
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
  comic: "COMIC BOOK / GRAPHIC NOVEL illustration. Describe bold confident ink outlines, dynamic action posing, halftone Ben-Day dots and cross-hatching for shading, flat saturated color fills, dramatic perspective and foreshortening, expressive linework, panel-art energy, and optional speech bubbles or onomatopoeia. Reference a fitting era (golden-age, modern American, European bande dessin\xE9e) WITHOUT naming copyrighted characters.",
  realismo: "EXTREME PHOTOREALISM. Specify a real camera body and lens (e.g. Sony A7 IV, 85mm f/1.4), aperture and depth of field, shutter/ISO when relevant, type and direction of lighting (golden hour, softbox, rim light), realistic skin texture with pores and subtle imperfections, fabric and material detail, color grading, film grain, and photographic mood. Avoid any cartoon or illustrated language.",
  scifi: "SCIENCE FICTION concept art. Describe advanced futuristic technology, spacecraft or starships, alien worlds and skylines, sleek hard-surface machinery and hardware, holographic interfaces, vast scale and dramatic perspective, cinematic lighting with cool metallic tones and glowing accents, atmospheric depth, and a polished blockbuster-sci-fi concept-art finish.",
  steampunk: "STEAMPUNK aesthetic. Describe Victorian-era retro-futurism powered by steam and clockwork: polished brass and copper, intricate exposed gears and cogs, riveted iron, pressure gauges, pipes and valves, leather and mahogany, goggles and ornate mechanical contraptions, warm sepia and bronze tones, gaslight glow, billowing steam and a richly detailed industrial-fantasy mood.",
  storyboard: "STORYBOARD MODE. This is a sequential shot-by-shot breakdown of a scene, NOT a single image. Break the user's idea into a clear narrative sequence of distinct frames/shots. Keep strong CONTINUITY across all frames: the same character(s) with consistent appearance and wardrobe, consistent setting, lighting and visual style throughout, so the frames read as one coherent scene. Vary the cinematography frame to frame (establishing wide, medium, close-up, over-the-shoulder, low/high angle, reaction shot) to tell the story with good visual rhythm.",
  thumbnail: "YOUTUBE THUMBNAIL design. Describe a high-impact attention-grabbing composition, an exaggerated expressive face or hero subject, punchy saturated colors and strong contrast, a bold separating outline around the subject, space reserved for big readable headline text, dramatic lighting, and a click-worthy scroll-stopping energy.",
  timelapse: "ACCELERATED TIMELAPSE video. A fixed, locked-off camera compresses hours or days into seconds, showing a subject being built, made, applied or transformed from start to finish. Describe smooth flicker-free time compression, hands and people reduced to blurred streaks, the sun arcing overhead with shadows sweeping across the scene, clouds streaking past, light shifting through the day, and IDENTICAL framing held from the first frame to the last so the transformation reads clearly. The payoff is the finished result revealed and held steady at the end.",
  ugc: "AUTHENTIC UGC (user-generated content) ADVERTISING VIDEO \u2014 looks like a real everyday creator filming on their phone, NOT a polished studio commercial. The talent is relatable and natural, talking directly to camera while holding, wearing, using, or showing off the product. Setting is casual and real (bedroom, kitchen, bathroom mirror, car, store aisle, street). Handheld slightly shaky framing, vertical phone footage, natural/window lighting, candid energy, genuine reactions. Build it as a short ad with a clear arc: a scroll-stopping HOOK in the first 2 seconds, a quick PROBLEM or desire, the PRODUCT shown solving it with real close-ups/demonstration, and a punchy CALL-TO-ACTION at the end.",
  vaporwave: "VAPORWAVE / SYNTHWAVE aesthetic. Describe a retro-futuristic 80s/90s digital dreamscape: glowing pink-and-purple neon, magenta-cyan gradients, a luminous laser grid floor receding to the horizon, a giant retro sun with horizontal stripes, chrome and glassy reflective surfaces, palm trees and geometric shapes, VHS scanlines and glitch artifacts, and a nostalgic dreamy synthwave mood.",
  vintage: "VINTAGE / ANALOG photography. Describe an aged film look \u2014 Polaroid or 35mm 70s/90s aesthetic, faded warm or slightly off colors, light leaks, soft focus and vignetting, visible film grain and dust, slightly washed contrast, and a nostalgic retro snapshot mood."
};
function App() {
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
    if (!idea.trim()) {
      setError("Escreva uma ideia primeiro \u270D\uFE0F");
      return;
    }
    setError("");
    setResult("");
    setCopied(false);
    setShowPage(false);
    setFrameImages({});
    setLoading(true);
    const chosen = STYLES.find((s) => s.id === style);
    const chosen2 = secondary ? STYLES.find((s) => s.id === secondary) : null;
    const isVideo = !!chosen.video;
    const isTimelapse = !!chosen.timelapse;
    const isMotion = isVideo || isTimelapse;
    const isStoryboard = style === "storyboard" || secondary === "storyboard";
    const isCarousel = !!chosen.carousel || secondary && STYLES.find((s) => s.id === secondary)?.carousel;
    const lookObj = isStoryboard ? style === "storyboard" ? chosen2 : chosen : null;
    const carLook = isCarousel ? chosen.carousel ? chosen2 : chosen : null;
    const nSeg = Math.max(1, Math.ceil(tlTotal / tlClip));
    const langLine = outLang === "en" ? "Write the entire final prompt in ENGLISH (best for AI generators)." : "Escreva o prompt final inteiro em PORTUGU\xCAS do Brasil.";
    const langDirective = outLang === "en" ? "CRITICAL OUTPUT LANGUAGE: Write the ENTIRE output in ENGLISH ONLY \u2014 every word, including all section labels, spoken lines and captions. This is mandatory even though the user's idea is written in Portuguese. Do NOT output any Portuguese." : "IDIOMA DE SA\xCDDA OBRIGAT\xD3RIO: Escreva TODA a resposta em PORTUGU\xCAS do Brasil \u2014 cada palavra, incluindo r\xF3tulos de se\xE7\xE3o, falas e legendas.";
    const imageReqs = `OUTPUT REQUIREMENTS:
- ${langLine}
- Return ONLY the final prompt text. No explanations, no preamble, no headings, no markdown, no quotes.
- Make it richly detailed: subject, appearance, wardrobe, pose/expression, environment, composition/framing, lighting, color palette, mood, texture/material detail, and rendering/technical specs appropriate to the style.
- Be concrete and visual. Prefer specific nouns and adjectives over vague ones.
- Keep it as a flowing, comma-and-clause description (one cohesive block), 90\u2013160 words.
- End the prompt with technical tags on a new line, including: --ar ${aspect} plus 3-6 fitting quality/style keywords for the chosen style.
- If the subject implies a real, identifiable person, render them as a generic/fictional likeness \u2014 never name real public figures.`;
    const ugcCatBlock = `RESULT / DEMONSTRATION SHOTS (very important): infer the product CATEGORY from the idea and brand, and ALWAYS include the close-up shots that actually SELL that category \u2014 showing the product in use and its visible RESULT, not just the package. Apply the matching ones:
- Makeup / cosmetics \u2192 macro close-ups of application on skin, lips with light catching the shine, eyes, plus a clear BEFORE-and-AFTER of the treated area.
- Skincare \u2192 extreme close-up of skin texture before, the product's spread on skin, and an after glow/hydration result.
- Perfume \u2192 close-up of the bottle, the spray gesture and mist, wrist/neck application.
- Hair \u2192 close-up of hair texture, the application, and the after shine/volume/movement.
- Food / drink \u2192 appetizing macro, steam/pour/texture, and a real bite or sip with genuine reaction.
- Apparel \u2192 close-up of fabric texture and stitching, the fit/drape on the body, and movement.
- Tech \u2192 close-up of the screen/buttons/key feature actually working, hands interacting.
- Cleaning / home \u2192 before-and-after of the surface, the product visibly working.
If the category is unclear, default to: product close-up + the product clearly in use + the visible benefit it delivers.`;
    const videoReqs = nSeg <= 1 ? `OUTPUT REQUIREMENTS (this is a VIDEO ad prompt for tools like Sora, Veo, Runway, Kling):
- ${langLine}
- Return ONLY the structured prompt below. No extra commentary before or after.
- Structure it EXACTLY with these labeled sections, each on its own lines:

CONCEITO: one sentence describing the overall ad and the creator/talent (relatable, fictional, never a named real person).
REFER\xCANCIA: an explicit instruction telling the video tool to use the user's ATTACHED REFERENCE IMAGE as the exact product \u2014 keep its real shape, color, logo, label, and proportions consistent across every shot; do not redesign or invent a different product.
FORMATO: vertical ${aspect}, total duration ~${tlTotal}s, authentic phone-shot UGC look.
CENAS: a numbered shot list (4\u20136 shots). For EACH shot give: the visual (setting, framing, camera move, how the product is held/worn/used, lighting) AND the spoken line the creator says, written naturally and casually. Include at least one slow, stable CLOSE-UP of the product on a clean/uncluttered background.

${ugcCatBlock}
TEXTO NA TELA: 2\u20134 short on-screen captions/overlays (hook + key benefit + CTA).
\xC1UDIO: voiceover tone, ambient sound, and a music vibe suggestion.
CTA: the final spoken + on-screen call to action.

- Keep the energy authentic and conversational, not corporate.
- If a real, identifiable person is implied, use a generic fictional creator \u2014 never name real public figures.` : `OUTPUT REQUIREMENTS (UGC video ad, SPLIT INTO ${nSeg} SEGMENTS for AI video tools that only make ${tlClip}s clips like Sora, Veo, Runway, Kling):
- ${langLine}
- The full ad lasts ~${tlTotal}s and is divided into ${nSeg} segments of ~${tlClip}s each, generated separately and stitched together in an editor afterward.
- Return ONLY the structured output below. No extra commentary.

First, one shared block so every segment stays consistent:

BASE (comum a todos os segmentos):
- CRIADOR(A): describe the fictional creator once \u2014 look, age range, wardrobe, vibe \u2014 so they stay IDENTICAL in every segment (this is critical for the clips to feel like one video).
- PRODUTO/REFER\xCANCIA: instruct the tool to use the user's ATTACHED REFERENCE IMAGE as the exact product, keeping its shape, color, logo and label consistent across every segment; never redesign it.
- FORMATO: vertical ${aspect}, authentic phone-shot UGC look, handheld, natural lighting.
- ARCO GERAL: one sentence describing the ad's arc across all segments \u2014 hook \u2192 problem/desire \u2192 product solving it with demo \u2192 CTA.

Then produce EXACTLY ${nSeg} segments. Format each one EXACTLY like this, on its own lines:

SEGMENTO 1 de ${nSeg}  \xB7  (~${tlClip}s)
\u{1F3AC} CLIPE: a self-contained ~${tlClip}s UGC prompt ready to paste \u2014 restate the creator + product briefly so it works alone, then the visual (setting, framing, how the product is held/used, lighting) for THIS segment.
\u{1F5E3}\uFE0F FALA: the exact spoken line(s) the creator says in this segment, natural and casual.
\u{1F4DD} TEXTO NA TELA: the on-screen caption for this segment (if any).
\u{1F517} CONTINUIDADE: one line on what carries over (same outfit, same room, same product state) so the next clip matches seamlessly.

(repeat for SEGMENTO 2 de ${nSeg}, \u2026 up to SEGMENTO ${nSeg} de ${nSeg}. Distribute the ad's arc across the segments: the FIRST segment opens with a scroll-stopping HOOK, the middle segments show the problem and the product solving it, and the LAST segment ends with a punchy CTA.)

${ugcCatBlock}
Spread these demonstration close-ups across the segments where they fit naturally.

- \xC1UDIO (uma linha no fim): overall voiceover tone and a music vibe for the whole ad.
- CRITICAL CONTINUITY: the creator, wardrobe, room and product must look IDENTICAL across all segments so the stitched clips feel like one seamless video.
- Keep the energy authentic and conversational, not corporate.
- If a Marca/Produto or P\xFAblico-alvo is provided, weave it into the script and CTA and tailor the creator to the audience.
- If a real, identifiable person is implied, use a generic fictional creator \u2014 never name real public figures.`;
    const timelapseReqs = nSeg <= 1 ? `OUTPUT REQUIREMENTS (accelerated TIMELAPSE video prompt for tools like Sora, Veo, Runway, Kling):
- ${langLine}
- Return ONLY the structured prompt below. No extra commentary.
- Structure EXACTLY with these labeled sections, each on its own lines:

CONCEITO: one sentence describing what is built/made/transformed and the arc from start to finished result.
FORMATO: ${aspect}, accelerated timelapse, ~${tlTotal}s of screen time compressing hours/days of real time.
C\xC2MERA: a LOCKED-OFF tripod camera holding the exact same framing for the entire sequence \u2014 state the precise angle, height, distance and lens.
ETAPAS: a numbered list of 5\u20138 chronological stages; for EACH, what changes in frame and roughly how long it holds.
MOVIMENTO: time-compression cues \u2014 hands/people as blurred streaks, sun arcing, shadows sweeping, clouds racing, light ramping cold\u2192warm\u2192night, flicker-free.
ILUMINA\xC7\xC3O: the lighting setup and how it evolves.
\xC1UDIO: music vibe plus ambient/whoosh accents.
FINAL: the finished result held steady for a satisfying reveal.

TRANSFORMATION STAGES BY CATEGORY (infer from the idea): Construction \u2192 empty lot, foundation, framing, walls/roof, fa\xE7ade, interior, landscaping, reveal. Makeup \u2192 bare face, primer/base, contour, eyes, lips, setting, final. Car \u2192 chassis, teardown, engine, bodywork, primer, paint, wheels, interior, reveal. PC \u2192 parts on desk, motherboard, CPU/RAM, cooler, case, GPU, cable management, RGB boot. Food \u2192 ingredients, prep, cooking with steam, plating, finished dish. Painting \u2192 blank canvas, sketch, blocking, color, details, signed piece. Renovation \u2192 before room, demolition, paint, furniture, styling, final tour. If unclear: before \u2192 accelerated work \u2192 after held steady.
- CRITICAL: state that the framing stays IDENTICAL from first to last.
- If a real person is implied, use a generic fictional person \u2014 never name real public figures.` : `OUTPUT REQUIREMENTS (accelerated TIMELAPSE, SPLIT INTO ${nSeg} SEGMENTS for AI video tools that only make ${tlClip}s clips like Sora, Veo, Runway, Kling):
- ${langLine}
- The full timelapse lasts ~${tlTotal}s and is divided into ${nSeg} segments of ~${tlClip}s each, generated separately and stitched together in an editor afterward.
- Return ONLY the structured output below. No extra commentary.

First, one shared block so every segment stays consistent:

BASE (comum a todos os segmentos):
- C\xC2MERA: a LOCKED-OFF tripod camera with the EXACT SAME framing, angle, height, distance and lens across every segment \u2014 the single most important rule for the pieces to stitch seamlessly.
- CEN\xC1RIO/ESTILO: the fixed setting, palette and lighting logic that must stay identical across all segments.
- ARCO GERAL: one sentence describing the whole transformation from the very first frame to the very last finished result.

Then produce EXACTLY ${nSeg} segments. Format each one EXACTLY like this, on its own lines:

SEGMENTO 1 de ${nSeg}  \xB7  (tempo ~00:00\u201300:${String(tlClip).padStart(2, "0")})
\u{1F3AC} CLIPE: a self-contained ~${tlClip}s timelapse prompt ready to paste \u2014 restate the locked camera + setting so it works alone, then describe exactly which stage(s) of the transformation happen in THIS segment.
\u25B6\uFE0F FRAME INICIAL: describe the exact opening state of this segment (what already exists on screen).
\u23F9\uFE0F FRAME FINAL: describe the exact ending state \u2014 this MUST become the FRAME INICIAL of the next segment, so the cut is invisible.
\u{1F517} CONTINUIDADE: one line noting what to carry over (progress level, light/time-of-day, shadow position) so the next clip matches.

(repeat for SEGMENTO 2 de ${nSeg}, \u2026 up to SEGMENTO ${nSeg} de ${nSeg}, each covering ~${tlClip}s, so the segments together tell the full ~${tlTotal}s transformation in order)

- CRITICAL CONTINUITY: each segment's FRAME INICIAL must exactly match the previous segment's FRAME FINAL \u2014 same camera, same framing, progress only ever moving forward. The lighting/time-of-day should advance smoothly and consistently from segment to segment.
- Spread the transformation stages evenly so the LAST segment ends on the finished result held steady.
- Use the right stages for the inferred CATEGORY (construction, makeup, car, PC, food, painting, renovation, etc.).
- ${langLine}
- If a real person is implied, use a generic fictional person \u2014 never name real public figures.`;
    const carouselReqs = `OUTPUT REQUIREMENTS (INSTAGRAM CAROUSEL of ${cardCount} cards):
- ${langLine}
- Return ONLY the carousel below. No preamble or commentary.
- GOAL: ${carouselGoal === "sell" ? "storytelling that sells a product/offer \u2014 build desire and lead to a purchase/action." : "educational value \u2014 teach something useful and highly saveable (tips, steps, mistakes, how-to)."}
- Produce EXACTLY ${cardCount} cards. Format each EXACTLY like this:

CARD 1 \u2014 [role, e.g. "Gancho" / "Hook"]
\u{1F5BC}\uFE0F VISUAL: [ready-to-paste image prompt for this card's background \u2014 subject, composition, style, colors, mood, leaving space for the text overlay. 35\u201360 words${carLook ? `, in the ${carLook.label} visual style` : ""}.]
\u270D\uFE0F TEXTO: [the exact on-card copy \u2014 a bold short headline plus optional 1\u20132 supporting lines. Punchy, phone-readable.]

(repeat up to CARD ${cardCount})

- ARC: Card 1 is a scroll-stopping HOOK. Middle cards deliver the story/value. The LAST card is a clear CTA.
- Keep a CONSISTENT visual identity across all cards.
- After the cards add: LEGENDA: [a ready-to-post caption with a hook first line, the core message, light relevant hashtags, and a call to action.]
- If a Marca/Produto or P\xFAblico-alvo is provided, tailor copy and offer to them.
- If a real person is implied, use a generic fictional persona \u2014 never name real public figures.`;
    const storyboardReqs = `OUTPUT REQUIREMENTS (STORYBOARD \u2014 a sequence of ${frameCount} frames):
- ${langLine}
- Return ONLY the storyboard below. No preamble or commentary.
- Produce EXACTLY ${frameCount} frames. Format each EXACTLY like this:

QUADRO 1 \u2014 [short shot label, e.g. "Plano geral / estabelecimento"]
[A rich, self-contained image prompt for this frame \u2014 subject, appearance, wardrobe, action/expression, environment, camera framing and angle, lighting, color palette, mood, and the visual/rendering style. Ready to paste. 45\u201380 words.]
--ar ${aspect}

(repeat up to QUADRO ${frameCount})

- CONTINUITY IS CRITICAL: the same character(s) keep identical appearance and wardrobe across every frame; consistent setting, lighting and art style. Restate the key identity details in each frame's prompt so each stands alone.
- Vary the cinematography across frames for good storytelling rhythm.
- Each frame's prompt must be concrete and visual${lookObj ? `, in the ${lookObj.label} style` : ""}.
- If a real person is implied, render a generic fictional likeness \u2014 never name real public figures.`;
    let styleBlock;
    if (isCarousel) {
      styleBlock = carLook ? `TARGET: An INSTAGRAM CAROUSEL with each card's visual in the ${carLook.label} style.
CAROUSEL RULES: ${STYLE_BRIEFS.carrossel}

VISUAL STYLE RULES:
${STYLE_BRIEFS[carLook.id]}` : `TARGET: An INSTAGRAM CAROUSEL.
CAROUSEL RULES: ${STYLE_BRIEFS.carrossel}

VISUAL STYLE: clean, modern, cohesive social-media look across all cards.`;
    } else if (isStoryboard) {
      styleBlock = lookObj ? `TARGET: A STORYBOARD in the ${lookObj.label} visual style.
STORYBOARD RULES: ${STYLE_BRIEFS.storyboard}

VISUAL STYLE RULES:
${STYLE_BRIEFS[lookObj.id]}` : `TARGET: A STORYBOARD.
STORYBOARD RULES: ${STYLE_BRIEFS.storyboard}

VISUAL STYLE: clean neutral cinematic look consistent across all frames.`;
    } else if (chosen2) {
      styleBlock = `TARGET STYLE: ${chosen.label} BLENDED WITH ${chosen2.label}.
PRIMARY STYLE RULES:
${STYLE_BRIEFS[style]}

SECONDARY STYLE RULES:
${STYLE_BRIEFS[secondary]}

BLENDING: The primary style defines the medium and execution. The secondary contributes subject, mood, palette or motifs, harmonizing without breaking the primary medium.`;
    } else {
      styleBlock = `TARGET STYLE: ${chosen.label}.
STYLE RULES: ${STYLE_BRIEFS[style]}`;
    }
    const job = isCarousel ? `a production-ready INSTAGRAM CAROUSEL of ${cardCount} cards` : isStoryboard ? `a production-ready STORYBOARD of ${frameCount} sequential image prompts` : isVideo ? nSeg <= 1 ? "ONE production-ready video ad prompt" : `a production-ready UGC video ad SPLIT INTO ${nSeg} stitchable segments` : isTimelapse ? nSeg <= 1 ? "ONE production-ready accelerated timelapse video prompt" : `a production-ready accelerated timelapse SPLIT INTO ${nSeg} stitchable segments` : "ONE extremely detailed, vivid, production-ready image prompt";
    const reqs = isCarousel ? carouselReqs : isStoryboard ? storyboardReqs : isVideo ? videoReqs : isTimelapse ? timelapseReqs : imageReqs;
    const system = `You are an elite prompt engineer for AI ${isMotion ? "video" : "image"} generators${isCarousel ? " and a social-media copywriter" : ""}.
Your job: turn a short user idea into ${job}.

${langDirective}

${styleBlock}

${reqs}

${langDirective}`;
    const extras = [];
    if (brand.trim()) extras.push(`Marca/Produto: "${brand.trim()}"`);
    if (audience.trim()) extras.push(`P\xFAblico-alvo: "${audience.trim()}"`);
    if (isVideo && adScript.trim()) extras.push(`Mensagem/roteiro que o usu\xE1rio QUER no an\xFAncio (use como base obrigat\xF3ria, adaptando o tom para UGC): "${adScript.trim()}"`);
    const userMsg = `Ideia do usu\xE1rio: "${idea.trim()}"${extras.length ? "\n" + extras.join("\n") : ""}`;
    const input = `${system}

=== PEDIDO DO USU\xC1RIO ===
${userMsg}`;
    try {
      const text = await askClaude(input, {
        cache: false,
        modelTier: "default",
        onText: ({ text: text2 }) => setResult(text2)
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
      setRevImage({ file, preview: e.target.result });
      setError("");
    };
    reader.readAsDataURL(file);
  }
  async function reverseEngineer() {
    if (!revImage) {
      setError("Envie uma imagem primeiro \u{1F5BC}\uFE0F");
      return;
    }
    setError("");
    setResult("");
    setCopied(false);
    setShowPage(false);
    setFrameImages({});
    setLoading(true);
    const langLine = outLang === "en" ? "Write the entire output in ENGLISH (best for AI generators)." : "Escreva toda a sa\xEDda em PORTUGU\xCAS do Brasil.";
    const focusLine = revFocus === "faithful" ? "GOAL: reverse-engineer a prompt that would RECREATE this exact image as faithfully as possible." : "GOAL: extract mainly the STYLE, technique, lighting and mood of this image so the user can apply that look to a DIFFERENT subject.";
    const system = `You are an expert reverse-prompt engineer for AI image generators. Analyze the given image deeply and produce a prompt that could reproduce its look.

${focusLine}

${langLine}

Return your answer in EXACTLY this structure:

PROMPT:
[One cohesive, comma-separated prompt block ready to paste \u2014 80\u2013150 words, covering subject, style/medium, composition, lighting, color, mood and technical cues. End with fitting tags on a new line.]

AN\xC1LISE:
\u2022 Estilo/Meio: [...]
\u2022 Cen\xE1rio/Local: [...]
\u2022 Composi\xE7\xE3o/Enquadramento: [...]
\u2022 Personagens/Sujeito: [describe people GENERICALLY, never identify real individuals]
\u2022 Ilumina\xE7\xE3o: [...]
\u2022 Cores/Paleta: [...]
\u2022 Clima/Atmosfera: [...]
\u2022 T\xE9cnica/Render: [...]

RULES:
- ${langLine}
- Keep the labels PROMPT: and AN\xC1LISE: exactly.
- NEVER name or guess the identity of any real person.
- Be concrete; infer plausible technical details from visual evidence.`;
    const input = `${system}

Analise a imagem anexada seguindo exatamente a estrutura e as regras acima.`;
    try {
      const text = await askClaude(input, {
        images: revImage.file,
        cache: false,
        modelTier: "default",
        onText: ({ text: text2 }) => setResult(text2)
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
      return { num: m && m[1] || String(i + 1), label: (m && m[2] || "").trim(), prompt: body };
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
    try {
      document.execCommand("copy");
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch (e) {
    }
    document.body.removeChild(ta);
  }
  const primaryObj = STYLES.find((s) => s.id === style);
  const secondaryObj = secondary ? STYLES.find((s) => s.id === secondary) : null;
  const allowCombine = canCombineAny(style) && !(primaryObj && primaryObj.video);
  const storyboardActive = style === "storyboard" || secondary === "storyboard";
  const carouselActive = primaryObj && primaryObj.carousel || secondaryObj && secondaryObj.carousel;
  const timelapseActive = primaryObj && primaryObj.timelapse;
  const L = { mono: { fontFamily: "'DM Mono', monospace" }, black: { fontFamily: "'Archivo Black', sans-serif" }, sans: { fontFamily: "'DM Sans', sans-serif" } };
  return /* @__PURE__ */ React.createElement("div", { className: "min-h-screen w-full text-[#f4ede0]", style: { background: "#0f0d0a", ...L.sans } }, /* @__PURE__ */ React.createElement("style", null, `
        /* fontes: do sistema (offline; Google Fonts removido) */
        @keyframes pulseDot { 0%,100%{opacity:.25;transform:scale(.8)} 50%{opacity:1;transform:scale(1.2)} }
        @keyframes riseIn { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
        .rise { animation: riseIn .5s cubic-bezier(.2,.8,.2,1) both; }
        .grain:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.04;z-index:50;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}
      `), /* @__PURE__ */ React.createElement("div", { className: "grain" }), /* @__PURE__ */ React.createElement("div", { className: "pointer-events-none fixed inset-0 z-0" }, /* @__PURE__ */ React.createElement("div", { className: "absolute -top-32 -left-24 h-96 w-96 rounded-full blur-3xl", style: { background: "radial-gradient(circle,#ff7a18,transparent 70%)", opacity: 0.06 } }), /* @__PURE__ */ React.createElement("div", { className: "absolute bottom-0 right-0 h-96 w-96 rounded-full blur-3xl", style: { background: "radial-gradient(circle,#ff7a18,transparent 70%)", opacity: 0.05 } })), /* @__PURE__ */ React.createElement("div", { className: "relative z-10 mx-auto max-w-3xl px-5 py-10 sm:py-14" }, /* @__PURE__ */ React.createElement("header", { className: "mb-9" }, /* @__PURE__ */ React.createElement("div", { className: "mb-3 inline-flex items-center gap-2 rounded-full border border-[#ff7a18]/30 bg-[#ff7a18]/10 px-3 py-1 text-xs tracking-wide", style: L.mono }, /* @__PURE__ */ React.createElement("span", { className: "h-2 w-2 rounded-full bg-[#ff7a18]", style: { animation: "pulseDot 1.6s infinite" } }), "GERADOR DE PROMPTS \xB7 IA"), /* @__PURE__ */ React.createElement("h1", { className: "text-4xl leading-[0.95] sm:text-6xl", style: { ...L.black, letterSpacing: "-0.02em" } }, "FORJA DE", /* @__PURE__ */ React.createElement("br", null), /* @__PURE__ */ React.createElement("span", { className: "text-[#ff7a18]" }, "PROMPTS")), /* @__PURE__ */ React.createElement("p", { className: "mt-3 max-w-lg text-sm text-[#8c8475] sm:text-base" }, "Digite uma ideia simples, escolha o estilo (ou misture dois!) e receba um prompt cinematogr\xE1fico, detalhado e pronto pra colar.")), /* @__PURE__ */ React.createElement("div", { className: "mb-6 grid grid-cols-2 gap-2 rounded-2xl border border-[#2a2620] bg-[#161310] p-1.5" }, [["generate", "\u2692 Gerar", "ideia \u2192 prompt"], ["reverse", "\u{1F50D} Engenharia reversa", "imagem \u2192 prompt"]].map(([v, label, sub]) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: v,
      onClick: () => {
        setMode(v);
        setResult("");
        setError("");
      },
      className: `rounded-xl px-3 py-2.5 text-center transition ${mode === v ? "bg-[#ff7a18] text-[#1a1206]" : "text-[#8c8475] hover:text-[#f4ede0]"}`
    },
    /* @__PURE__ */ React.createElement("div", { className: "text-sm font-bold", style: L.black }, label),
    /* @__PURE__ */ React.createElement("div", { className: `text-[10px] ${mode === v ? "text-[#1a1206]/70" : "text-[#6e675b]"}`, style: L.mono }, sub)
  ))), mode === "generate" && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Sua ideia"), /* @__PURE__ */ React.createElement(
    "textarea",
    {
      value: idea,
      onChange: (e) => setIdea(e.target.value),
      placeholder: primaryObj && primaryObj.video ? "ex: an\xFAncio de um s\xE9rum facial; criadora mostrando o resultado na pele..." : timelapseActive ? "ex: constru\xE7\xE3o de uma casa do zero num terreno vazio... / maquiagem completa do rosto limpo at\xE9 o look final... / montagem de um PC gamer na bancada..." : carouselActive ? "ex: 5 erros que est\xE3o matando suas vendas no Instagram... / como meu produto transformou a rotina de skincare da cliente..." : "ex: uma guerreira ruiva sob a chuva numa cidade antiga...",
      rows: 3,
      className: "w-full resize-none rounded-2xl border border-[#2a2620] bg-[#141210] p-4 text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]"
    }
  ), primaryObj && primaryObj.video && /* @__PURE__ */ React.createElement("p", { className: "mt-2 rounded-xl border border-[#ff7a18]/25 bg-[#ff7a18]/5 px-3 py-2 text-[12px] leading-snug text-[#8c8475]" }, "\u{1F4A1} O roteiro j\xE1 inclui a instru\xE7\xE3o de ", /* @__PURE__ */ React.createElement("b", null, "usar a foto do produto como refer\xEAncia"), ". Anexe a imagem do produto na ferramenta de v\xEDdeo usando o recurso de ", /* @__PURE__ */ React.createElement("i", null, "imagem de refer\xEAncia / image-to-video"), "."), timelapseActive && /* @__PURE__ */ React.createElement("p", { className: "mt-2 rounded-xl border border-[#ff7a18]/25 bg-[#ff7a18]/5 px-3 py-2 text-[12px] leading-snug text-[#8c8475]" }, "\u23F1\uFE0F Detecta o ", /* @__PURE__ */ React.createElement("b", null, "tipo de projeto"), " e monta as etapas certas, com ", /* @__PURE__ */ React.createElement("b", null, "c\xE2mera travada"), ". Timelapses longos s\xE3o ", /* @__PURE__ */ React.createElement("b", null, "fatiados em segmentos"), " que emendam, respeitando o limite de clipe das IAs."), (primaryObj && primaryObj.video || carouselActive) && /* @__PURE__ */ React.createElement("div", { className: "mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Marca / Produto ", /* @__PURE__ */ React.createElement("span", { className: "text-[#6e675b] normal-case" }, "(opcional)")), /* @__PURE__ */ React.createElement("input", { value: brand, onChange: (e) => setBrand(e.target.value), placeholder: "ex: Loja Aurora \u2014 jaqueta corta-vento", className: "w-full rounded-xl border border-[#2a2620] bg-[#141210] px-3 py-2.5 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" })), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "P\xFAblico-alvo ", /* @__PURE__ */ React.createElement("span", { className: "text-[#6e675b] normal-case" }, "(opcional)")), /* @__PURE__ */ React.createElement("input", { value: audience, onChange: (e) => setAudience(e.target.value), placeholder: "ex: mulheres 25-40 que treinam ao ar livre", className: "w-full rounded-xl border border-[#2a2620] bg-[#141210] px-3 py-2.5 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" }))), primaryObj && primaryObj.video && /* @__PURE__ */ React.createElement("div", { className: "mt-3" }, /* @__PURE__ */ React.createElement("label", { className: "mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Texto / Mensagem do an\xFAncio ", /* @__PURE__ */ React.createElement("span", { className: "text-[#6e675b] normal-case" }, "(opcional)")), /* @__PURE__ */ React.createElement("textarea", { value: adScript, onChange: (e) => setAdScript(e.target.value), placeholder: "ex: Fale sobre o desconto de 30% s\xF3 essa semana; mencione que tem frete gr\xE1tis; termine com 'corre que acaba r\xE1pido!'", rows: 3, className: "w-full resize-none rounded-xl border border-[#2a2620] bg-[#141210] p-3 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#8c8475]" }), /* @__PURE__ */ React.createElement("p", { className: "mt-1.5 text-[11px] leading-snug text-[#8c8475]", style: L.mono }, "Deixe vazio pra IA criar o roteiro do zero, ou escreva as falas/pontos que devem aparecer.")), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-7 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Estilo principal"), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-2.5 sm:grid-cols-3" }, STYLES.map((s) => {
    const active = s.id === style;
    return /* @__PURE__ */ React.createElement(
      "button",
      {
        key: s.id,
        onClick: () => {
          setStyle(s.id);
          if (s.video) setAspect("9:16");
          if (s.timelapse) setAspect("16:9");
          if (s.carousel) setAspect("4:5");
        },
        className: `group relative rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 shadow-[0_0_20px_rgba(255,122,24,0.25)] -translate-y-0.5" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}`
      },
      active && /* @__PURE__ */ React.createElement("span", { className: "absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ff7a18] text-[11px] font-black text-[#1a1206]" }, "\u2713"),
      /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-lg" }, s.tag), /* @__PURE__ */ React.createElement("span", { className: `text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}` }, s.label)),
      /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}` }, s.hint)
    );
  })), allowCombine && /* @__PURE__ */ React.createElement("div", { className: "mt-5" }, /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: () => {
        if (combineOpen) {
          setCombineOpen(false);
          setSecondary(null);
        } else setCombineOpen(true);
      },
      className: `flex w-full items-center justify-center gap-2 rounded-2xl border-2 px-4 py-3 text-sm font-bold transition ${combineOpen || secondary ? "border-[#ff7a18] bg-[#ff7a18]/10 text-[#ff9a6a]" : "border-dashed border-[#4a4338] bg-transparent text-[#8c8475] hover:border-[#ff7a18]/60 hover:text-[#ff9a6a]"}`,
      style: L.mono
    },
    combineOpen || secondary ? "\u2715 Remover combina\xE7\xE3o" : "+ Combinar com outro estilo"
  ), combineOpen && /* @__PURE__ */ React.createElement("div", { className: "rise mt-4" }, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Segundo estilo (mistura)"), /* @__PURE__ */ React.createElement("p", { className: "mb-3 text-[11px] text-[#8c8475]", style: L.mono }, "Op\xE7\xF5es esmaecidas s\xE3o incompat\xEDveis com ", /* @__PURE__ */ React.createElement("span", { className: "text-[#ff9a6a]" }, primaryObj && primaryObj.label), "."), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-2.5 sm:grid-cols-3" }, STYLES.map((s) => {
    if (s.id === style) return null;
    const compatible = canCombine(style, s.id);
    const active = s.id === secondary;
    return /* @__PURE__ */ React.createElement(
      "button",
      {
        key: s.id,
        disabled: !compatible,
        onClick: () => setSecondary(s.id),
        title: compatible ? "" : `Incompat\xEDvel com ${primaryObj && primaryObj.label}`,
        className: `group relative rounded-2xl border-2 p-3 text-left transition ${!compatible ? "cursor-not-allowed border-[#2a2620] bg-[#0f0d0a] opacity-30" : active ? "border-[#ff7a18] bg-[#ff7a18]/15 ring-2 ring-[#ff7a18]/40 shadow-[0_0_20px_rgba(255,209,102,0.2)] -translate-y-0.5" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}`
      },
      active && /* @__PURE__ */ React.createElement("span", { className: "absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ff7a18] text-[11px] font-black text-[#1a1206]" }, "\u2713"),
      /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-lg" }, s.tag), /* @__PURE__ */ React.createElement("span", { className: `text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}` }, s.label)),
      /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}` }, s.hint)
    );
  })), secondaryObj && /* @__PURE__ */ React.createElement("div", { className: "rise mt-4 rounded-xl border border-[#ff7a18]/30 bg-gradient-to-r from-[#ff7a18]/10 to-[#ff7a18]/10 px-4 py-3 text-sm" }, /* @__PURE__ */ React.createElement("span", { className: "text-[#8c8475]" }, "Misturando:"), " ", /* @__PURE__ */ React.createElement("span", { className: "font-bold text-[#ff7a18]" }, primaryObj.tag, " ", primaryObj.label), /* @__PURE__ */ React.createElement("span", { className: "mx-2 text-[#ff9a6a]" }, "+"), /* @__PURE__ */ React.createElement("span", { className: "font-bold text-[#ff9a6a]" }, secondaryObj.tag, " ", secondaryObj.label)))), (timelapseActive || primaryObj && primaryObj.video) && /* @__PURE__ */ React.createElement("div", { className: "rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4" }, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#ff9a6a]", style: L.mono }, "\u23F1\uFE0F Dura\xE7\xE3o total do v\xEDdeo"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, TL_TOTALS.map(([v, l]) => /* @__PURE__ */ React.createElement("button", { key: v, onClick: () => setTlTotal(v), className: `rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === tlTotal ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`, style: L.mono }, l))), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-5 block text-xs uppercase tracking-widest text-[#ff9a6a]", style: L.mono }, "Dura\xE7\xE3o de cada clipe da IA"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, TL_CLIPS.map((n) => /* @__PURE__ */ React.createElement("button", { key: n, onClick: () => setTlClip(n), className: `rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === tlClip ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`, style: L.mono }, n, "s"))), /* @__PURE__ */ React.createElement("p", { className: "mt-3 text-[11px] leading-snug text-[#8c8475]" }, segCount <= 1 ? /* @__PURE__ */ React.createElement(React.Fragment, null, "Cabe em ", /* @__PURE__ */ React.createElement("b", { className: "text-[#ff9a6a]" }, "1 clipe"), " s\xF3 \u2014 roteiro \xFAnico.") : timelapseActive ? /* @__PURE__ */ React.createElement(React.Fragment, null, "Vai gerar ", /* @__PURE__ */ React.createElement("b", { className: "text-[#ff9a6a]" }, segCount, " segmentos"), " de ~", tlClip, "s que emendam, cada um com frame inicial/final pra continuidade perfeita. Voc\xEA gera clipe por clipe e junta no editor.") : /* @__PURE__ */ React.createElement(React.Fragment, null, "Vai gerar ", /* @__PURE__ */ React.createElement("b", { className: "text-[#ff9a6a]" }, segCount, " segmentos"), " de ~", tlClip, "s que emendam, com a mesma criadora e produto em todos. Voc\xEA gera clipe por clipe e junta no editor."))), storyboardActive && /* @__PURE__ */ React.createElement("div", { className: "rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4" }, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#ff9a6a]", style: L.mono }, "\u{1F3AC} Quantos quadros?"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, [3, 4, 5, 6, 7, 8].map((n) => /* @__PURE__ */ React.createElement("button", { key: n, onClick: () => setFrameCount(n), className: `rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === frameCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`, style: L.mono }, n))), /* @__PURE__ */ React.createElement("p", { className: "mt-2.5 text-[11px] leading-snug text-[#8c8475]" }, "O storyboard gera ", /* @__PURE__ */ React.createElement("b", { className: "text-[#ff9a6a]" }, frameCount, " prompts"), " em sequ\xEAncia, com continuidade. ", secondaryObj ? "" : "\u{1F4A1} Combine com um estilo visual pra definir o look dos quadros.")), carouselActive && /* @__PURE__ */ React.createElement("div", { className: "rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4" }, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#ff9a6a]", style: L.mono }, "\u{1F3A0} Objetivo do carrossel"), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 gap-2.5 sm:grid-cols-2" }, [["sell", "\u{1F6CD}\uFE0F Storytelling / Venda", "Cria desejo e leva \xE0 a\xE7\xE3o"], ["educate", "\u{1F4A1} Educativo / Dicas", "Ensina algo salv\xE1vel"]].map(([v, label, sub]) => {
    const active = carouselGoal === v;
    return /* @__PURE__ */ React.createElement("button", { key: v, onClick: () => setCarouselGoal(v), className: `rounded-xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}` }, /* @__PURE__ */ React.createElement("div", { className: `text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}` }, label), /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}` }, sub));
  })), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-5 block text-xs uppercase tracking-widest text-[#ff9a6a]", style: L.mono }, "Quantos cards?"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, [3, 4, 5, 6, 7, 8, 9, 10].map((n) => /* @__PURE__ */ React.createElement("button", { key: n, onClick: () => setCardCount(n), className: `rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${n === cardCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`, style: L.mono }, n))), /* @__PURE__ */ React.createElement("p", { className: "mt-2.5 text-[11px] leading-snug text-[#8c8475]" }, "Gera ", /* @__PURE__ */ React.createElement("b", { className: "text-[#ff9a6a]" }, cardCount, " cards"), " (visual + copy) do gancho ao CTA, mais uma legenda pronta pra postar. ", secondaryObj ? "" : "\u{1F4A1} Combine com um estilo visual pra definir o look dos cards.")), /* @__PURE__ */ React.createElement("div", { className: "mt-7 flex flex-wrap items-end gap-6" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Propor\xE7\xE3o"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, ASPECTS.map((a) => /* @__PURE__ */ React.createElement("button", { key: a, onClick: () => setAspect(a), className: `rounded-lg border-2 px-2.5 py-1.5 text-xs font-bold transition ${a === aspect ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`, style: L.mono }, a)))), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Idioma do prompt"), /* @__PURE__ */ React.createElement("div", { className: "flex gap-1.5" }, [["en", "Ingl\xEAs"], ["pt", "Portugu\xEAs"]].map(([v, l]) => /* @__PURE__ */ React.createElement("button", { key: v, onClick: () => setOutLang(v), className: `rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`, style: L.mono }, l))))), /* @__PURE__ */ React.createElement("button", { onClick: generate, disabled: loading, className: "mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60", style: { ...L.black, letterSpacing: "0.01em" } }, loading ? /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("span", { className: "h-2 w-2 rounded-full bg-[#1a1206]", style: { animation: "pulseDot 1s infinite" } }), "FORJANDO...") : /* @__PURE__ */ React.createElement(React.Fragment, null, "\u2692 GERAR PROMPT")), error && /* @__PURE__ */ React.createElement("p", { className: "mt-3 text-center text-sm text-[#ff8c3a]" }, error)), mode === "reverse" && /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Imagem de refer\xEAncia"), /* @__PURE__ */ React.createElement("label", { className: "relative block cursor-pointer" }, /* @__PURE__ */ React.createElement("div", { className: "flex min-h-[180px] items-center justify-center rounded-2xl border-2 border-dashed border-[#4a4338] bg-[#161310] bg-contain bg-center bg-no-repeat p-4 transition hover:border-[#ff7a18]/60", style: revImage ? { backgroundImage: `url(${revImage.preview})`, minHeight: "280px" } : {} }, !revImage && /* @__PURE__ */ React.createElement("div", { className: "text-center" }, /* @__PURE__ */ React.createElement("div", { className: "text-4xl" }, "\u{1F5BC}\uFE0F"), /* @__PURE__ */ React.createElement("div", { className: "mt-2 text-sm font-bold text-[#8c8475]" }, "Clique pra enviar uma imagem"), /* @__PURE__ */ React.createElement("div", { className: "mt-1 text-[11px] text-[#8c8475]", style: L.mono }, "PNG, JPG ou WEBP"))), /* @__PURE__ */ React.createElement("input", { type: "file", accept: "image/*", className: "hidden", onChange: (e) => handleRevImage(e.target.files && e.target.files[0]) })), revImage && /* @__PURE__ */ React.createElement("button", { onClick: () => setRevImage(null), className: "mt-2 text-[11px] text-[#8c8475] underline transition hover:text-[#ff8c3a]", style: L.mono }, "remover imagem"), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Foco da an\xE1lise"), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 gap-2.5 sm:grid-cols-2" }, [["faithful", "\u{1F3AF} Recriar fiel", "Reproduz a imagem o mais parecido poss\xEDvel"], ["style", "\u{1F3A8} Capturar estilo", "Extrai s\xF3 o 'look' pra usar em outra ideia"]].map(([v, label, sub]) => {
    const active = revFocus === v;
    return /* @__PURE__ */ React.createElement("button", { key: v, onClick: () => setRevFocus(v), className: `rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 -translate-y-0.5" : "border-[#2a2620] bg-[#161310] hover:border-[#4a4338]"}` }, /* @__PURE__ */ React.createElement("div", { className: `text-sm font-bold ${active ? "text-[#ff9a6a]" : ""}` }, label), /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#8c8475]" : "text-[#8c8475]"}` }, sub));
  })), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "Idioma do resultado"), /* @__PURE__ */ React.createElement("div", { className: "flex gap-1.5" }, [["en", "Ingl\xEAs"], ["pt", "Portugu\xEAs"]].map(([v, l]) => /* @__PURE__ */ React.createElement("button", { key: v, onClick: () => setOutLang(v), className: `rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ff9a6a] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`, style: L.mono }, l))), /* @__PURE__ */ React.createElement("button", { onClick: reverseEngineer, disabled: loading, className: "mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60", style: { ...L.black, letterSpacing: "0.01em" } }, loading ? /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("span", { className: "h-2 w-2 rounded-full bg-[#1a1206]", style: { animation: "pulseDot 1s infinite" } }), "ANALISANDO...") : /* @__PURE__ */ React.createElement(React.Fragment, null, "\u{1F50D} EXTRAIR PROMPT")), error && /* @__PURE__ */ React.createElement("p", { className: "mt-3 text-center text-sm text-[#ff8c3a]" }, error)), result && /* @__PURE__ */ React.createElement("div", { ref: outRef, className: "rise mt-9 rounded-2xl border border-[#2a2620] bg-[#141210] p-5" }, /* @__PURE__ */ React.createElement("div", { className: "mb-3 flex items-center justify-between" }, /* @__PURE__ */ React.createElement("span", { className: "text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, mode === "reverse" ? "Prompt extra\xEDdo da imagem" : primaryObj && primaryObj.video ? segCount > 1 ? `An\xFAncio \xB7 ${segCount} segmentos` : "Roteiro do an\xFAncio" : timelapseActive ? segCount > 1 ? `Timelapse \xB7 ${segCount} segmentos` : "Roteiro do timelapse" : carouselActive ? `Carrossel \xB7 ${cardCount} cards` : storyboardActive ? `Storyboard \xB7 ${frameCount} quadros` : "Prompt gerado"), /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, mode === "generate" && storyboardActive && /* @__PURE__ */ React.createElement("button", { onClick: () => setShowPage((v) => !v), className: "rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#ff9a6a] transition hover:bg-[#ff7a18]/20" }, showPage ? "\u2715 Fechar p\xE1gina" : "\u{1F4D6} Montar p\xE1gina"), /* @__PURE__ */ React.createElement("button", { onClick: copyResult, className: "rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#ff9a6a] transition hover:bg-[#ff7a18]/20" }, copied ? "\u2713 Copiado!" : "Copiar"))), /* @__PURE__ */ React.createElement("p", { className: "whitespace-pre-wrap text-[15px] leading-relaxed text-[#bdb3a3]", style: L.mono }, result)), result && storyboardActive && showPage && mode === "generate" && /* @__PURE__ */ React.createElement("div", { className: "rise mt-6" }, /* @__PURE__ */ React.createElement("div", { className: "mb-3 flex items-center justify-between" }, /* @__PURE__ */ React.createElement("span", { className: "text-xs uppercase tracking-widest text-[#8c8475]", style: L.mono }, "\u{1F4D6} Prancha \xB7 clique num quadro pra adicionar a imagem")), /* @__PURE__ */ React.createElement("div", { className: "rounded-2xl bg-[#1f1c17] p-3 sm:p-4 shadow-2xl" }, /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 gap-3 sm:grid-cols-2" }, parseFrames(result).map((f, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: "overflow-hidden rounded-sm border-[3px] border-[#111] bg-white" }, /* @__PURE__ */ React.createElement("label", { className: "relative block cursor-pointer" }, /* @__PURE__ */ React.createElement("div", { className: "flex aspect-video items-center justify-center border-b-[3px] border-[#111] bg-[#d9d3c6] bg-cover bg-center", style: frameImages[i] ? { backgroundImage: `url(${frameImages[i]})` } : {} }, !frameImages[i] && /* @__PURE__ */ React.createElement("div", { className: "text-center" }, /* @__PURE__ */ React.createElement("div", { className: "text-2xl" }, "\u{1F5BC}\uFE0F"), /* @__PURE__ */ React.createElement("div", { className: "mt-1 text-[11px] font-bold text-[#8c8475]", style: L.mono }, "clique pra colar a imagem")), /* @__PURE__ */ React.createElement("span", { className: "absolute left-0 top-0 bg-[#111] px-2 py-0.5 text-xs font-black text-[#ff9a6a]", style: L.black }, f.num)), /* @__PURE__ */ React.createElement("input", { type: "file", accept: "image/*", className: "hidden", onChange: (e) => handleFrameImage(i, e.target.files && e.target.files[0]) })), /* @__PURE__ */ React.createElement("div", { className: "p-2.5" }, f.label && /* @__PURE__ */ React.createElement("div", { className: "mb-1 text-[11px] font-black uppercase tracking-wide text-[#111]", style: L.black }, f.label), /* @__PURE__ */ React.createElement("p", { className: "text-[11px] leading-snug text-[#333]", style: L.mono }, f.prompt)))))), /* @__PURE__ */ React.createElement("p", { className: "mt-2.5 text-center text-[11px] text-[#8c8475]", style: L.mono }, "\u{1F4A1} Gere cada imagem no seu app favorito usando os prompts, depois clique nos quadros pra montar sua HQ. Use o print da tela pra salvar a prancha.")), /* @__PURE__ */ React.createElement("footer", { className: "mt-12 text-center text-[11px] text-[#6e675b]", style: L.mono }, "feito com IA \xB7 cole o resultado no seu gerador de imagens favorito")));
}
window.__mountForja = function() {
  var el = document.getElementById("forja-root");
  if (!el || el.__mounted) return;
  el.__mounted = true;
  ReactDOM.createRoot(el).render(React.createElement(App));
};
