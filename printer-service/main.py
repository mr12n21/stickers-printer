from brother_ql.raster import BrotherQLRaster # type: ignore
from brother_ql.backends.helpers import send # type: ignore
from brother_ql.conversion import convert # type: ignore
from PIL import Image # type: ignore

#tisk
def print_label_with_image(image_path, printer_model, usb_path, label_type='62'):
    try:
        #nacteni png
        image = Image.open(image_path)
        image = image.convert('1') #prevod na cb

        #zmenseni
        target_width = 696
        if image.width != target_width:
            scale_factor = target_width / image.width
            target_height = int(image.height * scale_factor)
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        #inicializace tiskarny
        qlr = BrotherQLRaster(printer_model)

        #prevod obrazku na tiskove instrukce
        instructions = convert(
            qlr,
            [image],
            label=label_type,
            rotate='0'
        )

        #odeslani
        send(instructions, usb_path)
        print(f"tisk '{image_path}' kompletni")
    except Exception as e:
        print(f"error: {e}")

printer_model = 'QL-1050'
usb_path = '/dev/usb/lp0'
image_path = './test1.png'

print_label_with_image(image_path, printer_model, usb_path)