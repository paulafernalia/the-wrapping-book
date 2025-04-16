from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import logging
from utils import fonts
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CoverPageGenerator:
    """Class for generating PDF cover pages with background images and formatted text."""

    def __init__(self, font_config, page_size=A4, margin=inch, text_color=(51 / 255, 51 / 255, 51 / 255)):
        """
        Initialize the cover page generator with basic settings.
        
        Args:
            page_size (tuple): Width and height of the page
            margin (float): Margin size in points
            text_color (tuple): RGB colour for all text
            font_config (dict): Dictionary with keys 'title', 'subtitle', 'size',
                               each containing a dict with 'name' and 'path'
        """
        self.page_size = page_size
        self.width, self.height = page_size
        self.margin = margin
        self.registered_fonts = set()
        self.text_color = text_color

        # Register fonts
        for font_info in font_config:
            self._register_font(font_info['name'], font_info['path'])
        
    
    def _register_font(self, font_name, font_path):
        """
        Register a font for use in the PDF.
        
        Args:
            font_name (str): Name to refer to the font
            font_path (str): Path to the font file
            
        Returns:
            bool: True if font was registered successfully, False otherwise
        """
        if font_name in self.registered_fonts:
            return True
            
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            self.registered_fonts.add(font_name)
            return True
        except Exception as e:
            logger.error(f"Failed to register font {font_name}: {e}")
            return False
    
    def _draw_background_image(self, c, image_path, opacity=0.5):
        """
        Draw a background image with a translucent overlay.
        
        Args:
            image_path (str): Path to the background image
            opacity (float): Opacity of the white overlay (0-1)
        """
        try:
            img = ImageReader(image_path)
            img_width, img_height = img.getSize()

            # Calculate the maximum area within margins (90% of available space)
            max_width = (self.width - 2 * self.margin) * 0.9
            max_height = (self.height - 2 * self.margin) * 0.9

            # Preserve aspect ratio
            ratio = min(max_width / img_width, max_height / img_height)
            new_width = img_width * ratio
            new_height = img_height * ratio

            # Center image within the margins
            x = (self.width - new_width) / 2
            y = (self.height - new_height) / 2

            c.drawImage(img, x, y, width=new_width, height=new_height, mask='auto')

            # Add translucent overlay
            c.saveState()
            c.setFillColorRGB(1, 1, 1, alpha=opacity)  # white with specified opacity
            c.rect(self.margin, self.margin, 
                          self.width - 2 * self.margin, 
                          self.height - 2 * self.margin, 
                          fill=1, stroke=0)
            c.restoreState()
        except Exception as e:
            logger.error(f"Failed to load or draw image: {e}")
    
    def _add_text_content(self, c, title, subtitle, size_text):
        """
        Add formatted text to the cover page.
        
        Args:
            title (str): Main title text
            subtitle (str): Subtitle text
            size_text (str): Size information text
            title_font (str): Font name for title
            subtitle_font (str): Font name for subtitle
            size_font (str): Font name for size text
        """
        # Setup paragraph styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='NotoSerifDisplay-Medium',
            fontSize=60,
            textColor=self.text_color,
            alignment=0,
            leading=60,
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName='NotoSerifDisplay-Italic',
            fontSize=32,
            textColor=self.text_color,
            alignment=0,
            leading=22,
        )
        size_style = ParagraphStyle(
            'SizeStyle',
            parent=styles['Normal'],
            fontName='Poppins-Regular',
            fontSize=32,
            textColor=self.text_color,
            alignment=0,
            leading=22,
        )

        # Create Paragraphs
        title_paragraph = Paragraph(title, title_style)
        subtitle_paragraph = Paragraph(subtitle, subtitle_style)
        size_paragraph = Paragraph(size_text, size_style)

        # Define frame height for text content (adjust as needed based on text length)
        text_block_height = 500

        # Create a frame for text positioning
        frame = Frame(
            self.margin,
            self.margin,  # Bottom margin
            self.width - 2 * self.margin,
            text_block_height,
            showBoundary=0  # No visual boundary
        )

        # Add content to the frame
        c.saveState()
        frame.addFromList([size_paragraph, Spacer(1, 70), 
                          title_paragraph, Spacer(1, 20), 
                          subtitle_paragraph], c)
        c.restoreState()
    
    def create_cover_page(self, output_path, carryid, title, subtitle, size_text, image_path):
        """
        Generate a complete cover page PDF.
        
        Args:
            output_path (str): Path where the PDF will be saved
            carryid (str): Name of the carry in the db
            title (str): Main title text
            subtitle (str): Subtitle text
            size_text (str): Size information text
            image_path (str): Path to background image
            
        Returns:
            bool: True if page was created successfully, False otherwise
        """
        try:
            # Create canvas
            output_full_path = os.path.join(output_path, f"cover_{carryid}.pdf")
            c = canvas.Canvas(output_full_path, pagesize=self.page_size)
            
            # Add background and overlay
            self._draw_background_image(c, image_path)
            
            # Add text content
            self._add_text_content(c, title, subtitle, size_text)
            
            # Save the PDF
            c.save()
            logger.info(f"Cover page successfully created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create cover page: {e}")
            return False


def main():
    """Example usage of the CoverPageGenerator class."""
    # Create generator and cover page
    generator = CoverPageGenerator(font_config=fonts.FONTCONFIG)
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