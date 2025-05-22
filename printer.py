from PIL import Image
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert

def print_label_with_image(image, printer_model, usb_path, total_prints, label_type='62'):
    try:
        for i in range(total_prints):
            image_converted = image.convert('1')
            target_width = 696
            if image_converted.width != target_width:
                scale_factor = target_width / image_converted.width
                target_height = int(image_converted.height * scale_factor)
                image_converted = image_converted.resize((target_width, target_height), Image.Resampling.LANCZOS)
            qlr = BrotherQLRaster(printer_model)
            instructions = convert(qlr, [image_converted], label=label_type, rotate='0')
            send(instructions, usb_path)
            print(f"Tisk {i+1}/{total_prints} štítku")
    except Exception as e:
        print(f"Chyba při tisku: {e}")