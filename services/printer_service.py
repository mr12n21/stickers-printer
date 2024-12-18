from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send_to_printer
from PIL import Image
import os

def print_label(code):
    printer = "usb://0x04f9:0x2015/000M6Z401370"
    model = "QL-1050"
    label = "62"
    image_path = f"./archive/printed/{code}.png"

    image = Image.new('1', (696, 292), 255)
    image.save(image_path)

    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True
    qlr.convert(image_path, label, rotate="auto")

    send_to_printer(qlr.data, printer, backend="pyusb")
