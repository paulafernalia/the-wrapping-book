from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import os
from utils import colors_utils
from utils import db_utils
from utils import image_utils
from utils import BaseContentGenerator
from utils import HorizontalLine


SIGNATURE = "@PAULAFERMINCUETO"


class PostGenerator(BaseContentGenerator.BaseContentGenerator):
    def __init__(self, output_dir, carry, page_size=(3 * 210, 3 * 260), margin=inch):
        super().__init__(page_size=page_size)
        self.carry = carry
        self.output_dir = output_dir

        if self.carry.position == "BACK CARRY":
            self.cover_line_color = colors_utils.BACKPOSTLINE
            self.cover_back_color = colors_utils.BACKPOSTBACKGROUND
            self.title_text_color = "white"
        else:
            self.cover_line_color = colors_utils.FRONTPOSTLINE
            self.cover_back_color = colors_utils.FRONTPOSTBACKGROUND
            self.title_text_color = "black"

    def generate_post(self):
        # Create full output path
        os.makedirs(self.output_dir, exist_ok=True)
        output_full_path = os.path.join(self.output_dir, f"{self.carry.name}.pdf")

        # Create canvas for the combined PDF
        c = canvas.Canvas(output_full_path, pagesize=self.page_size)

        # Start page as 1
        self._create_cover_page(c)

        c.save()
        print(f"Post PDF successfully created: {output_full_path}")

        # Convert pdf to pngs
        image_utils.pdf_to_pngs(output_full_path, self.output_dir)

        # Delete pdf when done
        if os.path.exists(output_full_path):
            os.remove(output_full_path)


    def _create_cover_page(self, c):
        """
        Generate a single cover page for a carry on the given canvas.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information
            
        Returns:
            bool: True if page was created successfully, False otherwise
        """
        # Add background and overlay
        image_path = os.path.join("covers", f"{self.carry.name}.svg")

        # Set background color
        self._set_background_color(c)

        w = (self.width - 2 * self.margin) * 1
        h = (self.height - 2 * self.margin) * 1
        x = (self.width) / 2 - 3 * self.margin
        y = (self.height) / 2 - 4.5 * self.margin
        self._draw_background_image(c, image_path, self.cover_line_color, w, h, x, y)
        
        # # Add text content
        self._add_title(
            c, self.carry, text_color=self.title_text_color, frame_height=2 * self.margin
        )

        # # Draw border rectangle
        self._draw_inset_rectangle(c)

        self._add_signature(c)

        self._add_size(c, self.carry, text_color=self.title_text_color)

        self._create_tutorial_pages_for_carry(c)

    def _create_tutorial_pages_for_carry(self, c):
        """
        Generate pages for the picture tutorial of the carry
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information
            
        Returns:
            bool: True if pages were created successfully, False otherwise
        """
        # Get images from bucket
        results = db_utils.get_tutorial_steps_by_carry(self.carry.name)['data']
        urls = [step["url"] for step in results]
        
        # Calculate page layout
        num_pages = self._calculate_pages_needed(urls)
        image_width, image_height, gap_x = self._calculate_grid_layout()
        
        # Create pages with grid layout
        for page_index in range(num_pages):
            self.page += 1
            c.showPage()
            self._create_tutorial_grid_page(c, urls, page_index, self.carry, image_width, image_height, gap_x)
            # Draw header and footer
            self._draw_page_header(c, self.carry, self.height - self.margin)
            self._draw_page_footer(c)

    def _draw_page_header(self, c, carry, line_y):
        """
        Draw the page header with title, finish text and horizontal line
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information
            line_y: Y-position for the horizontal line
        """
        # Draw horizontal line at the top
        # line = HorizontalLine(width=self.width - self.margin, thickness=1)
        # line.drawOn(c, self.margin / 2, line_y)
        
        # Header text position - slightly above the line
        header_y = line_y + 30
        header_font = "NotoSerifDisplay-Italic"
        header_font_size = 14
        
        # Set font and draw header text
        c.setFont(header_font, header_font_size)
        c.setFillColor(colors_utils.BACKPOSTLINE)
        c.drawString(self.margin / 2, header_y, carry.title)  # Left-aligned title
        c.drawRightString(self.width - self.margin / 2, header_y, carry.finish)  # Right-aligned finish

        # Draw short horizontal line
        line = HorizontalLine.HorizontalLine(
            width=self.width / 2 - self.margin / 2, thickness=1, color=colors_utils.BACKPOSTLINE
        )
        line.drawOn(c, 0, self.height - self.margin / 1.5)
        line.drawOn(c, self.width / 2 + self.margin / 2, self.height - self.margin / 1.5)

        page_number_y = self.height - 55
        c.setFillColor(colors_utils.BACKPOSTLINE)
        c.setFont("AndaleMono", 32)
        c.drawCentredString(self.width / 2, page_number_y, f"{self.page:02}")

    def _draw_page_footer(self, c):
        """
        Draw the page footer with page number and horizontal line
        
        Args:
            c (canvas): The ReportLab canvas to draw on
        """
        # Calculate positions
        line_y = 0.75 * self.margin
        
        # Draw short horizontal line
        line = HorizontalLine.HorizontalLine(width=2 * self.margin, thickness=1, color=colors_utils.BACKPOSTLINE)
        line.drawOn(c, self.width / 2 - self.margin, line_y)

        # Draw signature
        c.setFont("Poppins-Light", 12)
        c.setFillColor(colors_utils.BACKPOSTLINE)
        c.drawCentredString(self.width / 2, line_y - 16 , SIGNATURE)


    def _add_signature(self, c):
        line_y = 1 * self.margin
        line = HorizontalLine.HorizontalLine(width=self.width - 2 * self.margin - 20, thickness=1)
        line.drawOn(c, self.margin, line_y)

        signature = SIGNATURE
        # author = "@GISELLEBAUMET"
        author = None
        if author:
            insta_handle_y = line_y + 36
            author_y = line_y + 12

            c.setFont("Poppins-Regular", 18)
            c.setFillColor(colors_utils.LIGHTBLACK)
            c.drawString(self.margin, insta_handle_y, signature)
            
            c.setFont("Poppins-Regular", 14)
            c.setFillColor(colors_utils.LIGHTBLACK)
            c.drawString(self.margin, author_y, f"based on video tutorials by {author}")
        else:
            insta_handle_y = line_y + 12

            c.setFont("Poppins-Light", 18)
            c.setFillColor(colors_utils.LIGHTBLACK)
            c.drawString(self.margin, insta_handle_y, signature)

    def _set_background_color(self, c):
        # Save the current graphics state
        c.saveState()
        
        # Set the fill color for the background
        c.setFillColor(self.cover_back_color)
        
        # Draw the background rectangle
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # Restore the graphics state
        c.restoreState()


    def _draw_inset_rectangle(self, c):
        """
        Draw an inset rectangle around the page.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
        """
        # Calculate rectangle dimensions
        width = self.width - 1 * self.margin
        height = self.height - 1 * self.margin

        c.setLineWidth(2) 

        r, g, b = self.cover_line_color
        c.setStrokeColorRGB(r, g, b)

        # Draw rectangle
        c.rect(0.5 * inch, 0.5 * inch, width, height)
