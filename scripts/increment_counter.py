import argparse
import asyncio
import sys
from dataclasses import replace
from pathlib import Path
from typing import Optional
from PIL import Image

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from bk_light.config import AppConfig, counter_options, load_config, text_options
from bk_light.fonts import get_font_profile, resolve_font
from bk_light.panel_manager import PanelManager
from bk_light.text import build_text_bitmap


def parse_color(value: str) -> tuple[int, int, int]:
    cleaned = value.replace("#", "").replace(" ", "")
    if "," in cleaned:
        parts = cleaned.split(",")
        return tuple(int(part) for part in parts[:3])
    if len(cleaned) == 6:
        return tuple(int(cleaned[i:i + 2], 16) for i in (0, 2, 4))
    raise ValueError("Invalid color")


def build_counter_image(
    canvas: tuple[int, int],
    value: int,
    color: tuple[int, int, int],
    background: tuple[int, int, int],
    font_path: Optional[Path],
    size: int,
    spacing: int,
    offset_x: int,
    offset_y: int,
    antialias: bool,
) -> Image.Image:
    text_bitmap = build_text_bitmap(
        str(value),
        font_path,
        size,
        spacing,
        color,
        antialias,
        monospace_digits=True,
    )
    frame = Image.new("RGBA", canvas, tuple(background) + (255,))
    origin_x = (canvas[0] - text_bitmap.width) // 2 + offset_x
    origin_y = (canvas[1] - text_bitmap.height) // 2 + offset_y
    frame.paste(text_bitmap, (origin_x, origin_y), text_bitmap)
    return frame.convert("RGB")


async def run_counter(config: AppConfig, preset_name: str, overrides: dict[str, Optional[str]]) -> None:
    counter_preset = counter_options(config, preset_name, overrides)
    text_preset = text_options(config, preset_name, {})
    color = parse_color(text_preset.color)
    background = parse_color(text_preset.background)
    font_ref = text_preset.font
    font_path = resolve_font(font_ref)
    profile = get_font_profile(font_ref, font_path)
    if profile.recommended_size is not None:
        size = profile.recommended_size
    else:
        size = text_preset.size
    spacing = text_preset.spacing
    offset_x = text_preset.offset_x + profile.offset_x
    offset_y = text_preset.offset_y + profile.offset_y
    start = overrides.get("start")
    count = overrides.get("count")
    delay = overrides.get("delay")
    start_value = int(start) if start is not None else counter_preset.start
    total = int(count) if count is not None else counter_preset.count
    interval = float(delay) if delay is not None else counter_preset.delay
    async with PanelManager(config) as manager:
        canvas = manager.canvas_size
        value = start_value
        for _ in range(total):
            image = build_counter_image(
                canvas,
                value,
                color,
                background,
                font_path,
                size,
                spacing,
                offset_x,
                offset_y,
                config.display.antialias_text,
            )
            await manager.send_image(image, delay=0.15)
            value += 1
            await asyncio.sleep(interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--address")
    parser.add_argument("--preset")
    parser.add_argument("--start", type=int)
    parser.add_argument("--count", type=int)
    parser.add_argument("--delay", type=float)
    return parser.parse_args()


def build_override_map(args: argparse.Namespace) -> dict[str, Optional[str]]:
    overrides: dict[str, Optional[str]] = {}
    if args.start is not None:
        overrides["start"] = str(args.start)
    if args.count is not None:
        overrides["count"] = str(args.count)
    if args.delay is not None:
        overrides["delay"] = str(args.delay)
    return overrides


if __name__ == "__main__":
    args = parse_args()
    config = load_config(args.config)
    if args.address:
        config.device = replace(config.device, address=args.address)
    preset_name = args.preset or config.runtime.preset or "default"
    overrides = build_override_map(args)
    asyncio.run(run_counter(config, preset_name, overrides))

