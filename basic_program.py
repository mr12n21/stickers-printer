from brother_ql import BrotherQLRaster
from brother_ql.backends import Backend
from brother_ql.models import Label
from brother_ql import utils

printer = BrotherQLRaster('usb://0x04f9:0x209b')

backend = Backend(printer)

label = Label('62')

label.text = 'test'

def print_label():
    backend.print(label)

    print("")

if __name__ == "__main__":
    print_label()
