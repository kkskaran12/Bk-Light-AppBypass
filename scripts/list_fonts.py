import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from bk_light.config import load_config
from bk_light.fonts import FONT_PROFILES, list_available_fonts, normalize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    return parser.parse_args()


def main() -> None:
    _ = load_config(parse_args().config)
    fonts = list_available_fonts()
    if fonts:
        for name in fonts:
            key = normalize(name)
            details: list[str] = []
            profile = FONT_PROFILES.get(key)
            if profile:
                if profile.recommended_size is not None:
                    details.append(f"size {profile.recommended_size}")
                if profile.offset_x or profile.offset_y:
                    details.append(f"offset ({profile.offset_x}, {profile.offset_y})")
                colon_info: list[str] = []
                if profile.colon_dx:
                    colon_info.append(f"dx {profile.colon_dx}")
                if profile.colon_top_adjust or profile.colon_bottom_adjust != -1:
                    colon_info.append(f"top {profile.colon_top_adjust:+d}")
                    colon_info.append(f"bottom {profile.colon_bottom_adjust:+d}")
                if colon_info:
                    details.append("colon " + ", ".join(colon_info))
            suffix = f" ({'; '.join(details)})" if details else ""
            print(f"{name}{suffix}")
    else:
        print("No fonts found in assets/fonts")


if __name__ == "__main__":
    main()
