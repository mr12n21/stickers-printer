from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from PIL import Image

def print_label_with_image(image_path, printer_model, usb_path, label_type='62'):
    try:
        image = Image.open(image_path)
        image = image.convert('1')

        target_width = 696
        if image.width != target_width:
            scale_factor = target_width / image.width
            target_height = int(image.height * scale_factor)
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        qlr = BrotherQLRaster(printer_model)

        instructions = convert(qlr, [image], label=label_type, rotate='0')

        send(instructions, usb_path)
        print(f"Printing '{image_path}' completed")
    except Exception as e:
        print(f"Error: {e}")
