from utils import fonts
from utils import report_utils

def main():
    """Example usage of the CoverPageGenerator class."""
    # Create generator and cover page
    generator = report_utils.CoverPageGenerator(font_config=fonts.FONTCONFIG)
    generator.create_cover_page(
        output_path="covers",
        carryid="annes_knotless_front_pocket",
        title="Anne's Knotless Front Pocket Double Cross Carry",
        subtitle="armpit to shoulder",
        size_text="BASE - 1",
        image_path="wendys_armpit_to_shoulder.png",
    )


if __name__ == "__main__":
    main()