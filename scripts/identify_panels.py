import argparse
import asyncio
import sys
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from bk_light.config import AppConfig, PanelDescriptor, load_config
from bk_light.display_session import BleDisplaySession


def build_panel_image(
    number: int,
    tile_width: int,
    tile_height: int,
    color: tuple[int, int, int],
    antialias: bool,
) -> bytes:
    background = (0, 0, 0)
    font = ImageFont.load_default()
    dummy = Image.new("L", (1, 1), 0)
    draw_dummy = ImageDraw.Draw(dummy)
    text = str(number)
    bbox = draw_dummy.textbbox((0, 0), text, font=font)
    width = max(1, bbox[2] - bbox[0])
    height = max(1, bbox[3] - bbox[1])
    mask_mode = "L" if antialias else "1"
    mask = Image.new(mask_mode, (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.text((-bbox[0], -bbox[1]), text, fill=255, font=font)
    if not antialias:
        mask = mask.convert("L")
    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fill_layer = Image.new("RGBA", (width, height), (*color, 255))
    text_layer = Image.composite(fill_layer, text_layer, mask)
    frame = Image.new("RGBA", (tile_width, tile_height), tuple(background) + (255,))
    origin_x = int((tile_width - width) / 2 - bbox[0])
    origin_y = int((tile_height - height) / 2 - bbox[1])
    frame.alpha_composite(text_layer, (origin_x, origin_y))
    frame_rgb = frame.convert("RGB")
    draw = ImageDraw.Draw(frame_rgb)
    draw.rectangle((0, 0, tile_width - 1, tile_height - 1), outline=(50, 50, 50))
    buffer = BytesIO()
    frame_rgb.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


async def display_panel(index: int, descriptor: PanelDescriptor, config: AppConfig) -> None:
    rotation = descriptor.rotation if descriptor.rotation is not None else config.device.rotate
    brightness = descriptor.brightness if descriptor.brightness is not None else config.device.brightness
    session = BleDisplaySession(
        address=descriptor.address,
        auto_reconnect=False,
        reconnect_delay=config.device.reconnect_delay,
        rotation=rotation,
        brightness=brightness,
        mtu=config.device.mtu,
        log_notifications=config.display.log_notifications,
    )
    try:
        async with session:
            color = (255, 120, 0)
            payload = build_panel_image(
                index,
                config.panels.tile_width,
                config.panels.tile_height,
                color,
                config.display.antialias_text,
            )
            await session.send_png(payload, delay=0.1)
            print(f"[{index}] {descriptor.name} @ {descriptor.address} (grid {descriptor.grid_x}, {descriptor.grid_y})")
            await asyncio.to_thread(input, "Press Enter to continue...")
    except Exception as error:
        print(f"ERROR identifying {descriptor.address}: {error}")


async def identify(config: AppConfig) -> None:
    panels = config.panels.items
    if not panels:
        address = config.device.address
        if not address:
            print("No panels defined and no device address set.")
            return
        panels = [
            PanelDescriptor(
                name="panel_1",
                address=address,
                grid_x=0,
                grid_y=0,
                rotation=config.device.rotate,
                brightness=config.device.brightness,
            )
        ]
    for index, descriptor in enumerate(panels, start=1):
        await display_panel(index, descriptor, config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--address")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    config = load_config(args.config)
    if args.address:
        config.device = replace(config.device, address=args.address)
    asyncio.run(identify(config))

