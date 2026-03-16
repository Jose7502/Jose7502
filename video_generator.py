"""
Generador de video vertical explicando cómo funciona una computadora.
- Formato: 1080x1920 (vertical/portrait)
- Duración: ~60 segundos
- Narración: ElevenLabs TTS
- Música de fondo: generada con numpy
- Visuales: escenas animadas con Pillow + MoviePy
"""

import os
import io
import math
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, CompositeAudioClip
)
from moviepy.audio.AudioClip import AudioArrayClip
from dotenv import load_dotenv

load_dotenv()

# ─── Configuración ────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1080, 1920
FPS = 30
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam (default)

# Paleta de colores
BG_DARK      = (10, 10, 30)
BG_ACCENT    = (20, 20, 60)
COLOR_BLUE   = (0, 120, 255)
COLOR_CYAN   = (0, 220, 255)
COLOR_WHITE  = (255, 255, 255)
COLOR_GRAY   = (180, 180, 200)
COLOR_YELLOW = (255, 220, 0)
COLOR_GREEN  = (0, 230, 120)
COLOR_PURPLE = (160, 60, 255)

# ─── Segmentos del video ──────────────────────────────────────────────────────
# Cada segmento: (texto_narración, título, subtítulo, color_acento, emoji_icono)
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


# ─── Utilidades de audio ──────────────────────────────────────────────────────

def generate_background_music(duration_secs: float, sample_rate: int = 44100) -> np.ndarray:
    """Genera música ambiental suave con tonos sinusoidales y armónicos."""
    t = np.linspace(0, duration_secs, int(sample_rate * duration_secs), endpoint=False)

    # Acorde base: Do menor (tecnológico/épico)
    freqs_left  = [130.81, 155.56, 196.00, 261.63, 311.13]  # C3, Eb3, G3, C4, Eb4
    freqs_right = [130.81, 155.56, 196.00, 261.63, 329.63]  # con variación

    def chord(freqs, amplitudes=None):
        if amplitudes is None:
            amplitudes = [0.18, 0.15, 0.12, 0.10, 0.08]
        wave = np.zeros_like(t)
        for f, a in zip(freqs, amplitudes):
            wave += a * np.sin(2 * np.pi * f * t)
        return wave

    left  = chord(freqs_left)
    right = chord(freqs_right)

    # Pulso de baja frecuencia (ritmo suave)
    pulse = 0.04 * np.sin(2 * np.pi * 0.5 * t) * np.sin(2 * np.pi * 4 * t)
    left  += pulse
    right += pulse

    # Fade in / fade out
    fade_samples = int(sample_rate * 2)
    envelope = np.ones_like(t)
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

    left  *= envelope
    right *= envelope

    audio = np.column_stack([left, right]).astype(np.float32)
    return audio


def elevenlabs_tts(text: str, output_path: str) -> bool:
    """Genera audio con ElevenLabs y lo guarda como MP3."""
    if not ELEVENLABS_API_KEY:
        print("[WARN] ELEVENLABS_API_KEY no configurada — se omite narración.")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        print(f"  [TTS] {output_path} generado.")
        return True
    else:
        print(f"  [TTS ERROR] {resp.status_code}: {resp.text}")
        return False


# ─── Utilidades visuales ──────────────────────────────────────────────────────

