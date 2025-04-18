from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import os
from utils import colors_utils
from utils import db_utils
from utils import qr_utils
from utils import BaseContentGenerator
from utils import HorizontalLine
import shutil


class BookGenerator(BaseContentGenerator.BaseContentGenerator):
    def _draw_page_header(self, c, carry, line_y):
        """
        Draw the page header with title, finish text and horizontal line

        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information
            line_y: Y-position for the horizontal line
        """
        # Draw horizontal line at the top
        line = HorizontalLine.HorizontalLine(
            width=self.width - self.margin, thickness=1
        )
        line.drawOn(c, self.margin / 2, line_y)

        # Header text position - slightly above the line
        header_y = line_y + 5
        header_font = "NotoSerifDisplay-Italic"
        header_font_size = 10

        # Set font and draw header text
        c.setFont(header_font, header_font_size)
        c.drawString(self.margin / 2, header_y, carry.title)  # Left-aligned title
        c.drawRightString(
            self.width - self.margin / 2, header_y, carry.finish
        )  # Right-aligned finish

    def _draw_page_footer(self, c):
        """
        Draw the page footer with page number and horizontal line

        Args:
            c (canvas): The ReportLab canvas to draw on
        """
        # Calculate positions
        line_y = 0.75 * self.margin
        page_number_y = line_y - 12  # 12 points below the line

        # Draw short horizontal line
        line = HorizontalLine.HorizontalLine(width=2 * self.margin, thickness=1)
        line.drawOn(c, self.width / 2 - self.margin, line_y)

        # Draw page number
        c.setFont("AndaleMono", 12)
        c.drawCentredString(self.width / 2, page_number_y, f"{self.page:02}")

    def _create_background_rectangle(self, c, color):
        # Calculate the positions for the rectangle (1/3 to 2/3 of height)
        y_bottom = self.height / 5 + 20  # 1/3 from bottom
        y_top = 4 * self.height / 5 + 20  # 2/3 from bottom

        # Save the current graphics state
        c.saveState()

        # To put this at the lowest z-index, we need to draw it first
        c.setFillColor(color)
        c.rect(0, y_bottom, self.width, y_top - y_bottom, fill=1, stroke=0)

        # Restore the graphics state
        c.restoreState()

    def _add_carry_qr(self, c, carry_name):
        # Load the image
        path = qr_utils.generate_qr(carry_name)
        img = ImageReader(path)
        img_width, img_height = img.getSize()

        # Define image dimensions for the square image
        # For this example, we'll make the image take up 20% of the page width
        image_size = self.width * 0.2

        # Calculate position for bottom right corner
        x_position = (
            self.width - image_size - 0.75 * self.margin
        )  # 10 points padding from right edge
        y_position = 0.75 * self.margin  # 10 points padding from bottom edge

        # Draw the image
        c.drawImage(
            path,
            x_position,
            y_position,
            width=image_size,
            height=image_size,
            preserveAspectRatio=True,
        )

    def _create_tutorial_pages_for_carry(self, c, carry):
        """
        Generate pages for the picture tutorial of the carry

        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information

        Returns:
            bool: True if pages were created successfully, False otherwise
        """
        # Get images from bucket
        results = db_utils.get_tutorial_steps_by_carry(carry.name)["data"]
        urls = [carry["url"] for carry in results]

        # Calculate page layout
        num_pages = self._calculate_pages_needed(urls)
        image_width, image_height, gap_x = self._calculate_grid_layout()

        # Create pages with grid layout
        for page_index in range(num_pages):
            self.page += 1
            c.showPage()
            self._create_tutorial_grid_page(
                c, urls, page_index, carry, image_width, image_height, gap_x
            )
            # Draw header and footer
            self._draw_page_header(c, carry, self.height - self.margin)
            self._draw_page_footer(c)

        # Add blank page if needed to maintain even number of pages
        if num_pages % 2 == 0:
            c.showPage()
            self.page += 1
            self._draw_page_footer(c)

    def _create_cover_page_for_carry(self, c, carry):
        """
        Generate a single cover page for a carry on the given canvas.

        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information

        Returns:
            bool: True if page was created successfully, False otherwise
        """
        self._create_background_rectangle(c, colors_utils.BOOKRECT)

        # Add background and overlay
        image_path = os.path.join("covers", f"{carry.name}.svg")

        w = (self.width - 2 * self.margin) * 0.6
        h = (self.height - 2 * self.margin) * 0.6
        x = (self.width - 200) / 2 + self.margin
        y = (self.height - 350) / 2
        self._draw_background_image(c, image_path, colors_utils.BOOKCOVER, w, h, x, y)

        # Add text content
        self._add_title(
            c,
            carry,
            text_color=colors_utils.LIGHTBLACK,
            frame_height=self.height / 3 - self.margin,
        )

        # Add horizontal line and mmposition
        self._add_secondary_info(c, carry)

        self._add_size(c, carry, text_color=colors_utils.LIGHTBLACK)

        # Add page number
        self._add_page(c)

        # Add QR
        self._add_carry_qr(c, carry.name)

    def _add_secondary_info(self, c, carry):
        """
        Add the horizontal line and the page number (mmposition) under the line.

        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing mmposition
        """
        line_y = 1 * self.margin
        line = HorizontalLine.HorizontalLine(
            width=self.width - 2 * self.margin - 20, thickness=1
        )
        line.drawOn(c, self.margin, line_y)

        difficulty_text_y = line_y + 12
        c.setFont("Poppins-Light", 14)
        c.drawString(self.margin, difficulty_text_y, f"{carry.difficulty}")

        # Page number under the line
        mmposition_text_y = line_y + 36
        c.setFont("Poppins-Light", 14)
        c.drawString(self.margin, mmposition_text_y, f"{carry.mmposition}")

    def create_combined_pdf(self, output_path, output_filename, carries):
        """
        Generate a combined PDF with cover pages for all carries.

        Args:
            output_path (str): Directory where the PDF will be saved
            output_filename (str): Name of the output PDF file
            carries (list): List of carry objects

        Returns:
            bool: True if PDF was created successfully, False otherwise
        """
        # Create full output path
        os.makedirs(output_path, exist_ok=True)
        output_full_path = os.path.join(output_path, output_filename)

        # Create canvas for the combined PDF
        c = canvas.Canvas(output_full_path, pagesize=self.page_size)

        # For each carry, create a page
        for i, carry in enumerate(carries):
            # Generate page content
            print(f"-Generate {carry.name}")
            self.page += 1
            self._create_cover_page_for_carry(c, carry)
            self._create_tutorial_pages_for_carry(c, carry)

            # If there are more carries, add a new page
            if i < len(carries) - 1:
                c.showPage()

        if os.path.exists("qrcodes"):
            # Remove the folder and all of its contents
            shutil.rmtree("qrcodes")

        # Save the PDF
        c.save()
        print(f"Combined PDF successfully created: {output_full_path}")
