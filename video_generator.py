"""
Generador de video vertical explicando cómo funciona una computadora.
- Formato: 1080x1920 (vertical/portrait)
- Duración: ~60 segundos
- Narración: ElevenLabs TTS (voz Adam)
- Música de fondo: generada con numpy
- Visuales: escenas animadas con Pillow + MoviePy 2.x
"""

import os
import math
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoClip, AudioFileClip, CompositeAudioClip,
    AudioArrayClip, concatenate_videoclips,
)
from dotenv import load_dotenv

load_dotenv()

# ─── Configuración ────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1080, 1920
FPS = 30
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam

BG_DARK      = (10, 10, 30)
BG_ACCENT    = (20, 20, 60)
COLOR_WHITE  = (255, 255, 255)
COLOR_CYAN   = (0, 220, 255)
COLOR_BLUE   = (0, 120, 255)
COLOR_GREEN  = (0, 230, 120)
COLOR_YELLOW = (255, 220, 0)
COLOR_PURPLE = (160, 60, 255)

# ─── Segmentos ────────────────────────────────────────────────────────────────
SEGMENTS = [
    {
        "narration": (
            "¿Alguna vez te has preguntado cómo funciona una computadora? "
            "En este video te lo explicamos de forma sencilla."
        ),
        "title": "¿Cómo funciona\nuna computadora?",
        "subtitle": "Guía visual",
        "accent": COLOR_CYAN,
        "icon": "💻",
        "duration": 7,
    },
    {
        "narration": (
            "Todo empieza con el CPU, el procesador. "
            "Es el cerebro de la computadora. "
            "Ejecuta millones de instrucciones por segundo y coordina todo lo que ocurre."
        ),
        "title": "CPU",
        "subtitle": "El Cerebro\nProcesador Central",
        "accent": COLOR_BLUE,
        "icon": "🧠",
        "duration": 10,
    },
    {
        "narration": (
            "La RAM es la memoria de trabajo. "
            "Guarda temporalmente los programas que están abiertos. "
            "Cuanta más RAM tienes, más programas puedes usar al mismo tiempo."
        ),
        "title": "RAM",
        "subtitle": "Memoria de Trabajo\nTemporal y Rápida",
        "accent": COLOR_GREEN,
        "icon": "⚡",
        "duration": 10,
    },
    {
        "narration": (
            "El almacenamiento, ya sea un disco duro o un SSD, "
            "guarda tus archivos, fotos y programas de forma permanente, "
            "incluso cuando apagas la computadora."
        ),
        "title": "Almacenamiento",
        "subtitle": "HDD / SSD\nMemoria Permanente",
        "accent": COLOR_YELLOW,
        "icon": "💾",
        "duration": 10,
    },
    {
        "narration": (
            "La tarjeta madre o motherboard conecta todos los componentes entre sí. "
            "Es la autopista por donde viajan los datos entre el CPU, la RAM y el almacenamiento."
        ),
        "title": "Motherboard",
        "subtitle": "Placa Madre\nConecta Todo",
        "accent": COLOR_PURPLE,
        "icon": "🔌",
        "duration": 10,
    },
    {
        "narration": (
            "Finalmente, los dispositivos de entrada como el teclado y el mouse "
            "envían información a la computadora, "
            "y los de salida como el monitor y los parlantes muestran los resultados."
        ),
        "title": "Entrada / Salida",
        "subtitle": "Teclado, Mouse\nMonitor, Parlantes",
        "accent": COLOR_CYAN,
        "icon": "🖥️",
        "duration": 10,
    },
    {
        "narration": (
            "Así es como funciona una computadora: "
            "el CPU piensa, la RAM recuerda temporalmente, "
            "el almacenamiento guarda todo, y la motherboard los conecta. "
            "¡Ahora ya sabes cómo funciona!"
        ),
        "title": "¡Ahora lo sabes!",
        "subtitle": "CPU · RAM · Storage\nMotherboard · I/O",
        "accent": COLOR_GREEN,
        "icon": "🚀",
        "duration": 13,
    },
]


# ─── Audio helpers ────────────────────────────────────────────────────────────

