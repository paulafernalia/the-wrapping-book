import os
import qrcode
from utils import colors_utils


# Data to be encoded
def generate_qr(carryname):
    # Create QR code object
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code, 1 is the smallest
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
        box_size=10,  # Size of each box in the QR code grid
        border=4,  # Thickness of the border (minimum is 4)
    )

    # Add data to the QR code
    qr.add_data(f"https//thewrappinggallery.com/carry/{carryname}")
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill=colors_utils.LIGHTBLACK, back_color="white")

    # Save the image to a file
    os.makedirs("qrcodes", exist_ok=True)
    path = os.path.join("qrcodes", f"qrcode_{carryname}.png")
    img.save(path)

    return path
