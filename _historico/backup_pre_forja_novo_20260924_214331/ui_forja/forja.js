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
  return !!COMPAT[aCat]?.includes(bCat);
}
function canCombineAny(aId) {
  const aCat = STYLE_CATEGORIES[aId];
  return (COMPAT[aCat]?.length || 0) > 0;
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
    const videoReqs = `OUTPUT REQUIREMENTS (this is a VIDEO ad prompt for tools like Sora, Veo, Runway, Kling):
- ${langLine}
- Return ONLY the structured prompt below. No extra commentary before or after.
- Structure it EXACTLY with these labeled sections, each on its own lines:

CONCEITO: one sentence describing the overall ad and the creator/talent (relatable, fictional, never a named real person).
REFER\xCANCIA: an explicit instruction telling the video tool to use the user's ATTACHED REFERENCE IMAGE as the exact product \u2014 keep its real shape, color, logo, label, and proportions consistent across every shot; do not redesign or invent a different product.
FORMATO: vertical ${aspect.includes(":") && aspect.split(":")[0] > aspect.split(":")[1] ? "9:16" : aspect}, total duration ~15\u201325s, authentic phone-shot UGC look.
CENAS: a numbered shot list (4\u20136 shots). For EACH shot give: the visual (setting, framing, camera move, how the product is held/worn/used, lighting) AND the spoken line the creator says, written naturally and casually. Include at least one slow, stable CLOSE-UP of the product on a clean/uncluttered background and a steady hold so the reference product stays recognizable; avoid fast motion, harsh angles, heavy shadows or partial cropping on the product itself.

RESULT / DEMONSTRATION SHOTS (very important): infer the product CATEGORY from the idea and brand, and ALWAYS include the close-up shots that actually SELL that category \u2014 showing the product in use and its visible RESULT, not just the package. Apply the matching ones:
- Makeup / cosmetics \u2192 macro close-ups of application on skin (foundation blending into pores, concealer covering blemishes), lips for lipstick/gloss with light catching the shine, eyes for shadow/mascara, plus a clear BEFORE-and-AFTER of the treated area.
- Skincare \u2192 extreme close-up of skin texture before, the product's texture/spread on skin, and an after glow/hydration result.
- Perfume / fragrance \u2192 close-up of the bottle, the spray gesture and mist, wrist/neck application.
- Hair products \u2192 close-up of hair texture, the application, and the after shine/volume/movement.
- Food / drink \u2192 appetizing macro of the food, steam/pour/texture, and a real bite or sip with genuine reaction.
- Apparel / accessories \u2192 close-up of fabric texture and stitching, the fit/drape on the body, and movement.
- Tech / gadgets \u2192 close-up of the screen/buttons/key feature actually working, hands interacting.
- Cleaning / home \u2192 before-and-after of the surface, the product visibly working.
- Supplements / wellness \u2192 the product, the routine of taking it, and a lifestyle result moment.
If the category is unclear, default to: product close-up + the product clearly in use + the visible benefit it delivers.
TEXTO NA TELA: 2\u20134 short on-screen captions/overlays (hook + key benefit + CTA).
\xC1UDIO: voiceover tone, ambient sound, and a music vibe suggestion.
CTA: the final spoken + on-screen call to action.

- Keep the energy authentic and conversational, not corporate. Show the product clearly with at least one close-up demo shot.
- Prioritize product fidelity: stable framing, even lighting on the product, clean backgrounds behind it, and the product kept fully in frame during demo shots.
- If a Marca/Produto is provided, weave the product naturally into the script and CTA. If a P\xFAblico-alvo is provided, tailor the creator's look, language, setting and pain points to that audience.
- If a real, identifiable person is implied, use a generic fictional creator instead \u2014 never name real public figures.`;
    const timelapseReqs = `OUTPUT REQUIREMENTS (this is an accelerated TIMELAPSE video prompt for tools like Sora, Veo, Runway, Kling):
- ${langLine}
- Return ONLY the structured prompt below. No extra commentary before or after.
- Structure it EXACTLY with these labeled sections, each on its own lines:

CONCEITO: one sentence describing what is being built, made or transformed, and the full arc from the starting state to the finished result.
FORMATO: ${aspect}, accelerated timelapse, ~10\u201320s of screen time compressing hours, days or weeks of real time.
C\xC2MERA: a LOCKED-OFF camera on a tripod holding the exact same framing for the entire sequence \u2014 this is what makes the transformation readable. State the precise angle, height, distance and lens. If motion is wanted instead, specify a slow smooth hyperlapse, keeping the subject centered and consistent.
ETAPAS: a numbered list of 5\u20138 stages in chronological order. For EACH stage describe exactly what changes inside the frame, what appears or disappears, and roughly how long it holds on screen.
MOVIMENTO: the time-compression cues \u2014 hands, people and vehicles reduced to blurred streaks, the sun arcing across the sky, shadows sweeping across the ground, clouds racing, light ramping smoothly from cold morning to warm afternoon to night, flicker-free.
ILUMINA\xC7\xC3O: the lighting setup and how it evolves across the sequence (a natural daylight cycle outdoors, or constant even studio light indoors).
\xC1UDIO: music vibe plus any ambient or whoosh accents.
FINAL: the last shot \u2014 the finished result held steady for a satisfying reveal.

TRANSFORMATION STAGES BY CATEGORY (very important): infer the CATEGORY from the user's idea and use the stages that actually tell that story. Apply the matching one:
- Construction / building \u2192 empty lot, excavation and foundation, structure and framing rising, walls and roof, fa\xE7ade and windows, interior finishes, landscaping, final reveal; sun arcing, shadows sweeping, workers as blurred streaks.
- Makeup \u2192 bare clean face, primer and base, concealer and contour, blush, eyes and lashes, lips, setting spray, final look; macro framing locked on the face, hands blurring in and out, products swapping on the counter.
- Car build / restoration \u2192 bare shell or chassis, teardown, engine and drivetrain drop-in, bodywork and sanding, primer, paint booth and glossy coat, wheels and trim, interior, final gleaming reveal.
- PC build \u2192 parts laid out on the desk, motherboard prep, CPU and RAM, cooler, case mounting, GPU install, cable management, RGB lighting up on first boot.
- Cooking / food \u2192 raw ingredients, prep and chopping, cooking with rising steam, assembly, plating and garnish, finished dish.
- Art / painting \u2192 blank canvas, sketch, blocking in shapes, layers of color, refinement, fine details, signed final piece.
- Renovation / room makeover \u2192 the 'before' room, demolition, structure and paint, furniture arriving, styling, final tour.
- Nature / growth \u2192 seed in soil, sprout breaking through, leaves unfurling, growth, bud swelling, full bloom.
- City / sky \u2192 light shifting through the day, traffic as light trails, clouds racing, day-to-night transition.
If the category is unclear, default to: the untouched 'before' state \u2192 the work happening in accelerated stages \u2192 the finished 'after' held steady.

- CRITICAL: state explicitly in the prompt that the framing stays IDENTICAL from the first stage to the last, so the viewer reads the transformation clearly.
- If a real, identifiable person is implied, use a generic fictional person instead \u2014 never name real public figures.`;
    const carouselReqs = `OUTPUT REQUIREMENTS (this is an INSTAGRAM CAROUSEL of ${cardCount} cards):
- ${langLine}
- Return ONLY the carousel below. No preamble or commentary before or after.
- GOAL OF THE CAROUSEL: ${carouselGoal === "sell" ? "storytelling that sells a product/offer \u2014 build desire and lead to a purchase/action." : "educational value \u2014 teach something useful and highly saveable (tips, steps, mistakes, how-to)."}
- Produce EXACTLY ${cardCount} cards. Format each card EXACTLY like this, each on its own lines:

CARD 1 \u2014 [role, e.g. "Gancho" / "Hook"]
\u{1F5BC}\uFE0F VISUAL: [a ready-to-paste image prompt for this card's background/illustration \u2014 subject, composition, style, colors, mood, and leave clear space for the text overlay. 35\u201360 words${carLook ? `, in the ${carLook.label} visual style` : ""}.]
\u270D\uFE0F TEXTO: [the exact on-card copy \u2014 a bold short headline plus optional 1\u20132 supporting lines. Punchy, phone-readable.]

(repeat for every card, numbered CARD 2, CARD 3, \u2026 up to ${cardCount})

- ARC: Card 1 is a scroll-stopping HOOK. The middle cards deliver the story/value and keep momentum so people keep swiping. The LAST card is a clear CTA (follow, save, comment, link in bio, or buy).
- Keep a CONSISTENT visual identity across all cards: same palette, same type feel, same framing/layout logic, so the set looks cohesive.
- Keep on-card TEXT short and high-contrast \u2014 headlines a few words, never long paragraphs.
- After the cards, add one final section:
LEGENDA: [a ready-to-post Instagram caption with a hook first line, the core message, a light sprinkle of relevant hashtags, and a call to action.]
- If a Marca/Produto or P\xFAblico-alvo is provided, tailor the copy, tone and offer to them.
- If a real, identifiable person is implied, use a generic fictional persona \u2014 never name real public figures.`;
    const storyboardReqs = `OUTPUT REQUIREMENTS (this is a STORYBOARD \u2014 a sequence of ${frameCount} frames):
- ${langLine}
- Return ONLY the storyboard below. No preamble or commentary before or after.
- Produce EXACTLY ${frameCount} frames. Format each frame EXACTLY like this, each on its own lines:

QUADRO 1 \u2014 [short shot label, e.g. "Plano geral / estabelecimento"]
[A rich, self-contained image prompt for this frame \u2014 subject, appearance, wardrobe, action/expression, environment, camera framing and angle, lighting, color palette, mood, and the visual/rendering style. It must be ready to paste directly into an image generator. 45\u201380 words.]
--ar ${aspect}

(repeat for every frame, numbered QUADRO 2, QUADRO 3, \u2026 up to ${frameCount})

- CONTINUITY IS CRITICAL: the same character(s) must keep identical appearance, wardrobe and features across every frame; keep the setting, lighting and art style consistent so the frames feel like one scene. Restate the key identity details in each frame's prompt so each one stands alone when pasted separately.
- Vary the cinematography across frames (wide establishing, medium, close-up, over-the-shoulder, reaction, detail insert) for good storytelling rhythm.
- Each frame's prompt must be concrete and visual, in the chosen visual style${lookObj ? ` (${lookObj.label})` : ""}.
- If a real, identifiable person is implied, render a generic fictional likeness \u2014 never name real public figures.`;
    const styleBlock = isCarousel ? carLook ? `TARGET: An INSTAGRAM CAROUSEL with each card's visual in the ${carLook.label} style.
CAROUSEL RULES: ${STYLE_BRIEFS.carrossel}

VISUAL STYLE RULES (apply this look to every card's image):
${STYLE_BRIEFS[carLook.id]}` : `TARGET: An INSTAGRAM CAROUSEL.
CAROUSEL RULES: ${STYLE_BRIEFS.carrossel}

VISUAL STYLE: no specific art style chosen \u2014 use a clean, modern, cohesive social-media look across all cards.` : isStoryboard ? lookObj ? `TARGET: A STORYBOARD sequence rendered in the ${lookObj.label} visual style.
STORYBOARD RULES: ${STYLE_BRIEFS.storyboard}

VISUAL STYLE RULES (apply this look to every frame):
${STYLE_BRIEFS[lookObj.id]}` : `TARGET: A STORYBOARD sequence.
STORYBOARD RULES: ${STYLE_BRIEFS.storyboard}

VISUAL STYLE: no specific art style chosen \u2014 use a clean, neutral cinematic look consistent across all frames.` : chosen2 ? `TARGET STYLE: ${chosen.label} BLENDED WITH ${chosen2.label}.
PRIMARY STYLE RULES (dominant medium and execution):
${STYLE_BRIEFS[style]}

SECONDARY STYLE RULES (woven into the primary):
${STYLE_BRIEFS[secondary]}

BLENDING INSTRUCTION: The primary style defines the overall medium, rendering and execution. The secondary style contributes its subject matter, mood, palette, atmosphere or motifs as appropriate, harmonizing naturally without breaking the primary medium. Mention both influences seamlessly in the prompt.` : `TARGET STYLE: ${chosen.label}.
STYLE RULES: ${STYLE_BRIEFS[style]}`;
    const system = `You are an elite prompt engineer for AI ${isMotion ? "video" : "image"} generators${isCarousel ? " and a social-media copywriter" : ""}.
Your job: turn a short user idea into ${isCarousel ? `a production-ready INSTAGRAM CAROUSEL of ${cardCount} cards (each with an image prompt and on-card copy)` : isStoryboard ? `a production-ready STORYBOARD of ${frameCount} sequential image prompts` : isVideo ? "ONE production-ready video ad prompt" : isTimelapse ? "ONE production-ready accelerated timelapse video prompt" : "ONE extremely detailed, vivid, production-ready image prompt"}.

${langDirective}

${styleBlock}

${isCarousel ? carouselReqs : isStoryboard ? storyboardReqs : isVideo ? videoReqs : isTimelapse ? timelapseReqs : imageReqs}

${langDirective}`;
    const extras = [];
    if (brand.trim()) extras.push(`Marca/Produto: "${brand.trim()}"`);
    if (audience.trim()) extras.push(`P\xFAblico-alvo: "${audience.trim()}"`);
    if (isVideo && adScript.trim())
      extras.push(
        `Mensagem/roteiro que o usu\xE1rio QUER no an\xFAncio (use isto como base obrigat\xF3ria \u2014 incorpore essas falas, frases ou pontos-chave no roteiro, adaptando o tom para soar natural de UGC, sem inventar uma mensagem diferente): "${adScript.trim()}"`
      );
    const userMsg = `Ideia do usu\xE1rio: "${idea.trim()}"${extras.length ? "\n" + extras.join("\n") : ""}`;
    try {
      const response = await fetch("/api/forja", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ system, user: userMsg, max_tokens: 1500 })
      });
      const data = await response.json();
      if (!data.ok) throw new Error(data.error && data.error.message || "falha");
      const text = (data.text || "").trim();
      if (!text) throw new Error("empty");
      setResult(text);
    } catch (e) {
      setError("Algo deu errado ao gerar. Tente de novo em alguns segundos.");
    } finally {
      setLoading(false);
    }
  }
  function handleRevImage(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      const base64 = dataUrl.split(",")[1];
      setRevImage({ data: base64, media_type: file.type || "image/jpeg", preview: dataUrl });
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
    const focusLine = revFocus === "faithful" ? "GOAL: reverse-engineer a prompt that would RECREATE this exact image as faithfully as possible \u2014 same subject, composition, style and mood." : "GOAL: extract mainly the STYLE, technique, lighting and mood of this image (its 'recipe'), so the user can apply that same look to a DIFFERENT subject. Describe the aesthetic more than the specific subject.";
    const system = `You are an expert reverse-prompt engineer for AI image generators. You are given an image. Analyze it deeply and produce a prompt that could reproduce its look.

${focusLine}

${langLine}

Return your answer in EXACTLY this structure, using these labels:

PROMPT:
[One cohesive, flowing, comma-separated prompt block ready to paste directly into an image generator \u2014 80\u2013150 words, covering subject, style/medium, composition, lighting, color, mood and technical/render cues. End with fitting technical tags on a new line.]

AN\xC1LISE:
\u2022 Estilo/Meio: [art style or medium \u2014 photo, 3D, anime, oil painting, etc., with specifics]
\u2022 Cen\xE1rio/Local: [setting, background, environment, props]
\u2022 Composi\xE7\xE3o/Enquadramento: [framing, camera angle, shot type, rule-of-thirds, focal point]
\u2022 Personagens/Sujeito: [who/what is in frame, pose, expression, wardrobe \u2014 describe people GENERICALLY, never identify or name real individuals]
\u2022 Ilumina\xE7\xE3o: [light type, direction, quality, time of day, shadows]
\u2022 Cores/Paleta: [dominant colors, grading, contrast, saturation]
\u2022 Clima/Atmosfera: [mood, emotion, energy]
\u2022 T\xE9cnica/Render: [camera+lens if photo, or rendering engine/brush/texture cues, grain, depth of field]

RULES:
- ${langLine}
- Keep the two labels PROMPT: and AN\xC1LISE: exactly as written.
- NEVER name, identify or guess the identity of any real person; describe them by generic visual traits only.
- Be concrete and specific; infer plausible technical details (lens, lighting setup) from visual evidence.`;
    try {
      setError("A engenharia reversa por imagem precisa de um modelo de VIS\xC3O \u2014 o N\xDACLEO roda s\xF3 modelos de texto. Recurso reservado para uma vers\xE3o futura.");
    } finally {
      setLoading(false);
    }
  }
  function parseFrames(text) {
    if (!text) return [];
    const parts = text.split(/(?=QUADRO\s*\d+)/i).filter((p) => p.trim());
    return parts.map((block, i) => {
      const lines = block.trim().split("\n");
      const header = lines[0]?.trim() || `QUADRO ${i + 1}`;
      const body = lines.slice(1).join("\n").trim();
      const m = header.match(/QUADRO\s*(\d+)\s*[—\-–:]*\s*(.*)/i);
      return {
        num: m?.[1] || String(i + 1),
        label: (m?.[2] || "").trim(),
        prompt: body
      };
    });
  }
  function handleFrameImage(idx, file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setFrameImages((prev) => ({ ...prev, [idx]: e.target.result }));
    };
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
  function downloadResult(ext) {
    if (!result) return;
    try {
      const blob = new Blob([result], { type: (ext === "md" ? "text/markdown" : "text/plain") + ";charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const d = new Date(), p = (n) => String(n).padStart(2, "0");
      a.href = url;
      a.download = "prompt_" + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + "_" + p(d.getHours()) + p(d.getMinutes()) + "." + ext;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    } catch (e) {
    }
  }
  const primaryObj = STYLES.find((s) => s.id === style);
  const secondaryObj = secondary ? STYLES.find((s) => s.id === secondary) : null;
  const allowCombine = canCombineAny(style) && !primaryObj?.video;
  const storyboardActive = style === "storyboard" || secondary === "storyboard";
  const carouselActive = primaryObj?.carousel || secondaryObj?.carousel;
  return /* @__PURE__ */ React.createElement("div", { className: "min-h-screen w-full bg-[#0f0d0a] text-[#f4ede0]", style: { fontFamily: "'DM Sans', sans-serif" } }, /* @__PURE__ */ React.createElement("style", null, `
        /* offline: fontes do sistema (Google Fonts removido). Fallbacks nas fontFamily. */
        @keyframes pulseDot { 0%,100%{opacity:.25;transform:scale(.8)} 50%{opacity:1;transform:scale(1.2)} }
        @keyframes riseIn { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
        .rise { animation: riseIn .5s cubic-bezier(.2,.8,.2,1) both; }
        .grain:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.04;z-index:50;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}
      `), /* @__PURE__ */ React.createElement("div", { className: "grain" }), /* @__PURE__ */ React.createElement("div", { className: "pointer-events-none fixed inset-0 z-0" }, /* @__PURE__ */ React.createElement("div", { className: "absolute -top-32 -left-24 h-96 w-96 rounded-full blur-3xl", style: { background: "radial-gradient(circle,#ff7a18,transparent 70%)", opacity: 0.18 } }), /* @__PURE__ */ React.createElement("div", { className: "absolute bottom-0 right-0 h-96 w-96 rounded-full blur-3xl", style: { background: "radial-gradient(circle,#ffd166,transparent 70%)", opacity: 0.12 } })), /* @__PURE__ */ React.createElement("div", { className: "relative z-10 mx-auto max-w-3xl px-5 py-10 sm:py-14" }, /* @__PURE__ */ React.createElement("header", { className: "mb-9" }, /* @__PURE__ */ React.createElement("div", { className: "mb-3 inline-flex items-center gap-2 rounded-full border border-[#ff7a18]/30 bg-[#ff7a18]/10 px-3 py-1 text-xs tracking-wide", style: { fontFamily: "'DM Mono', monospace" } }, /* @__PURE__ */ React.createElement("span", { className: "h-2 w-2 rounded-full bg-[#ff7a18]", style: { animation: "pulseDot 1.6s infinite" } }), "GERADOR DE PROMPTS \xB7 IA"), /* @__PURE__ */ React.createElement("h1", { className: "text-4xl leading-[0.95] sm:text-6xl", style: { fontFamily: "'Archivo Black', sans-serif", letterSpacing: "-0.02em" } }, "FORJA DE", /* @__PURE__ */ React.createElement("br", null), /* @__PURE__ */ React.createElement("span", { className: "text-[#ff7a18]" }, "PROMPTS")), /* @__PURE__ */ React.createElement("p", { className: "mt-3 max-w-lg text-sm text-[#bdb3a3] sm:text-base" }, "Digite uma ideia simples, escolha o estilo (ou misture dois!) e receba um prompt cinematogr\xE1fico, detalhado e pronto pra colar.")), /* @__PURE__ */ React.createElement("div", { className: "mb-6 grid grid-cols-1 gap-2 rounded-2xl border border-[#2a2620] bg-[#141210] p-1.5" }, [
    ["generate", "\u2692 Gerar", "ideia \u2192 prompt"]
  ].map(([v, label, sub]) => /* @__PURE__ */ React.createElement(
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
    /* @__PURE__ */ React.createElement("div", { className: "text-sm font-bold", style: { fontFamily: "'Archivo Black', sans-serif" } }, label),
    /* @__PURE__ */ React.createElement("div", { className: `text-[10px] ${mode === v ? "text-[#1a1206]/70" : "text-[#5c554a]"}`, style: { fontFamily: "'DM Mono', monospace" } }, sub)
  ))), mode === "generate" && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Sua ideia"), /* @__PURE__ */ React.createElement(
    "textarea",
    {
      value: idea,
      onChange: (e) => setIdea(e.target.value),
      placeholder: primaryObj?.video ? "ex: an\xFAncio de um s\xE9rum facial; criadora mostrando o resultado na pele..." : primaryObj?.timelapse ? "ex: constru\xE7\xE3o de uma casa de madeira do zero num terreno vazio... / maquiagem completa do rosto limpo at\xE9 o look final... / montagem de um PC gamer na bancada..." : primaryObj?.carousel ? "ex: 5 erros que est\xE3o matando suas vendas no Instagram... / como meu produto transformou a rotina de skincare da cliente..." : "ex: uma guerreira ruiva sob a chuva numa cidade antiga...",
      rows: 3,
      className: "w-full resize-none rounded-2xl border border-[#2a2620] bg-[#161310] p-4 text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#6e675b]"
    }
  ), primaryObj?.video && /* @__PURE__ */ React.createElement("p", { className: "mt-2 rounded-xl border border-[#ffd166]/25 bg-[#ffd166]/5 px-3 py-2 text-[12px] leading-snug text-[#d8c9a3]" }, "\u{1F4A1} O roteiro j\xE1 inclui a instru\xE7\xE3o de ", /* @__PURE__ */ React.createElement("b", null, "usar a foto do produto como refer\xEAncia"), ". Anexe a imagem do produto na ferramenta de v\xEDdeo (Runway, Kling, Veo, Sora) usando o recurso de ", /* @__PURE__ */ React.createElement("i", null, "imagem de refer\xEAncia / image-to-video"), "."), primaryObj?.timelapse && /* @__PURE__ */ React.createElement("p", { className: "mt-2 rounded-xl border border-[#ffd166]/25 bg-[#ffd166]/5 px-3 py-2 text-[12px] leading-snug text-[#d8c9a3]" }, "\u23F1\uFE0F O roteiro j\xE1 detecta o ", /* @__PURE__ */ React.createElement("b", null, "tipo de projeto"), " (constru\xE7\xE3o, maquiagem, carro, PC, comida...) e monta as etapas certas da transforma\xE7\xE3o, com ", /* @__PURE__ */ React.createElement("b", null, "c\xE2mera travada"), " e enquadramento id\xEAntico do in\xEDcio ao fim."), (primaryObj?.video || carouselActive) && /* @__PURE__ */ React.createElement("div", { className: "mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Marca / Produto ", /* @__PURE__ */ React.createElement("span", { className: "text-[#5c554a] normal-case" }, "(opcional)")), /* @__PURE__ */ React.createElement(
    "input",
    {
      value: brand,
      onChange: (e) => setBrand(e.target.value),
      placeholder: "ex: Loja Aurora \u2014 jaqueta corta-vento",
      className: "w-full rounded-xl border border-[#2a2620] bg-[#161310] px-3 py-2.5 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#6e675b]"
    }
  )), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "P\xFAblico-alvo ", /* @__PURE__ */ React.createElement("span", { className: "text-[#5c554a] normal-case" }, "(opcional)")), /* @__PURE__ */ React.createElement(
    "input",
    {
      value: audience,
      onChange: (e) => setAudience(e.target.value),
      placeholder: "ex: mulheres 25-40 que treinam ao ar livre",
      className: "w-full rounded-xl border border-[#2a2620] bg-[#161310] px-3 py-2.5 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#6e675b]"
    }
  ))), primaryObj?.video && /* @__PURE__ */ React.createElement("div", { className: "mt-3" }, /* @__PURE__ */ React.createElement("label", { className: "mb-1.5 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Texto / Mensagem do an\xFAncio ", /* @__PURE__ */ React.createElement("span", { className: "text-[#5c554a] normal-case" }, "(opcional)")), /* @__PURE__ */ React.createElement(
    "textarea",
    {
      value: adScript,
      onChange: (e) => setAdScript(e.target.value),
      placeholder: "ex: Fale sobre o desconto de 30% s\xF3 essa semana; mencione que tem frete gr\xE1tis; termine com 'corre que acaba r\xE1pido!'",
      rows: 3,
      className: "w-full resize-none rounded-xl border border-[#2a2620] bg-[#161310] p-3 text-sm text-[#f4ede0] outline-none transition focus:border-[#ff7a18]/60 placeholder:text-[#6e675b]"
    }
  ), /* @__PURE__ */ React.createElement("p", { className: "mt-1.5 text-[11px] leading-snug text-[#6e675b]", style: { fontFamily: "'DM Mono', monospace" } }, "Deixe vazio pra IA criar o roteiro do zero, ou escreva as falas/pontos que devem aparecer.")), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-7 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Estilo principal"), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-2.5 sm:grid-cols-3" }, STYLES.map((s) => {
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
        className: `group relative rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 shadow-[0_0_20px_rgba(255,122,24,0.25)] -translate-y-0.5" : "border-[#2a2620] bg-[#141210] hover:border-[#4a4338]"}`
      },
      active && /* @__PURE__ */ React.createElement("span", { className: "absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ff7a18] text-[11px] font-black text-[#1a1206]" }, "\u2713"),
      /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-lg" }, s.tag), /* @__PURE__ */ React.createElement("span", { className: `text-sm font-bold ${active ? "text-[#ffd166]" : ""}` }, s.label)),
      /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#d8c9a3]" : "text-[#8c8475]"}` }, s.hint)
    );
  })), allowCombine && /* @__PURE__ */ React.createElement("div", { className: "mt-5" }, /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: () => {
        if (combineOpen) {
          setCombineOpen(false);
          setSecondary(null);
        } else {
          setCombineOpen(true);
        }
      },
      className: `flex w-full items-center justify-center gap-2 rounded-2xl border-2 px-4 py-3 text-sm font-bold transition ${combineOpen || secondary ? "border-[#ffd166] bg-[#ffd166]/10 text-[#ffd166]" : "border-dashed border-[#4a4338] bg-transparent text-[#bdb3a3] hover:border-[#ff7a18]/60 hover:text-[#ffd166]"}`,
      style: { fontFamily: "'DM Mono', monospace" }
    },
    combineOpen || secondary ? "\u2715 Remover combina\xE7\xE3o" : "+ Combinar com outro estilo"
  ), combineOpen && /* @__PURE__ */ React.createElement("div", { className: "rise mt-4" }, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Segundo estilo (mistura)"), /* @__PURE__ */ React.createElement("p", { className: "mb-3 text-[11px] text-[#6e675b]", style: { fontFamily: "'DM Mono', monospace" } }, "Op\xE7\xF5es esmaecidas s\xE3o incompat\xEDveis com ", /* @__PURE__ */ React.createElement("span", { className: "text-[#ffd166]" }, primaryObj?.label), "."), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-2.5 sm:grid-cols-3" }, STYLES.map((s) => {
    if (s.id === style) return null;
    const compatible = canCombine(style, s.id);
    const active = s.id === secondary;
    return /* @__PURE__ */ React.createElement(
      "button",
      {
        key: s.id,
        disabled: !compatible,
        onClick: () => setSecondary(s.id),
        title: compatible ? "" : `Incompat\xEDvel com ${primaryObj?.label}`,
        className: `group relative rounded-2xl border-2 p-3 text-left transition ${!compatible ? "cursor-not-allowed border-[#1f1c17] bg-[#0f0d0a] opacity-30" : active ? "border-[#ffd166] bg-[#ffd166]/15 ring-2 ring-[#ffd166]/40 shadow-[0_0_20px_rgba(255,209,102,0.2)] -translate-y-0.5" : "border-[#2a2620] bg-[#141210] hover:border-[#4a4338]"}`
      },
      active && /* @__PURE__ */ React.createElement("span", { className: "absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[#ffd166] text-[11px] font-black text-[#1a1206]" }, "\u2713"),
      /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-lg" }, s.tag), /* @__PURE__ */ React.createElement("span", { className: `text-sm font-bold ${active ? "text-[#ffd166]" : ""}` }, s.label)),
      /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#d8c9a3]" : "text-[#8c8475]"}` }, s.hint)
    );
  })), secondaryObj && /* @__PURE__ */ React.createElement("div", { className: "rise mt-4 rounded-xl border border-[#ff7a18]/30 bg-gradient-to-r from-[#ff7a18]/10 to-[#ffd166]/10 px-4 py-3 text-sm" }, /* @__PURE__ */ React.createElement("span", { className: "text-[#8c8475]" }, "Misturando:"), " ", /* @__PURE__ */ React.createElement("span", { className: "font-bold text-[#ff7a18]" }, primaryObj?.tag, " ", primaryObj?.label), /* @__PURE__ */ React.createElement("span", { className: "mx-2 text-[#ffd166]" }, "+"), /* @__PURE__ */ React.createElement("span", { className: "font-bold text-[#ffd166]" }, secondaryObj.tag, " ", secondaryObj.label)))), storyboardActive && /* @__PURE__ */ React.createElement("div", { className: "rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4" }, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#ffd166]", style: { fontFamily: "'DM Mono', monospace" } }, "\u{1F3AC} Quantos quadros?"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, [3, 4, 5, 6, 7, 8].map((n) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: n,
      onClick: () => setFrameCount(n),
      className: `rounded-lg border-2 px-3.5 py-1.5 text-xs font-bold transition ${n === frameCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ffd166] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`,
      style: { fontFamily: "'DM Mono', monospace" }
    },
    n
  ))), /* @__PURE__ */ React.createElement("p", { className: "mt-2.5 text-[11px] leading-snug text-[#bdb3a3]" }, "O storyboard gera ", /* @__PURE__ */ React.createElement("b", { className: "text-[#ffd166]" }, frameCount, " prompts"), " em sequ\xEAncia, com continuidade de personagem e cen\xE1rio. ", secondaryObj ? "" : "\u{1F4A1} Combine com um estilo visual (Cinematogr\xE1fico, Anime, etc.) pra definir o look dos quadros.")), carouselActive && /* @__PURE__ */ React.createElement("div", { className: "rise mt-5 rounded-2xl border-2 border-[#ff7a18]/40 bg-[#ff7a18]/5 p-4" }, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#ffd166]", style: { fontFamily: "'DM Mono', monospace" } }, "\u{1F3A0} Objetivo do carrossel"), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 gap-2.5 sm:grid-cols-2" }, [
    ["sell", "\u{1F6CD}\uFE0F Storytelling / Venda", "Cria desejo e leva \xE0 a\xE7\xE3o"],
    ["educate", "\u{1F4A1} Educativo / Dicas", "Ensina algo salv\xE1vel"]
  ].map(([v, label, sub]) => {
    const active = carouselGoal === v;
    return /* @__PURE__ */ React.createElement(
      "button",
      {
        key: v,
        onClick: () => setCarouselGoal(v),
        className: `rounded-xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40" : "border-[#2a2620] bg-[#141210] hover:border-[#4a4338]"}`
      },
      /* @__PURE__ */ React.createElement("div", { className: `text-sm font-bold ${active ? "text-[#ffd166]" : ""}` }, label),
      /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#d8c9a3]" : "text-[#8c8475]"}` }, sub)
    );
  })), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-5 block text-xs uppercase tracking-widest text-[#ffd166]", style: { fontFamily: "'DM Mono', monospace" } }, "Quantos cards?"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, [3, 4, 5, 6, 7, 8, 9, 10].map((n) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: n,
      onClick: () => setCardCount(n),
      className: `rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${n === cardCount ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ffd166] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`,
      style: { fontFamily: "'DM Mono', monospace" }
    },
    n
  ))), /* @__PURE__ */ React.createElement("p", { className: "mt-2.5 text-[11px] leading-snug text-[#bdb3a3]" }, "Gera ", /* @__PURE__ */ React.createElement("b", { className: "text-[#ffd166]" }, cardCount, " cards"), " (visual + copy) do gancho ao CTA, mais uma legenda pronta pra postar. ", secondaryObj ? "" : "\u{1F4A1} Combine com um estilo visual pra definir o look dos cards.")), /* @__PURE__ */ React.createElement("div", { className: "mt-7 flex flex-wrap items-end gap-6" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Propor\xE7\xE3o"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1.5" }, ASPECTS.map((a) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: a,
      onClick: () => setAspect(a),
      className: `rounded-lg border-2 px-2.5 py-1.5 text-xs font-bold transition ${a === aspect ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ffd166] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`,
      style: { fontFamily: "'DM Mono', monospace" }
    },
    a
  )))), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Idioma do prompt"), /* @__PURE__ */ React.createElement("div", { className: "flex gap-1.5" }, [
    ["en", "Ingl\xEAs"],
    ["pt", "Portugu\xEAs"]
  ].map(([v, l]) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: v,
      onClick: () => setOutLang(v),
      className: `rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ffd166] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`,
      style: { fontFamily: "'DM Mono', monospace" }
    },
    l
  ))))), /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: generate,
      disabled: loading,
      className: "mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60",
      style: { fontFamily: "'Archivo Black', sans-serif", letterSpacing: "0.01em" }
    },
    loading ? /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("span", { className: "h-2 w-2 rounded-full bg-[#1a1206]", style: { animation: "pulseDot 1s infinite" } }), "FORJANDO...") : /* @__PURE__ */ React.createElement(React.Fragment, null, "\u2692 GERAR PROMPT")
  ), error && /* @__PURE__ */ React.createElement("p", { className: "mt-3 text-center text-sm text-[#ff9a6a]" }, error)), mode === "reverse" && /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "mb-2 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Imagem de refer\xEAncia"), /* @__PURE__ */ React.createElement("label", { className: "relative block cursor-pointer" }, /* @__PURE__ */ React.createElement(
    "div",
    {
      className: "flex min-h-[180px] items-center justify-center rounded-2xl border-2 border-dashed border-[#4a4338] bg-[#141210] bg-contain bg-center bg-no-repeat p-4 transition hover:border-[#ff7a18]/60",
      style: revImage ? { backgroundImage: `url(${revImage.preview})`, minHeight: "280px" } : {}
    },
    !revImage && /* @__PURE__ */ React.createElement("div", { className: "text-center" }, /* @__PURE__ */ React.createElement("div", { className: "text-4xl" }, "\u{1F5BC}\uFE0F"), /* @__PURE__ */ React.createElement("div", { className: "mt-2 text-sm font-bold text-[#bdb3a3]" }, "Clique pra enviar uma imagem"), /* @__PURE__ */ React.createElement("div", { className: "mt-1 text-[11px] text-[#6e675b]", style: { fontFamily: "'DM Mono', monospace" } }, "PNG, JPG ou WEBP"))
  ), /* @__PURE__ */ React.createElement(
    "input",
    {
      type: "file",
      accept: "image/*",
      className: "hidden",
      onChange: (e) => handleRevImage(e.target.files?.[0])
    }
  )), revImage && /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: () => setRevImage(null),
      className: "mt-2 text-[11px] text-[#8c8475] underline transition hover:text-[#ff9a6a]",
      style: { fontFamily: "'DM Mono', monospace" }
    },
    "remover imagem"
  ), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Foco da an\xE1lise"), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 gap-2.5 sm:grid-cols-2" }, [
    ["faithful", "\u{1F3AF} Recriar fiel", "Reproduz a imagem o mais parecido poss\xEDvel"],
    ["style", "\u{1F3A8} Capturar estilo", "Extrai s\xF3 o 'look' pra usar em outra ideia"]
  ].map(([v, label, sub]) => {
    const active = revFocus === v;
    return /* @__PURE__ */ React.createElement(
      "button",
      {
        key: v,
        onClick: () => setRevFocus(v),
        className: `rounded-2xl border-2 p-3 text-left transition ${active ? "border-[#ff7a18] bg-[#ff7a18]/20 ring-2 ring-[#ff7a18]/40 -translate-y-0.5" : "border-[#2a2620] bg-[#141210] hover:border-[#4a4338]"}`
      },
      /* @__PURE__ */ React.createElement("div", { className: `text-sm font-bold ${active ? "text-[#ffd166]" : ""}` }, label),
      /* @__PURE__ */ React.createElement("p", { className: `mt-1 text-[11px] leading-snug ${active ? "text-[#d8c9a3]" : "text-[#8c8475]"}` }, sub)
    );
  })), /* @__PURE__ */ React.createElement("label", { className: "mb-2 mt-6 block text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "Idioma do resultado"), /* @__PURE__ */ React.createElement("div", { className: "flex gap-1.5" }, [
    ["en", "Ingl\xEAs"],
    ["pt", "Portugu\xEAs"]
  ].map(([v, l]) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: v,
      onClick: () => setOutLang(v),
      className: `rounded-lg border-2 px-3 py-1.5 text-xs font-bold transition ${v === outLang ? "border-[#ff7a18] bg-[#ff7a18]/25 text-[#ffd166] ring-2 ring-[#ff7a18]/30" : "border-[#2a2620] text-[#8c8475] hover:border-[#4a4338]"}`,
      style: { fontFamily: "'DM Mono', monospace" }
    },
    l
  ))), /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: reverseEngineer,
      disabled: loading,
      className: "mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#ff7a18] py-4 text-base font-bold text-[#1a1206] transition hover:bg-[#ff8c3a] disabled:opacity-60",
      style: { fontFamily: "'Archivo Black', sans-serif", letterSpacing: "0.01em" }
    },
    loading ? /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("span", { className: "h-2 w-2 rounded-full bg-[#1a1206]", style: { animation: "pulseDot 1s infinite" } }), "ANALISANDO...") : /* @__PURE__ */ React.createElement(React.Fragment, null, "\u{1F50D} EXTRAIR PROMPT")
  ), error && /* @__PURE__ */ React.createElement("p", { className: "mt-3 text-center text-sm text-[#ff9a6a]" }, error)), result && /* @__PURE__ */ React.createElement("div", { ref: outRef, className: "rise mt-9 rounded-2xl border border-[#2a2620] bg-[#161310] p-5" }, /* @__PURE__ */ React.createElement("div", { className: "mb-3 flex items-center justify-between" }, /* @__PURE__ */ React.createElement("span", { className: "text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, mode === "reverse" ? "Prompt extra\xEDdo da imagem" : primaryObj?.video ? "Roteiro do an\xFAncio" : primaryObj?.timelapse ? "Roteiro do timelapse" : carouselActive ? `Carrossel \xB7 ${cardCount} cards` : storyboardActive ? `Storyboard \xB7 ${frameCount} quadros` : "Prompt gerado"), /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, mode === "generate" && storyboardActive && /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: () => setShowPage((v) => !v),
      className: "rounded-lg border border-[#ffd166]/40 bg-[#ffd166]/10 px-3 py-1.5 text-xs font-bold text-[#ffd166] transition hover:bg-[#ffd166]/20"
    },
    showPage ? "\u2715 Fechar p\xE1gina" : "\u{1F4D6} Montar p\xE1gina"
  ), /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: () => downloadResult("md"),
      className: "rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#ffd166] transition hover:bg-[#ff7a18]/20"
    },
    "\u2b07 .md"
  ), /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: () => downloadResult("txt"),
      className: "rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#ffd166] transition hover:bg-[#ff7a18]/20"
    },
    "\u2b07 .txt"
  ), /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: copyResult,
      className: "rounded-lg border border-[#ff7a18]/40 bg-[#ff7a18]/10 px-3 py-1.5 text-xs font-bold text-[#ffd166] transition hover:bg-[#ff7a18]/20"
    },
    copied ? "\u2713 Copiado!" : "Copiar"
  ))), /* @__PURE__ */ React.createElement("p", { className: "whitespace-pre-wrap text-[15px] leading-relaxed text-[#e9e0d2]", style: { fontFamily: "'DM Mono', monospace" } }, result)), result && storyboardActive && showPage && mode === "generate" && /* @__PURE__ */ React.createElement("div", { className: "rise mt-6" }, /* @__PURE__ */ React.createElement("div", { className: "mb-3 flex items-center justify-between" }, /* @__PURE__ */ React.createElement("span", { className: "text-xs uppercase tracking-widest text-[#8c8475]", style: { fontFamily: "'DM Mono', monospace" } }, "\u{1F4D6} Prancha \xB7 clique num quadro pra adicionar a imagem")), /* @__PURE__ */ React.createElement("div", { className: "rounded-2xl bg-[#e8e2d5] p-3 sm:p-4 shadow-2xl" }, /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 gap-3 sm:grid-cols-2" }, parseFrames(result).map((f, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: "overflow-hidden rounded-sm border-[3px] border-[#111] bg-white" }, /* @__PURE__ */ React.createElement("label", { className: "relative block cursor-pointer" }, /* @__PURE__ */ React.createElement(
    "div",
    {
      className: "flex aspect-video items-center justify-center border-b-[3px] border-[#111] bg-[#d9d3c6] bg-cover bg-center",
      style: frameImages[i] ? { backgroundImage: `url(${frameImages[i]})` } : {}
    },
    !frameImages[i] && /* @__PURE__ */ React.createElement("div", { className: "text-center" }, /* @__PURE__ */ React.createElement("div", { className: "text-2xl" }, "\u{1F5BC}\uFE0F"), /* @__PURE__ */ React.createElement("div", { className: "mt-1 text-[11px] font-bold text-[#6b6455]", style: { fontFamily: "'DM Mono', monospace" } }, "clique pra colar a imagem")),
    /* @__PURE__ */ React.createElement("span", { className: "absolute left-0 top-0 bg-[#111] px-2 py-0.5 text-xs font-black text-[#ffd166]", style: { fontFamily: "'Archivo Black', sans-serif" } }, f.num)
  ), /* @__PURE__ */ React.createElement(
    "input",
    {
      type: "file",
      accept: "image/*",
      className: "hidden",
      onChange: (e) => handleFrameImage(i, e.target.files?.[0])
    }
  )), /* @__PURE__ */ React.createElement("div", { className: "p-2.5" }, f.label && /* @__PURE__ */ React.createElement("div", { className: "mb-1 text-[11px] font-black uppercase tracking-wide text-[#111]", style: { fontFamily: "'Archivo Black', sans-serif" } }, f.label), /* @__PURE__ */ React.createElement("p", { className: "text-[11px] leading-snug text-[#333]", style: { fontFamily: "'DM Mono', monospace" } }, f.prompt)))))), /* @__PURE__ */ React.createElement("p", { className: "mt-2.5 text-center text-[11px] text-[#6e675b]", style: { fontFamily: "'DM Mono', monospace" } }, "\u{1F4A1} Gere cada imagem no seu app favorito usando os prompts, depois clique nos quadros pra montar sua HQ. Use o print da tela pra salvar a prancha pronta.")), /* @__PURE__ */ React.createElement("footer", { className: "mt-12 text-center text-[11px] text-[#5c554a]", style: { fontFamily: "'DM Mono', monospace" } }, "feito com IA \xB7 cole o resultado no seu gerador de imagens favorito")));
}
window.__mountForja = function() {
  var el = document.getElementById("forja-root");
  if (!el || el.__mounted) return;
  el.__mounted = true;
  ReactDOM.createRoot(el).render(React.createElement(App));
};