def generate_background_music(duration_secs: float, sample_rate: int = 44100) -> np.ndarray:
    t = np.linspace(0, duration_secs, int(sample_rate * duration_secs), endpoint=False)
    freqs_l = [130.81, 155.56, 196.00, 261.63, 311.13]
    freqs_r = [130.81, 155.56, 196.00, 261.63, 329.63]
    amps    = [0.18, 0.15, 0.12, 0.10, 0.08]

    left  = sum(a * np.sin(2 * np.pi * f * t) for f, a in zip(freqs_l, amps))
    right = sum(a * np.sin(2 * np.pi * f * t) for f, a in zip(freqs_r, amps))
    pulse = 0.04 * np.sin(2 * np.pi * 0.5 * t) * np.sin(2 * np.pi * 4 * t)
    left  += pulse
    right += pulse

    fade = int(sample_rate * 2)
    env = np.ones_like(t)
    env[:fade]  = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    left  *= env * 0.18
    right *= env * 0.18

    return np.column_stack([left, right]).astype(np.float32)


def elevenlabs_tts(text: str, output_path: str) -> bool:
    if not ELEVENLABS_API_KEY:
        print("  [WARN] ELEVENLABS_API_KEY no configurada.")
        return False
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75,
                           "style": 0.3, "use_speaker_boost": True},
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            print(f"  [TTS OK] {output_path}")
            return True
        print(f"  [TTS ERR] {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"  [TTS SKIP] No se pudo conectar a ElevenLabs: {type(e).__name__}. Continuando sin narración.")
        return False


# ─── Visual helpers ───────────────────────────────────────────────────────────

def load_font(size: int):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_text_centered(draw, text, cy, width, font, color):
    lines = text.split("\n")
    try:
        lh = draw.textbbox((0, 0), "A", font=font)[3] * 1.4
    except Exception:
        lh = 40
    y = cy - lh * len(lines) / 2
    for line in lines:
        try:
            tw = draw.textbbox((0, 0), line, font=font)[2]
        except Exception:
            tw = len(line) * 20
        draw.text(((width - tw) / 2, y), line, font=font, fill=color)
        y += lh


def draw_hex_grid(draw, accent, alpha=25):
    s = 60
    for row in range(HEIGHT // (s * 2) + 2):
        for col in range(WIDTH // int(s * math.sqrt(3)) + 2):
            cx = col * int(s * math.sqrt(3))
            cy = row * s * 2 + (s if col % 2 else 0)
            pts = [
                (cx + s * 0.9 * math.cos(math.radians(60 * i - 30)),
                 cy + s * 0.9 * math.sin(math.radians(60 * i - 30)))
                for i in range(6)
            ]
            r, g, b = accent
            draw.polygon(pts, fill=(r, g, b, alpha), outline=(r, g, b, 60))


def draw_circuit_lines(draw, accent, seed=0):
    rng = np.random.default_rng(seed % (2**31))
    r, g, b = accent
    for _ in range(18):
        x1, y1 = int(rng.integers(0, WIDTH)), int(rng.integers(0, HEIGHT))
        ln = int(rng.integers(60, 300))
        if rng.integers(0, 2):
            x2, y2 = x1 + ln, y1
        else:
            x2, y2 = x1, y1 + ln
        draw.line([(x1, y1), (x2, y2)], fill=(r, g, b, 60), width=2)
        draw.ellipse([(x2 - 5, y2 - 5), (x2 + 5, y2 + 5)], fill=(r, g, b, 100))


def make_frame(seg: dict, progress: float) -> np.ndarray:
    accent = seg["accent"]
    r, g, b = accent

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    # Gradiente de fondo
    for y in range(HEIGHT):
        t = y / HEIGHT
        cr = int(BG_DARK[0] + (BG_ACCENT[0] - BG_DARK[0]) * t)
        cg = int(BG_DARK[1] + (BG_ACCENT[1] - BG_DARK[1]) * t)
        cb = int(BG_DARK[2] + (BG_ACCENT[2] - BG_DARK[2]) * t)
        draw.line([(0, y), (WIDTH, y)], fill=(cr, cg, cb, 255))

    draw_hex_grid(draw, accent)
    draw_circuit_lines(draw, accent, seed=abs(hash(seg["title"])) % (2**31))

    # Borde pulsante
    pa = int(40 + 30 * math.sin(progress * math.pi * 6))
    draw.rectangle([(8, 8), (WIDTH - 8, HEIGHT - 8)], outline=(r, g, b, pa), width=8)

    # Círculo icono
    cx, cy_icon = WIDTH // 2, int(HEIGHT * 0.28)
    cr_size = 160
    ga = int(60 + 40 * math.sin(progress * math.pi * 4))
    draw.ellipse([(cx - cr_size, cy_icon - cr_size), (cx + cr_size, cy_icon + cr_size)],
                 fill=(r, g, b, ga), outline=(r, g, b, 150), width=4)

    # Icono
    icon_font = load_font(110)
    icon = seg["icon"]
    try:
        ib = draw.textbbox((0, 0), icon, font=icon_font)
        iw, ih = ib[2] - ib[0], ib[3] - ib[1]
    except Exception:
        iw, ih = 100, 100
    draw.text(((WIDTH - iw) / 2, cy_icon - ih / 2), icon, font=icon_font, fill=COLOR_WHITE)

    # Línea separadora
    sep_y = int(HEIGHT * 0.46)
    lw = int(WIDTH * 0.6 * min(progress * 3, 1))
    xs = (WIDTH - lw) // 2
    draw.line([(xs, sep_y), (xs + lw, sep_y)], fill=(r, g, b, 220), width=4)

    # Título
    tf = load_font(90 if len(seg["title"]) < 12 else 70)
    draw_text_centered(draw, seg["title"], int(HEIGHT * 0.56), WIDTH, tf, COLOR_WHITE)

    # Subtítulo
    sf = load_font(46)
    draw_text_centered(draw, seg["subtitle"], int(HEIGHT * 0.70), WIDTH,
                       sf, (r, g, b, 210))

    # Barra de progreso
    by = int(HEIGHT * 0.90)
    bw = int(WIDTH * 0.70)
    bx = (WIDTH - bw) // 2
    draw.rounded_rectangle([(bx, by), (bx + bw, by + 14)], radius=7, fill=(60, 60, 80, 200))
    fw = int(bw * progress)
    if fw > 0:
        draw.rounded_rectangle([(bx, by), (bx + fw, by + 14)], radius=7, fill=(r, g, b, 230))

    return np.array(img.convert("RGB"))


# ─── Build ────────────────────────────────────────────────────────────────────

def build_video():
    os.makedirs("output", exist_ok=True)
    total_dur = sum(s["duration"] for s in SEGMENTS)
    print(f"\nGenerando video vertical {WIDTH}x{HEIGHT} · {total_dur}s\n")

    # 1. Narración ElevenLabs
    narr_files = []
    for i, seg in enumerate(SEGMENTS):
        path = f"output/narr_{i}.mp3"
        ok = elevenlabs_tts(seg["narration"], path)
        narr_files.append(path if ok else None)

    # 2. Música de fondo
    print("\nGenerando música de fondo...")
    music_arr = generate_background_music(total_dur + 2)
    music_clip = AudioArrayClip(music_arr, fps=44100).with_duration(total_dur)

    # 3. Clips de video por segmento
    print("\nRenderizando frames...")
    vid_clips = []
    for i, seg in enumerate(SEGMENTS):
        dur = seg["duration"]
        print(f"  [{i+1}/{len(SEGMENTS)}] {seg['title']} ({dur}s)")

        def make_fn(s=seg, d=dur):
            def fn(t):
                return make_frame(s, t / d)
            return fn

        vc = VideoClip(make_fn(), duration=dur).with_fps(FPS)
        vid_clips.append(vc)

    # 4. Ensamblar video
    print("\nEnsamblando...")
    final_video = concatenate_videoclips(vid_clips, method="chain")

    # 5. Audio compuesto
    audio_parts = [music_clip]
    t_offset = 0.0
    for i, seg in enumerate(SEGMENTS):
        if narr_files[i] and os.path.exists(narr_files[i]):
            try:
                na = AudioFileClip(narr_files[i])
                if na.duration > seg["duration"]:
                    na = na.subclipped(0, seg["duration"])
                audio_parts.append(na.with_start(t_offset))
            except Exception as e:
                print(f"  [WARN] audio {i}: {e}")
        t_offset += seg["duration"]

    final_audio = CompositeAudioClip(audio_parts)
    final_video = final_video.with_audio(final_audio)

    # 6. Exportar
    out = "output/computadora_explicada.mp4"
    print(f"\nExportando → {out}")
    final_video.write_videofile(
        out, fps=FPS, codec="libx264", audio_codec="aac",
        bitrate="4000k", audio_bitrate="192k",
        ffmpeg_params=["-vf", f"scale={WIDTH}:{HEIGHT}"],
        logger=None,
    )

    print(f"\n✓ Video listo: {out}")
    print(f"  {WIDTH}x{HEIGHT} · {total_dur}s · {FPS}fps")


if __name__ == "__main__":
    build_video()
