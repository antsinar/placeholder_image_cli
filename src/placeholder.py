from __future__ import annotations

from argparse import ArgumentParser
from collections import namedtuple
import logging
from PIL import Image
from PIL import ImageFilter
from PIL.ImageDraw import ImageDraw
import re
from enum import auto, StrEnum
from pathlib import Path

BoundTuple = namedtuple("BoundTuple", ["lower", "upper"])
RGBTuple = namedtuple("RGBTuple", ["r", "g", "b"])
RatioTuple = namedtuple("RatioTuple", ["width", "height"])


class DimmentionOptions(StrEnum):
    SIZE = auto()
    RATIO = auto()


BOUNDS = {
    "width": BoundTuple(lower=32, upper=4000),
    "height": BoundTuple(lower=32, upper=4000),
    "ratio": BoundTuple(lower=1, upper=30),
}


def validate_ratio(value: list[int]) -> bool:
    if not isinstance(value, list):
        return False
    if not len(value) == 2:
        return False
    return all([validate_range(v, BOUNDS["ratio"]) for v in value])


def validate_hex_color(value: str) -> bool:
    """
    Parses a hex color and returns True if it is valid
    See: https://stackoverflow.com/a/1636354

    Args:
        value (str): hex color code
        ^              anchor for start of string
        #              the literal #
        (              start of group
        ?:            indicate a non-capturing group that doesn't generate backreferences
        [0-9a-fA-F]   hexadecimal digit
        {3}           three times
        )              end of group
        {1,2}          repeat either once or twice
        $              anchor for end of string
    """
    return re.match(r"^#(?:[0-9a-fA-F]{3,4}){1,2}$", value)


def validate_range(value: int, bounds: BoundTuple) -> bool:
    """
    Validates if the image size is within the allowed range

    Args:
        value (int): numeric value
        bounds (BoundTuple): tuple with lower and upper

    Returns:
        bool: True if the value is within the bounds
    """
    return value >= bounds.lower and value <= bounds.upper


def dimmentions_from_ratio(
    ratio: RatioTuple, base_dimmention: int = 100
) -> tuple[int, int]:
    if base_dimmention * ratio.width > BOUNDS["width"].upper:
        base_dimmention = BOUNDS["width"].upper // ratio.width
    if base_dimmention * ratio.height > BOUNDS["height"].upper:
        base_dimmention = BOUNDS["height"].upper // ratio.height
    return (base_dimmention * ratio.width), (base_dimmention * ratio.height)


def placeholder_exists(
    width: int,
    height: int,
    save_root: Path = Path(__file__).parent.parent / "placeholders",
) -> bool:
    if not save_root.is_dir():
        return False
    return f"{width}_x_{height}.jpg" in [
        f.name for f in save_root.iterdir() if f.is_file()
    ]


class ImageGenerator:
    def __init__(
        self,
        width: int,
        height: int,
        color: str,
        save_root: Path = Path(__file__).parent.parent / "placeholders",
    ) -> None:
        self.width = width
        self.height = height
        self.color = RGBTuple(
            r=(color >> 16) & 0xFF, g=(color >> 8) & 0xFF, b=color & 0xFF
        )
        self.image: Image.Image | None = None
        self.save_root = save_root

    @property
    def inverted_color(self):
        return RGBTuple(
            r=255 - self.color.r,
            g=255 - self.color.g,
            b=255 - self.color.b,
        )

    def start(self):
        self._setup_frame()
        self._setup_cross()
        self._smoothen_image()
        self._save_image()

    def _setup_frame(self):
        self.image = Image.new("RGB", (self.width, self.height), self.color)

    def _setup_cross(self):
        """
        Draws an X symbol across the image
        """
        draw = ImageDraw(self.image)
        _width = 2 if self.image.width < 1000 else 3
        draw.line(
            (0, 0, self.width, self.height), fill=self.inverted_color, width=_width
        )
        draw.line(
            (0, self.height, self.width, 0), fill=self.inverted_color, width=_width
        )

    def _smoothen_image(self):
        self.image.filter(ImageFilter.GaussianBlur(radius=1))

    def _save_image(self):
        _save_path = (
            f"{self.save_root.as_posix()}/{self.image.width}_x_{self.image.height}.jpg"
        )
        self.image.save(_save_path, format="jpeg")
        logger.info(f"Saved placeholder image @ {_save_path}")

    def __str__(self) -> str:
        return f"ImageGenerator(width={self.width}, height={self.height}, color={self.color})"


def main():
    parser = ArgumentParser()
    parser.add_argument("option", help="fixed size or ratio", type=DimmentionOptions)
    parser.add_argument("--width", help="width of the image", type=int, nargs="?")
    parser.add_argument("--height", help="height of the image", type=int, nargs="?")
    parser.add_argument("--ratio", help="image aspect ratio", type=int, nargs="*")
    parser.add_argument("-c", "--color", type=str, default="#96b08a")
    parser.add_argument(
        "-o",
        "--out",
        help="placeholder output directory",
        type=Path,
        nargs="?",
        default=Path(__file__).parent.parent,
    )
    parser.description = (
        "Generates a placeholder image with the specified width and height"
    )
    args = parser.parse_args()

    match args.option:
        case DimmentionOptions.SIZE:
            if not (args.width and args.height):
                logger.error("Missing width or height")
                return 1
            if not (
                validate_range(args.width, BOUNDS["width"])
                and validate_range(args.height, BOUNDS["height"])
            ):
                logger.error(f"Invalid size {args.width}x{args.height}")
                return 1
            width, height = args.width, args.height
        case DimmentionOptions.RATIO:
            if not validate_ratio(args.ratio):
                logger.error(f"Invalid ratio: {args.ratio}")
                return 1
            try:
                ratio = RatioTuple(width=args.ratio[0], height=args.ratio[1])
            except IndexError:
                logger.error("Missing width or height ratio")
                return 1
            width, height = dimmentions_from_ratio(ratio)

        case _:
            logger.error(f"Invalid option {args.option}")
            return 1

    if not validate_hex_color(args.color):
        logger.error(f"Invalid color {args.color}")
        return 1

    (args.out / "placeholders").mkdir(exist_ok=True, parents=True)

    if placeholder_exists(width, height, args.out / "placeholders"):
        logger.info(
            f"Placeholder {width}x{height} already exists in placeholders directory"
        )
        return

    generator = ImageGenerator(
        width, height, int(args.color.replace("#", "0x"), 16), args.out / "placeholders"
    )
    generator.start()


if __name__ == "__main__":
    logs_location = Path(__file__).parent.parent / "logs/usage.log"
    logs_location.parent.mkdir(exist_ok=True, parents=True)
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s : %(message)s",
        filename=(logs_location).as_posix(),
        level=logging.INFO,
    )
    logger = logging.getLogger(__name__)
    main()
