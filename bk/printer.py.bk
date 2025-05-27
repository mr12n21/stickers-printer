import os
import warnings
from PIL import Image
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
import logging

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=DeprecationWarning, module="brother_ql")

PRINTER_MODEL = "QL-1050"
USB_PATH = "/dev/usb/lp0"

def print_label_with_image(image_path, test_mode, total_prints):
    logger.info(f"Processing label: {image_path} (Test mode: {test_mode})")
    try:
        if test_mode:
            logger.info(f"Test mode: Saving {total_prints} copies of {image_path} without printing")
            return
        image = Image.open(image_path)
        image = image.convert('1')
        target_width = 696
        if image.width != target_width:
            scale_factor = target_width / image.width
            target_height = int(image.height * scale_factor)
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        qlr = BrotherQLRaster(PRINTER_MODEL)
        instructions = convert(qlr, [image], label='62', rotate='0')
        for i in range(total_prints):
            send(instructions, USB_PATH)
            logger.info(f"Print {i+1}/{total_prints} of '{image_path}' completed")
    except Exception as e:
        logger.error(f"Error during printing: {e}")
