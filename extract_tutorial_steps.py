import argparse
import shutil
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_path
import os
import numpy as np
from utils import image_utils
from utils import db_utils

WIDTH = 191 - 24 - 0.5
HEIGHT = 693 - 488 + 1.5
STARTX = 24
STARTY = 693
BUFFERX = 24


def extract_steps_to_png(tutorial_dir, carryname):
    pdf_filename = f"{carryname}.pdf"
    input_pdf_path = os.path.join(tutorial_dir, pdf_filename)

    counter = 1
    pdf_reader = PdfReader(input_pdf_path)
    num_pages = len(pdf_reader.pages)

    filepaths = []
    if not os.path.exists("steps"):
        os.makedirs("steps")

    for m in range(num_pages):

        page = pdf_reader.pages[m]

        for j in range(0, 3):
            for i in range(0, 3):

                page.mediabox.upper_left = [
                    STARTX + i * (WIDTH + BUFFERX),
                    STARTY - j * HEIGHT]
                page.mediabox.lower_right = [
                    STARTX + (i + 1) * WIDTH + i * BUFFERX,
                    STARTY - (j + 1) * HEIGHT]

                pdf_writer = PdfWriter()
                pdf_writer.add_page(page)

                step_pdf_filename = f"{carryname}_{counter}.pdf"
                pdf_writer.write(step_pdf_filename)

                image = convert_from_path(
                    step_pdf_filename,
                    dpi=300,
                    poppler_path="/opt/homebrew/bin/")[0]

                os.remove(step_pdf_filename)

                pixels = np.array(list(image.getdata()))
                unique = np.unique(pixels, return_counts=False)
                if len(unique) == 1:
                    break

                step_png_path = f"{carryname}_step{str(counter).zfill(2)}.png"
                step_png_filename = os.path.split(step_png_path)[-1]

                new_path = os.path.join("steps", step_png_filename)
                image.save(new_path, "PNG")

                filepaths.append(os.path.join(new_path))

                counter += 1

    # Upload them to supabase
    db_utils.upload_png_files(filepaths)

    # Mark as tutorial available in production db
    db_utils.update_value_in_table(carryname)

    # Delete steps at the end
    if os.path.exists("steps"):
        # Remove the folder and all of its contents
        shutil.rmtree("steps")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate an instagram post from a tutorial"
    )
    parser.add_argument(
        "output_dir", type=str, help="Directory where the PDF will be saved"
    )
    parser.add_argument("carryname", type=str, help="Name of the carry, e.g. giselles")
    args = parser.parse_args()

    extract_steps_to_png(args.output_dir, args.carryname)