def load_font(size: int):
    """Carga fuente del sistema o cae a la fuente por defecto de Pillow."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_text_centered(draw, text, y, width, font, color, line_height_mult=1.4):
    """Dibuja texto centrado horizontalmente con soporte multilínea."""
    lines = text.split("\n")
    try:
        bbox = draw.textbbox((0, 0), "A", font=font)
        line_h = (bbox[3] - bbox[1]) * line_height_mult
    except Exception:
        line_h = font.size * line_height_mult if hasattr(font, "size") else 30 * line_height_mult

    total_h = line_h * len(lines)
    cur_y = y - total_h / 2

    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
        except Exception:
            text_w = len(line) * (font.size if hasattr(font, "size") else 20)

        x = (width - text_w) / 2
        draw.text((x, cur_y), line, font=font, fill=color)
        cur_y += line_h


def draw_hex_grid(draw, width, height, accent, alpha=40):
    """Dibuja una cuadrícula hexagonal decorativa de fondo."""
    hex_size = 60
    rows = height // (hex_size * 2) + 2
    cols = width  // (int(hex_size * math.sqrt(3))) + 2

    for row in range(rows):
        for col in range(cols):
            cx = col * int(hex_size * math.sqrt(3))
            cy = row * hex_size * 2
            if col % 2 == 1:
                cy += hex_size

            points = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                px = cx + hex_size * 0.9 * math.cos(angle)
                py = cy + hex_size * 0.9 * math.sin(angle)
                points.append((px, py))

            r, g, b = accent
            fill_color = (r, g, b, alpha)
            draw.polygon(points, fill=fill_color, outline=(r, g, b, 80))


def draw_circuit_lines(draw, width, height, accent, seed=0):
    """Dibuja líneas decorativas tipo circuito."""
    rng = np.random.default_rng(seed)
    r, g, b = accent

    for _ in range(18):
        x1 = int(rng.integers(0, width))
        y1 = int(rng.integers(0, height))
        length = int(rng.integers(60, 300))
        direction = int(rng.integers(0, 2))

        if direction == 0:
            x2, y2 = x1 + length, y1
        else:
            x2, y2 = x1, y1 + length

        draw.line([(x1, y1), (x2, y2)], fill=(r, g, b, 60), width=2)
        # Nodo en el extremo
        draw.ellipse([(x2 - 5, y2 - 5), (x2 + 5, y2 + 5)], fill=(r, g, b, 100))


def create_segment_frame(seg: dict, frame_idx: int, total_frames: int) -> Image.Image:
    """Crea un frame animado para un segmento del video."""
    progress = frame_idx / max(total_frames - 1, 1)
    accent   = seg["accent"]

    # Canvas base con gradiente vertical
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img, "RGBA")

    # Gradiente de fondo
    for y in range(HEIGHT):
        t_grad = y / HEIGHT
        r = int(BG_DARK[0] + (BG_ACCENT[0] - BG_DARK[0]) * t_grad)
        g = int(BG_DARK[1] + (BG_ACCENT[1] - BG_DARK[1]) * t_grad)
        b = int(BG_DARK[2] + (BG_ACCENT[2] - BG_DARK[2]) * t_grad)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Cuadrícula hexagonal
    draw_hex_grid(draw, WIDTH, HEIGHT, accent, alpha=25)

    # Líneas de circuito decorativas
    draw_circuit_lines(draw, WIDTH, HEIGHT, accent, seed=hash(seg["title"]) % 9999)

    # Animación: pulso de borde
    pulse_alpha = int(40 + 30 * math.sin(progress * math.pi * 6))
    r, g, b = accent
    border_w = 8
    draw.rectangle(
        [(border_w, border_w), (WIDTH - border_w, HEIGHT - border_w)],
        outline=(r, g, b, pulse_alpha),
        width=border_w,
    )

    # ── Sección superior: icono grande ─────────────────────────────────────
    icon_y = int(HEIGHT * 0.28)
    # Círculo de fondo para el icono
    circle_r = 160
    cx = WIDTH // 2
    glow_alpha = int(60 + 40 * math.sin(progress * math.pi * 4))
    draw.ellipse(
        [(cx - circle_r, icon_y - circle_r), (cx + circle_r, icon_y + circle_r)],
        fill=(r, g, b, glow_alpha),
        outline=(r, g, b, 150),
        width=4,
    )

    # Icono emoji como texto
    icon_font = load_font(120)
    icon_text = seg["icon"]
    try:
        bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
        iw = bbox[2] - bbox[0]
        ih = bbox[3] - bbox[1]
    except Exception:
        iw, ih = 100, 100
    draw.text(
        ((WIDTH - iw) / 2, icon_y - ih / 2),
        icon_text,
        font=icon_font,
        fill=COLOR_WHITE,
    )

    # ── Línea separadora con efecto ─────────────────────────────────────────
    sep_y = int(HEIGHT * 0.46)
    line_width_anim = int((WIDTH * 0.6) * min(progress * 3, 1))
    x_start = (WIDTH - line_width_anim) // 2
    draw.line([(x_start, sep_y), (x_start + line_width_anim, sep_y)],
              fill=(r, g, b, 220), width=4)

    # ── Título ──────────────────────────────────────────────────────────────
    title_font = load_font(90 if len(seg["title"]) < 12 else 72)
    draw_text_centered(draw, seg["title"], int(HEIGHT * 0.55), WIDTH,
                       title_font, COLOR_WHITE, line_height_mult=1.3)

    # ── Subtítulo ───────────────────────────────────────────────────────────
    sub_font = load_font(46)
    draw_text_centered(draw, seg["subtitle"], int(HEIGHT * 0.70), WIDTH,
                       sub_font, tuple(list(accent) + [200]), line_height_mult=1.4)

    # ── Barra de progreso inferior ──────────────────────────────────────────
    bar_y = int(HEIGHT * 0.90)
    bar_h = 14
    bar_w = int(WIDTH * 0.70)
    bar_x = (WIDTH - bar_w) // 2
    # Fondo barra
    draw.rounded_rectangle(
        [(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)],
        radius=7,
        fill=(60, 60, 80, 200),
    )
    # Relleno progreso
    fill_w = int(bar_w * progress)
    if fill_w > 0:
        draw.rounded_rectangle(
            [(bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h)],
            radius=7,
            fill=(r, g, b, 230),
        )

    return img.convert("RGB")


# ─── Construcción del video ───────────────────────────────────────────────────

def build_video():
    os.makedirs("output", exist_ok=True)
    audio_clips  = []
    video_clips  = []
    total_duration = sum(s["duration"] for s in SEGMENTS)

    print(f"Generando video vertical ({WIDTH}x{HEIGHT}) · {total_duration}s\n")

    # 1. Generar narración con ElevenLabs para cada segmento
    narration_files = []
    for i, seg in enumerate(SEGMENTS):
        path = f"output/narration_{i}.mp3"
        ok = elevenlabs_tts(seg["narration"], path)
        narration_files.append(path if ok else None)

    # 2. Generar música de fondo
    print("\nGenerando música de fondo...")
    sample_rate = 44100
    music_array = generate_background_music(total_duration + 2, sample_rate)
    # Bajar volumen de música al 18%
    music_array *= 0.18
    music_clip = AudioArrayClip(music_array, fps=sample_rate)
    music_clip = music_clip.set_duration(total_duration)

    # 3. Crear clips de video + audio por segmento
    print("\nRenderizando frames de video...")
    current_time = 0.0

    for i, seg in enumerate(SEGMENTS):
        dur = seg["duration"]
        n_frames = int(dur * FPS)

        print(f"  Segmento {i + 1}/{len(SEGMENTS)}: '{seg['title']}' ({dur}s, {n_frames} frames)")

        # Generar frames
        frames = [
            np.array(create_segment_frame(seg, f, n_frames))
            for f in range(n_frames)
        ]

        # Clip de video del segmento
        def make_frame_fn(frame_list, idx_offset=0):
            def frame_fn(t):
                frame_idx = min(int(t * FPS), len(frame_list) - 1)
                return frame_list[frame_idx]
            return frame_fn

        from moviepy.editor import VideoClip
        vid_clip = VideoClip(make_frame_fn(frames), duration=dur)
        vid_clip = vid_clip.set_fps(FPS)

        # Audio de narración
        if narration_files[i] and os.path.exists(narration_files[i]):
            try:
                narr_audio = AudioFileClip(narration_files[i])
                # Ajustar duración al segmento
                if narr_audio.duration > dur:
                    narr_audio = narr_audio.subclip(0, dur)
                narr_audio = narr_audio.set_start(current_time).volumex(1.0)
                audio_clips.append(narr_audio)
            except Exception as e:
                print(f"  [WARN] No se pudo cargar narración {i}: {e}")

        vid_clip = vid_clip.set_start(current_time)
        video_clips.append(vid_clip)
        current_time += dur

    # 4. Ensamblar video final
    print("\nEnsamblando video final...")
    from moviepy.editor import concatenate_videoclips

    final_video = concatenate_videoclips(
        [c.set_start(0) for c in [
            vc.set_start(0)
            for vc in video_clips
        ]],
        method="compose",
    )

    # Construir audio compuesto
    all_audio = [music_clip]
    if audio_clips:
        all_audio.extend(audio_clips)

    # Necesitamos ajustar los tiempos — reconstruir con concatenate
    # Más sencillo: concatenar video_clips sin set_start, luego audio separado
    final_video = concatenate_videoclips(
        [vc.set_start(0) for vc in [
            # Quitar start para poder concatenar
        ]] if False else video_clips,
        method="chain",
    )

    # Rehacer sin set_start individual para concatenation correcta
    clean_clips = []
    for vc in video_clips:
        clean_clips.append(vc.copy().set_start(0))

    final_video = concatenate_videoclips(clean_clips, method="chain")

    # Reajustar tiempos de narración relativos al inicio de cada clip
    final_audio_clips = [music_clip.set_start(0)]
    cumulative = 0.0
    for i, seg in enumerate(SEGMENTS):
        if narration_files[i] and os.path.exists(narration_files[i]):
            try:
                na = AudioFileClip(narration_files[i])
                if na.duration > seg["duration"]:
                    na = na.subclip(0, seg["duration"])
                na = na.set_start(cumulative).volumex(1.0)
                final_audio_clips.append(na)
            except Exception as e:
                print(f"  [WARN] Audio {i}: {e}")
        cumulative += seg["duration"]

    final_audio = CompositeAudioClip(final_audio_clips)
    final_video = final_video.set_audio(final_audio)

    # 5. Exportar
    output_path = "output/computadora_explicada.mp4"
    print(f"\nExportando '{output_path}'...")
    final_video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="4000k",
        audio_bitrate="192k",
        ffmpeg_params=["-vf", f"scale={WIDTH}:{HEIGHT}"],
        verbose=False,
        logger=None,
    )

    print(f"\n✓ Video generado: {output_path}")
    print(f"  Resolución : {WIDTH}x{HEIGHT} (vertical)")
    print(f"  Duración   : {total_duration}s")
    print(f"  FPS        : {FPS}")


if __name__ == "__main__":
    build_video()
