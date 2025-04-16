from utils import fonts
from utils import report_utils
from utils import db_utils
from utils import data_utils


def main():
    # Get carries from supabase
    carries = db_utils.get_carries()

    # Create generator and cover page
    generator = report_utils.BookContentGenerator(font_config=fonts.FONTCONFIG)

    # for carry in carries:
    generator.create_combined_pdf(output_path=".", output_filename="book.pdf", carries=carries)


if __name__ == "__main__":
    main()
