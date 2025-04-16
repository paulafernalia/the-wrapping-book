from PIL import Image

def convert_to_greyscale(image_path):
    img = Image.open(image_path)

    # Convert to greyscale
    gray_img = img.convert("L")  # "L" stands for luminance (greyscale)

    # Save the result
    new_name = f"{image_path[:-4]}_grey.png"
    gray_img.save(new_name)

    return new_name