from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import logging
import os
from utils import image_utils
from reportlab.platypus import Flowable


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HorizontalLine(Flowable):
    def __init__(self, width, thickness=0.5):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.height = thickness  # Minimal height to reserve space

    def draw(self):
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


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


    def _draw_inset_rectangle(self, c):
        """
        Draw an inset rectangle around the page.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
        """
        # Calculate rectangle dimensions
        width = self.width - 1 * self.margin
        height = self.height - 1 * self.margin

        c.setLineWidth(1) 

        # r, g, b = 229/255, 219/255, 219/255
        r, g, b = 51/255, 51/255, 51/255
        c.setStrokeColorRGB(r, g, b)

        # Draw rectangle
        c.rect(0.5 * inch, 0.5 * inch, width, height)
    
    def _draw_background_image(self, c, image_path, opacity=0.5):
        """
        Draw a background image with a translucent overlay.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            image_path (str): Path to the background image
            opacity (float): Opacity of the white overlay (0-1)
        """
        try:
            # grey_image_path = image_utils.convert_to_greyscale(image_path)
            # img = ImageReader(grey_image_path)
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
    
    def _add_text_content(self, c, carry):
        """
        Add formatted text to the cover page.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing title, finish, position, size, mmposition, and name
        """
        # Setup paragraph styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='PlayfairDisplay',
            fontSize=72,
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
            fontName='Poppins-Light',
            fontSize=28,
            textColor=self.text_color,
            alignment=0,
            leading=22,
        )
        mmposition_style = ParagraphStyle(
            'SizeStyle',
            parent=styles['Normal'],
            fontName='Poppins-Light',
            fontSize=18,
            textColor=self.text_color,
            alignment=0,
            leading=22,
        )

        # Create Paragraphs
        title_paragraph = Paragraph(carry.title, title_style)
        subtitle_paragraph = Paragraph(carry.finish, subtitle_style)
        size_paragraph = Paragraph(f"{carry.position}   |   {carry.size}", size_style)
        mmposition_paragraph = Paragraph(f"{carry.mmposition}", mmposition_style)

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
        frame.addFromList([
            size_paragraph,
            Spacer(1, 70), 
            title_paragraph,
            Spacer(1, 20), 
            subtitle_paragraph,   
            Spacer(1, 80),  
            mmposition_paragraph,     
            Spacer(1, 5),   
            HorizontalLine(width=self.width - 2 * self.margin - 20, thickness=1),
        ], c)
        c.restoreState()
    
    def create_cover_page_for_carry(self, c, carry):
        """
        Generate a single cover page for a carry on the given canvas.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information
            
        Returns:
            bool: True if page was created successfully, False otherwise
        """
        try:
            # Add background and overlay
            image_path = os.path.join("cover_pictures", f"{carry.name}.png")
            self._draw_background_image(c, image_path)
            
            # Add text content
            self._add_text_content(c, carry)

            # Draw border rectangle
            self._draw_inset_rectangle(c)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create cover page for {carry.name}: {e}")
            return False
    
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
        try:
            # Create full output path
            output_full_path = os.path.join(output_path, output_filename)
            
            # Create canvas for the combined PDF
            c = canvas.Canvas(output_full_path, pagesize=self.page_size)
            
            # For each carry, create a page
            for i, carry in enumerate(carries):
                # Generate page content
                success = self.create_cover_page_for_carry(c, carry)
                
                if not success:
                    logger.warning(f"Failed to add page for carry {carry.name}")
                
                # If there are more carries, add a new page
                if i < len(carries) - 1:
                    c.showPage()
            
            # Save the PDF
            c.save()
            logger.info(f"Combined PDF successfully created: {output_full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create combined PDF: {e}")
            return False