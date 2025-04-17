from utils import BookGenerator
from utils import db_utils
from utils import data_utils


def main():
    # Get carries from supabase
    carries = db_utils.get_carries()

    # Create generator and cover page
    generator = BookGenerator.BookGenerator()

    # for carry in carries:
    generator.create_combined_pdf(
        output_path=".", output_filename="book.pdf", carries=carries
    )


if __name__ == "__main__":
    main()
