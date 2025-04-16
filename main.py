from utils import fonts
from utils import report_utils
from utils import db_utils
from utils import data_utils


def main():
    # Get carries from supabase
    carries = db_utils.get_carries()

    # Create generator and cover page
    generator = report_utils.CoverPageGenerator(font_config=fonts.FONTCONFIG)

    for carry in carries:
        generator.create_cover_page(output_path="covers", carry=carry)

if __name__ == "__main__":
    main()