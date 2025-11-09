import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from bk_light.config import load_config
from bk_light.fonts import get_font_profile, list_available_fonts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    return parser.parse_args()


def main() -> None:
    _ = load_config(parse_args().config)
    fonts = list_available_fonts()
    if fonts:
        for name in fonts:
            profile = get_font_profile(name)
            details = []
            if profile.recommended_size is not None:
                details.append(f"size {profile.recommended_size}")
            if profile.offset_x or profile.offset_y:
                details.append(f"offset ({profile.offset_x}, {profile.offset_y})")
            suffix = f" ({', '.join(details)})" if details else ""
            print(f"{name}{suffix}")
    else:
        print("No fonts found in assets/fonts")


if __name__ == "__main__":
    main()
