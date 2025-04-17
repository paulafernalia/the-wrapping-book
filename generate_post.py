import argparse
from utils import fonts
from utils import report_utils
from utils import db_utils
from utils import data_utils


def main(output_dir, carryname):
    # Create generator and cover page
    carry = db_utils.get_carry_by_name(carryname)
    if carry is None:
        raise ValueError(f"Carry with a tutorial and name {carryname} not found in the database")
    generator = report_utils.PostGenerator(output_dir, carry)

    generator.generate_post()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate an instagram post from a tutorial"
    )
    parser.add_argument(
        "output_dir", type=str, help="Directory where the PDF will be saved"
    )
    parser.add_argument("carryname", type=str, help="Name of the carry, e.g. giselles")
    args = parser.parse_args()

    main(args.output_dir, args.carryname)
