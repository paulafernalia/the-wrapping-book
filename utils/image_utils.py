from PIL import Image
from reportlab.lib.utils import ImageReader
import re
import cairosvg
import io
import os
from pdf2image import convert_from_path


def pdf_to_pngs(pdf_path, output_folder='.'):
    try:
        # Extract base name without extension
        base = os.path.splitext(os.path.basename(pdf_path))[0]

        # Convert PDF pages to images
        images = convert_from_path(pdf_path)

        for i, img in enumerate(images, start=1):
            filename = f"{base}_p{i}.png"
            full_path = os.path.join(output_folder, filename)
            img.save(full_path, "PNG")
            print(f"Saved page {i} to {full_path}")

    except Exception as e:
        print("Failed to convert PDF to PNGs:", e)


def transform_svg_cover(svg_path, target_color, init_color="ff0000"):
    """
    Convert SVG file to PNG with transparent background.
    
    Parameters:
    - svg_path: str, path to input SVG file
    - target_color: str, target color to replace the initial color with
    - init_color: str, initial color to be replaced (default: "ff0000")
    
    Returns:
    - PIL.Image object with transparent background
    """
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {svg_path} does not exist.")
    
    # Replace the initial color with the target color
    updated_content = svg_content.replace(init_color, target_color)
    
    temp_svg = "temp.svg"
    temp_png = "temp.png"
    try:
        with open(temp_svg, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        cairosvg.svg2png(
            url=temp_svg,
            write_to=temp_png,
            output_width=None,
            output_height=None,
            scale=1.0,
            background_color=None  # This ensures a transparent background
        )

        img = ImageReader(temp_png)
                
    finally:
        # Ensure the temporary file is removed even if an error occurs
        if os.path.exists(temp_svg):
            os.remove(temp_svg)
        
        if os.path.exists(temp_png):
            os.remove(temp_png)

    return img


def svg_to_pdf(input_svg, output_pdf):
    try:
        cairosvg.svg2pdf(url=input_svg, write_to=output_pdf)
        print(f"Successfully converted '{input_svg}' to '{output_pdf}'")
    except Exception as e:
        print("Conversion failed:", e)
    