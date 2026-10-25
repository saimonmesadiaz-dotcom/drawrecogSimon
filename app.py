import base64
import io
import random

import numpy as np
import openai  # noqa: F401  (se mantiene por compatibilidad con tu entorno)
import streamlit as st
from openai import OpenAI
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# =========================================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================================
st.set_page_config(
    page_title="Tablero Inteligente | Racing Edition",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "canvas_v" not in st.session_state:
    st.session_state.canvas_v = 0
if "mi_respuesta" not in st.session_state:
    st.session_state.mi_respuesta = ""


def flat(html: str) -> str:
    """Aplana el HTML en una sola línea (evita que Markdown lo interprete como código)."""
    return "".join(line.strip() for line in html.splitlines())


# =========================================================================
# CSS: crema + amarillo cromo + café + asfalto y rojo de carrera
# =========================================================================
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Racing+Sans+One&display=swap');

:root {
  --cafe: #3B2108;
  --crema: #F7F4EA;
  --amarillo: #E9C46A;
  --boton: #F0B03C;
  --hover: #F7C867;
  --asfalto: #2B2926;
  --rojo: #D62828;
  --tinta: #1F1308;
  --vino: #6B1E2E;
  --vino-oscuro: #4A1420;
}

.stApp { background: var(--crema); color: var(--tinta); font-family: 'Fredoka', 'Trebuchet MS', sans-serif; }
[data-testid="stHeader"] { background: transparent; }

/* Espacio abajo para que el carro no tape el contenido */
.block-container, [data-testid="stMainBlockContainer"] {
  position: relative; z-index: 0;
  padding-top: 2rem !important;
  padding-bottom: 200px !important;
}

/* ---------------- BARRA LATERAL (vino tinto, textos blancos) ---------------- */
[data-testid="stSidebar"][aria-expanded="true"] { width: 320px !important; min-width: 320px !important; }
[data-testid="stSidebar"] { background: var(--vino) !important; border-right: 3px solid var(--tinta); }
[data-testid="stSidebar"] > div:first-child { padding-bottom: 180px; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label { color: #FFFFFF !important; font-family: 'Fredoka', sans-serif; font-weight: 500; }
[data-testid="stSidebar"] [data-testid="stSliderTickBarMin"],
[data-testid="stSidebar"] [data-testid="stSliderTickBarMax"],
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"] { color: #FFFFFF !important; }

.side-card {
  background: rgba(255,255,255,.10); border: 2px solid var(--boton); border-radius: 14px;
  padding: 14px 16px; box-shadow: 3px 3px 0 var(--tinta); margin-bottom: 18px;
}
.side-card h3 { margin: 0 0 6px 0; font-family: 'Racing Sans One', cursive; font-size: 1.5rem; color: #FFE7A8; letter-spacing: 1px; }
.side-card p { margin: 0; color: #FFFFFF !important; font-weight: 400; line-height: 1.4; }
.side-title { font-family: 'Racing Sans One', cursive; font-size: 1.25rem; color: #FFFFFF; margin: 6px 0 4px; letter-spacing: 1px; }

/* ---------------- BOTONES ---------------- */
.stButton button {
  background: var(--boton) !important; border: 3px solid var(--tinta) !important; border-radius: 14px !important;
  box-shadow: 4px 4px 0 var(--tinta) !important; transition: all .1s ease !important; padding: .55rem 1rem !important;
}
.stButton button p {
  color: var(--cafe) !important; font-family: 'Racing Sans One', cursive !important;
  font-size: 1.3rem !important; letter-spacing: 1px; font-weight: 400 !important;
}
.stButton button:hover { background: var(--hover) !important; transform: translate(-2px,-2px); box-shadow: 6px 6px 0 var(--tinta) !important; }
.stButton button:active { transform: translate(2px,2px); box-shadow: 1px 1px 0 var(--tinta) !important; }
[data-testid="stSidebar"] .stButton button p { font-size: 1.15rem !important; }
.st-key-key_card .stButton button { animation: turbo 1.8s ease-in-out infinite; }
@keyframes turbo {
  0%, 100% { box-shadow: 4px 4px 0 var(--tinta), 0 0 0 0 rgba(214,40,40,.0); }
  50%      { box-shadow: 4px 4px 0 var(--tinta), 0 0 18px 4px rgba(240,176,60,.75); }
}

/* Inputs */
[data-testid="stTextInput"] input {
  background: #FFFDF7 !important; border: 2px solid var(--tinta) !important; border-radius: 10px !important;
  color: var(--tinta) !important; font-family: 'Fredoka', sans-serif;
}
[data-testid="stTextInput"] label p { color: #FFFFFF !important; font-weight: 500; }

/* ---------------- PORTADA (delgada y sin animación) ---------------- */
.race-hero {
  position: relative; overflow: hidden; text-align: center;
  background: var(--asfalto); border: 3px solid var(--tinta); border-radius: 12px;
  padding: 18px 20px 12px; margin-bottom: 14px; box-shadow: 4px 4px 0 var(--amarillo);
}
.race-hero .checker {
  position: absolute; left: 0; right: 0; top: 0; height: 6px;
  background: conic-gradient(#fff 25%, #111 0 50%, #fff 0 75%, #111 0) 0 0 / 12px 12px;
}
.race-hero h1 {
  margin: 0; display: inline-block; transform: skewX(-6deg);
  font-family: 'Racing Sans One', cursive; font-weight: 400;
  font-size: 2.1rem; line-height: 1.2; letter-spacing: 2px; text-transform: uppercase;
  background: linear-gradient(90deg, #FFF6E0, #F0B03C, #FFF6E0);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent;
}
.race-hero .sub { margin: 0; color: #FFF8E1; font-size: .95rem; font-weight: 500; }

/* ---------------- TÍTULOS DE SECCIÓN ---------------- */
.sec-title {
  text-align: center; margin: 14px 0 2px; font-family: 'Racing Sans One', cursive;
  font-size: 1.6rem; letter-spacing: 1.5px; color: var(--cafe);
}
.sec-sub { text-align: center; margin: 0 0 12px; color: #6E5A44; font-size: 1.05rem; font-weight: 500; }

/* ---------------- TABLERO (centrado) ---------------- */
.st-key-canvas_card {
  background: #FFFDF7; border: 4px solid var(--tinta); border-radius: 16px; padding: 16px;
  box-shadow: 8px 8px 0 var(--tinta);
  width: fit-content !important; max-width: 100%; margin-left: auto; margin-right: auto; align-items: center;
}
.st-key-canvas_card::before {
  content: ""; display: block; width: 100%; height: 14px; border-radius: 6px; margin-bottom: 6px;
  background: conic-gradient(#fff 25%, #111 0 50%, #fff 0 75%, #111 0) 0 0 / 28px 28px; border: 2px solid var(--tinta);
}
.stMain iframe { display: block; max-width: 100%; }

/* ---------------- TARJETAS DE ANÁLISIS (vino tinto, textos blancos) ---------------- */
.st-key-key_card, .st-key-result_card {
  background: var(--vino); border: 3px solid var(--tinta); border-radius: 16px; padding: 18px 20px;
  box-shadow: 6px 6px 0 var(--tinta); width: 100%; max-width: 898px; margin: 16px auto 0 auto;
}
.st-key-result_card { background: var(--vino-oscuro); border-left: 12px solid var(--boton); }
.st-key-result_card p, .st-key-result_card li, .st-key-result_card span { color: #FFFFFF !important; font-size: 1.08rem; line-height: 1.55; }
.card-h { font-family: 'Racing Sans One', cursive; font-size: 1.5rem; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 6px; }

/* ---------------- FONDO: LÍNEAS DE VELOCIDAD ---------------- */
.bg-layer {
  position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden;
}
.spd {
  position: absolute; left: 0; height: 3px; border-radius: 3px;
  background: linear-gradient(90deg, transparent, rgba(59,33,8,.45), transparent);
  animation: spdmove linear infinite;
}
@keyframes spdmove { from { transform: translateX(110vw); } to { transform: translateX(-520px); } }

/* ---------------- CARRO DE CARRERAS (abajo de toda la interfaz) ---------------- */
.race-bar { position: fixed; left: 0; right: 0; bottom: 0; height: 130px; z-index: 99999; pointer-events: none; overflow: hidden; }
.race-bar .road { position: absolute; left: 0; right: 0; bottom: 0; height: 50px; background: var(--asfalto); border-top: 4px solid var(--tinta); }
.race-bar .road::before {
  content: ""; position: absolute; left: 0; right: 0; top: calc(50% - 3px); height: 6px;
  background: repeating-linear-gradient(90deg, #F0B03C 0 44px, transparent 44px 96px); background-size: 96px 6px;
  animation: roadmove .28s linear infinite;
}
@keyframes roadmove { to { background-position: -96px 0; } }
.race-bar .kerb {
  position: absolute; left: 0; right: 0; bottom: 50px; height: 10px;
  background: repeating-linear-gradient(90deg, #D62828 0 32px, #FFF 32px 64px); background-size: 64px 10px;
  border-top: 2px solid var(--tinta); animation: kerbmove .24s linear infinite;
}
@keyframes kerbmove { to { background-position: -64px 0; } }

.runner { position: absolute; bottom: 14px; left: 0; width: 340px; animation: drive 18s cubic-bezier(.45,.05,.55,.95) infinite; }
@keyframes drive { 0% { transform: translateX(-400px); } 100% { transform: translateX(calc(100vw + 80px)); } }
.runner svg { display: block; animation: bob .22s ease-in-out infinite alternate; overflow: visible; }
@keyframes bob { from { transform: translateY(0); } to { transform: translateY(-2px); } }

.streaks i {
  position: absolute; left: -260px; width: 260px; height: 3px; border-radius: 3px;
  background: linear-gradient(90deg, transparent, rgba(240,176,60,.95));
  transform-origin: right center; animation: streak .35s linear infinite;
}
.streaks i:nth-child(1) { top: 26px; animation-delay: 0s; }
.streaks i:nth-child(2) { top: 40px; animation-delay: -.12s; width: 200px; left: -200px; }
.streaks i:nth-child(3) { top: 54px; animation-delay: -.22s; }
.streaks i:nth-child(4) { top: 66px; animation-delay: -.05s; width: 160px; left: -160px; }
@keyframes streak { 0% { transform: scaleX(.4); opacity: .2; } 50% { transform: scaleX(1); opacity: 1; } 100% { transform: scaleX(.6); opacity: .1; } }

.wheel { transform-box: fill-box; transform-origin: center; animation: spin .22s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.flame { transform-box: fill-box; transform-origin: 100% 50%; animation: flick .09s ease-in-out infinite alternate; }
.flame.f2 { animation-duration: .07s; animation-delay: -.03s; }
.flame.f3 { animation-duration: .05s; }
@keyframes flick { from { transform: scale(.76, .88); } to { transform: scale(1.14, 1.1); } }
.spark { animation: spark .5s linear infinite; }
.spark.s2 { animation-delay: -.17s; }
.spark.s3 { animation-delay: -.33s; }
@keyframes spark { 0% { transform: translateX(0); opacity: 1; } 100% { transform: translateX(-55px); opacity: 0; } }
"""

st.markdown("<style>" + "\n".join(l for l in CSS.splitlines() if l.strip()) + "</style>", unsafe_allow_html=True)

# =========================================================================
# FONDO: líneas de velocidad (sin stickers)
# =========================================================================
def fondo_carreras():
    """Solo líneas de velocidad suaves (sin stickers, para no saturar)."""
    rnd = random.Random(11)
    piezas = []
    for _ in range(12):
        piezas.append(
            f'<i class="spd" style="top:{rnd.uniform(2, 78):.1f}vh;width:{rnd.randint(140, 420)}px;'
            f'animation-duration:{rnd.uniform(1.6, 3.4):.2f}s;animation-delay:-{rnd.uniform(0, 3):.2f}s;'
            f'opacity:{rnd.uniform(.2, .4):.2f}"></i>'
        )
    return '<div class="bg-layer">' + "".join(piezas) + "</div>"


st.markdown(fondo_carreras(), unsafe_allow_html=True)

# =========================================================================
# CARRO DE CARRERAS ANIMADO (SVG) con llamas, chispas y líneas de velocidad
# =========================================================================
CAR_SVG = flat(
    """
<svg viewBox="-90 0 380 90" width="340" height="81" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gBody" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FF5A5A"/><stop offset=".55" stop-color="#D62828"/><stop offset="1" stop-color="#8F0F1A"/>
    </linearGradient>
    <linearGradient id="gFlame1" x1="1" y1="0" x2="0" y2="0">
      <stop offset="0" stop-color="#FFC107"/><stop offset=".45" stop-color="#FF5A00"/><stop offset="1" stop-color="#E52E00" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="gFlame2" x1="1" y1="0" x2="0" y2="0">
      <stop offset="0" stop-color="#FFF3B0"/><stop offset=".5" stop-color="#FFC107"/><stop offset="1" stop-color="#FF8A00" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="gBeam" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#FFF3B0" stop-opacity=".75"/><stop offset="1" stop-color="#FFF3B0" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="gRim"><stop offset="0" stop-color="#FAFAFA"/><stop offset="1" stop-color="#8E8E8E"/></radialGradient>
  </defs>

  <ellipse cx="112" cy="77" rx="112" ry="4" fill="rgba(0,0,0,.35)"/>

  <!-- Llamas traseras -->
  <g>
    <path class="flame f1" d="M10 47 Q-18 36 -48 49 Q-78 53 -90 53 Q-78 56 -48 59 Q-18 70 10 59 Z" fill="url(#gFlame1)"/>
    <path class="flame f2" d="M10 49 Q-10 43 -32 51 Q-52 53 -60 53 Q-52 54 -32 56 Q-10 63 10 57 Z" fill="url(#gFlame2)"/>
    <path class="flame f3" d="M10 51 Q-2 49 -16 53 Q-2 57 10 55 Z" fill="#FFFFFF"/>
    <circle class="spark" cx="-20" cy="48" r="2.4" fill="#FFD54A"/>
    <circle class="spark s2" cx="-30" cy="58" r="2" fill="#FF9A1F"/>
    <circle class="spark s3" cx="-14" cy="53" r="1.8" fill="#FFF3B0"/>
  </g>

  <!-- Faros -->
  <polygon points="212,45 285,30 285,64 212,50" fill="url(#gBeam)"/>

  <!-- Alerón y escape -->
  <rect x="5" y="50" width="9" height="6" rx="2" fill="#8a8a8a"/>
  <polygon points="4,28 40,28 40,33 31,33 29,43 24,43 22,33 4,33" fill="#1F1308"/>

  <!-- Carrocería -->
  <path d="M12 54 C12 46 20 42 34 40 L62 36 C78 22 98 16 124 16 C146 16 160 24 170 34 L196 38 C208 40 214 46 214 54 L214 58 L12 58 Z" fill="url(#gBody)" stroke="#1F1308" stroke-width="2"/>
  <path d="M80 35 C90 25 104 21 120 21 C136 21 146 27 152 35 Z" fill="#BFE9FF" stroke="#1F1308" stroke-width="1.5"/>
  <line x1="117" y1="21" x2="117" y2="35" stroke="#1F1308" stroke-width="1.5"/>
  <path d="M66 37 C82 24 100 19 124 19" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="2" fill="none"/>
  <line x1="22" y1="52" x2="208" y2="52" stroke="#F0B03C" stroke-width="3.5"/>
  <circle cx="102" cy="44" r="6.5" fill="#fff" stroke="#1F1308" stroke-width="1"/>
  <text x="102" y="48" font-size="10" font-weight="800" text-anchor="middle" fill="#1F1308" font-family="Arial Black, Arial, sans-serif">7</text>
  <ellipse cx="209" cy="47" rx="5" ry="3" fill="#FFE066"/>

  <!-- Ruedas -->
  <g transform="translate(50 58)">
    <circle r="17" fill="#0d0d0d"/><circle r="15" fill="#1b1b1b" stroke="#000" stroke-width="2"/>
    <g class="wheel">
      <circle r="9" fill="url(#gRim)"/>
      <line x1="-9" y1="0" x2="9" y2="0" stroke="#555" stroke-width="2"/>
      <line x1="-4.5" y1="-7.8" x2="4.5" y2="7.8" stroke="#555" stroke-width="2"/>
      <line x1="4.5" y1="-7.8" x2="-4.5" y2="7.8" stroke="#555" stroke-width="2"/>
      <circle r="2.5" fill="#333"/>
    </g>
  </g>
  <g transform="translate(170 58)">
    <circle r="17" fill="#0d0d0d"/><circle r="15" fill="#1b1b1b" stroke="#000" stroke-width="2"/>
    <g class="wheel">
      <circle r="9" fill="url(#gRim)"/>
      <line x1="-9" y1="0" x2="9" y2="0" stroke="#555" stroke-width="2"/>
      <line x1="-4.5" y1="-7.8" x2="4.5" y2="7.8" stroke="#555" stroke-width="2"/>
      <line x1="4.5" y1="-7.8" x2="-4.5" y2="7.8" stroke="#555" stroke-width="2"/>
      <circle r="2.5" fill="#333"/>
    </g>
  </g>
</svg>
"""
)

st.markdown(
    flat(
        f"""
<div class="race-bar">
  <div class="kerb"></div>
  <div class="road"></div>
  <div class="runner">
    <div class="streaks"><i></i><i></i><i></i><i></i></div>
    {CAR_SVG}
  </div>
</div>
"""
    ),
    unsafe_allow_html=True,
)

# =========================================================================
# BARRA LATERAL
# =========================================================================
with st.sidebar:
    st.markdown(
        flat(
            """
<div class="side-card">
  <h3>🏁 Acerca de</h3>
  <p>En esta aplicación veremos la capacidad que ahora tiene una máquina de interpretar un boceto.
  Dibuja carros, bólidos o pistas y deja que la IA los analice.</p>
</div>
"""
        ),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-title">🛠️ Ajustes de pista</div>', unsafe_allow_html=True)
    stroke_width = st.slider("Ancho de línea", 1, 30, 5)
    stroke_color = st.color_picker("Color del trazo", "#000000")
    herramientas = {
        "✏️ Pincel libre": "freedraw",
        "📏 Línea recta": "line",
        "▭ Rectángulo": "rect",
        "⭕ Círculo": "circle",
        "✋ Mover figuras": "transform",
    }
    drawing_mode = herramientas[st.selectbox("Herramienta", list(herramientas.keys()))]

    if st.button("🗑️ Limpiar pista", use_container_width=True):
        st.session_state.canvas_v += 1
        st.rerun()

# =========================================================================
# PORTADA
# =========================================================================
st.markdown(
    flat(
        """
<div class="race-hero">
  <div class="checker"></div>
  <h1>Tablero Inteligente</h1>
  <p class="sub">🏎️ Dibuja carros, bólidos y circuitos de carreras</p>
</div>
"""
    ),
    unsafe_allow_html=True,
)

def imagen_a_base64(image_data) -> str:
    """Convierte el lienzo (RGBA) a PNG sobre fondo blanco y lo codifica en base64."""
    img = Image.fromarray(np.array(image_data).astype("uint8"), "RGBA")
    fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    fondo.alpha_composite(img)
    buf = io.BytesIO()
    fondo.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# =========================================================================
# TABLERO ANCHO Y CENTRADO
# =========================================================================
st.markdown('<div class="sec-title">🏁 Pista de dibujo</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sec-sub">Dibuja el boceto de tu carro (o lo que quieras) en el panel.</div>',
    unsafe_allow_html=True,
)

with st.container(key="canvas_card"):
    canvas_result = st_canvas(
        fill_color="rgba(240, 176, 60, 0.30)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#FFFFFF",
        height=360,
        width=860,
        drawing_mode=drawing_mode,
        key=f"canvas_{st.session_state.canvas_v}",
    )

# =========================================================================
# ZONA DE ANÁLISIS (abajo)
# =========================================================================
st.markdown('<div class="sec-title">⚡ Zona de análisis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sec-sub">Haz tu dibujo y la IA creará una historia a partir de esto.</div>',
    unsafe_allow_html=True,
)

with st.container(key="key_card"):
    st.markdown('<div class="card-h">🔑 Llave de encendido</div>', unsafe_allow_html=True)
    c_key, c_btn = st.columns([3, 2], vertical_alignment="bottom")
    with c_key:
        ke = st.text_input("Ingresa tu Clave", type="password", placeholder="sk-...")
    with c_btn:
        analyze_button = st.button("🚀 ¡Crear mi historia!", use_container_width=True)

api_key = ke.strip() if ke else ""

if not api_key:
    st.warning("Por favor ingresa tu API key.")
elif analyze_button:
    objetos = (canvas_result.json_data or {}).get("objects", []) if canvas_result is not None else []
    if canvas_result is None or canvas_result.image_data is None or not objetos:
        st.warning("🏎️ ¡Primero dibuja algo en la pista!")
    else:
        with st.spinner("🏎️ Calentando motores... escribiendo tu historia"):
            try:
                client = OpenAI(api_key=api_key)
                base64_image = imagen_a_base64(canvas_result.image_data)
                prompt_text = (
                    "Mira este dibujo hecho a mano y escribe una historia corta, creativa y amena "
                    "en español (máximo 3 párrafos) inspirada en lo que ves. Ponle un título."
                )
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=700,
                )
                st.session_state.mi_respuesta = response.choices[0].message.content or ""
            except Exception as e:
                st.error(f"An error occurred: {e}")

if st.session_state.mi_respuesta:
    with st.container(key="result_card"):
        st.markdown('<div class="card-h">📖 Tu historia</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.mi_respuesta)
