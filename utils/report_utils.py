from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import logging
import requests
import os
import io
from PIL import Image
from utils import image_utils
from utils import colors
from utils import db_utils
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



class BookContentGenerator:
    """Class for generating PDF cover pages with background images and formatted text."""

    def __init__(self, font_config, page_size=A4, margin=inch, text_color=colors.LIGHTBLACK):
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
        self.page = 0

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
        r, g, b = colors.LIGHTBLACK
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
            max_width = (self.width - 2 * self.margin) * 0.7
            max_height = (self.height - 2 * self.margin) * 0.7

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
        title_style, subtitle_style, size_style, mmposition_style = self._get_paragraph_styles()

        # Create Paragraphs
        title_paragraph, subtitle_paragraph, size_paragraph, mmposition_paragraph = self._create_paragraphs(carry, title_style, subtitle_style, size_style, mmposition_style)

        # Define frame height for text content (adjust as needed based on text length)
        text_block_height = 500

        # Create a frame for text positioning
        frame = self._create_text_frame(text_block_height)

        # Add content to the frame
        self._add_content_to_frame(c, frame, title_paragraph, subtitle_paragraph, size_paragraph)

        # Add horizontal line and page number
        self._add_mmposition_line(c, carry)

    def _get_paragraph_styles(self):
        """
        Setup and return the paragraph styles for title, subtitle, size, and mmposition.
        
        Returns:
            tuple: The styles for title, subtitle, size, and mmposition
        """
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
            fontSize=16,
            textColor=self.text_color,
            alignment=0,
            leading=22,
        )

        return title_style, subtitle_style, size_style, mmposition_style

    def _create_paragraphs(self, carry, title_style, subtitle_style, size_style, mmposition_style):
        """
        Create the paragraphs for the title, subtitle, size, and mmposition.

        Args:
            carry: Object containing title, finish, position, size, mmposition, and name
            title_style, subtitle_style, size_style, mmposition_style: Styles for the paragraphs
        
        Returns:
            tuple: The paragraphs for title, subtitle, size, and mmposition
        """
        title_paragraph = Paragraph(carry.title, title_style)
        subtitle_paragraph = Paragraph(carry.finish, subtitle_style)
        size_paragraph = Paragraph(f"{carry.position}   |   {carry.size}", size_style)
        mmposition_paragraph = Paragraph(f"{carry.mmposition}", mmposition_style)

        return title_paragraph, subtitle_paragraph, size_paragraph, mmposition_paragraph

    def _create_text_frame(self, text_block_height):
        """
        Create the frame for text positioning on the page.
        
        Args:
            text_block_height: Height for the text block
        
        Returns:
            Frame: The created frame for text content
        """
        frame = Frame(
            self.margin,
            self.margin,  # Bottom margin
            self.width - 2 * self.margin,
            text_block_height,
            showBoundary=0  # No visual boundary
        )
        return frame

    def _add_content_to_frame(self, c, frame, title_paragraph, subtitle_paragraph, size_paragraph):
        """
        Add the content to the frame.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            frame (Frame): The frame where content is placed
            title_paragraph, subtitle_paragraph, size_paragraph: The paragraphs to be added
        
        Returns:
            None
        """
        c.saveState()
        frame.addFromList([
            size_paragraph,
            Spacer(1, 70), 
            title_paragraph,
            Spacer(1, 20), 
            subtitle_paragraph,   
        ], c)
        c.restoreState()

    def _add_mmposition_line(self, c, carry):
        """
        Add the horizontal line and the page number (mmposition) under the line.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing mmposition
        """
        mmposition_line_y = 1.5 * self.margin
        mmposition_line = HorizontalLine(width=self.width - 2 * self.margin - 20, thickness=1)
        mmposition_line.drawOn(c, self.margin, mmposition_line_y)

        # Page number under the line
        page_number_y = mmposition_line_y + 12  # 12 points below the line
        c.setFont("Poppins-Light", 14)
        c.drawString(self.margin, page_number_y, f"{carry.mmposition}")

    def create_tutorial_pages_for_carry(self, c, carry):
        """
        Generate pages for the picture tutorial of the carry
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information
            
        Returns:
            bool: True if pages were created successfully, False otherwise
        """
        # Get images from bucket
        results = db_utils.get_tutorial_steps_by_carry(carry.name)['data']
        
        urls = [carry["url"] for carry in results]
        grid_size = 9
        num_pages = len(urls) // 9
        if len(urls) % 9 > 0:
            num_pages += 1

        temp_dir = "./temp_images"
        os.makedirs(temp_dir, exist_ok=True)

        available_width = self.width - (self.margin)
        available_height = self.height - (2 * self.margin)

        gap_x = 20
        image_width = (available_width - (2 * gap_x)) / 3
        image_height = available_height / 3

        # Download and place images
        temp_image_paths = []
        for page in range(num_pages):
            self.page += 1
            c.showPage()

            # Line position
            line_y = self.height - self.margin
            line = HorizontalLine(width=self.width - self.margin, thickness=1)
            line.drawOn(c, self.margin / 2, line_y)

            line2_y = 0.75 * self.margin
            line2 = HorizontalLine(width=2 * self.margin, thickness=1)
            line2.drawOn(c, self.width / 2 - self.margin, line2_y)

            # Page number under the line
            page_number_y = line2_y - 12  # 12 points below the line
            c.setFont("AndaleMono", 12)
            c.drawCentredString(self.width / 2, page_number_y, f"{self.page:02}")

            # Header text position
            header_y = line_y + 5  # Slightly above the line
            header_font = "NotoSerifDisplay-Italic"
            header_font_size = 10

            # Set font
            c.setFont(header_font, header_font_size)

            # Left-aligned header text
            c.drawString(self.margin / 2, header_y, carry.title)

            # Right-aligned header text
            c.drawRightString(self.width - self.margin / 2, header_y, carry.finish)
            for j in range(page * 9, (page + 1) * 9):
                if j >= len(urls):
                    break

                i = j % 9
                try:
                    # Download image
                    response = requests.get(urls[j], stream=True)
                    response.raise_for_status()  # Raise an exception for bad responses
                    
                    # Convert to ImageReader format
                    img_data = io.BytesIO(response.content)
                    img = Image.open(img_data).convert('RGB')
                    
                    # Determine image position (0,0 is bottom left in ReportLab)
                    row = 2 - (i // 3)  # Convert to 0-indexed rows from top to bottom
                    col = i % 3
                    
                    x = self.margin / 2 + (col * (image_width + gap_x))
                    y = self.margin + (row * image_height)
                    
                    # Save to memory buffer
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='JPEG')
                    img_buffer.seek(0)
                    
                    # Draw image on canvas
                    img_reader = ImageReader(img_buffer)
                    c.drawImage(img_reader, x, y, width=image_width, height=image_height, preserveAspectRatio=True)

                except Exception as e:
                    print(f"Error processing image {i} from {urls[j]}: {e}")

        if num_pages % 2 == 0:
            c.showPage()
            self.page += 1

        return True
    
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
            os.makedirs(output_path, exist_ok=True)
            output_full_path = os.path.join(output_path, output_filename)
            
            # Create canvas for the combined PDF
            c = canvas.Canvas(output_full_path, pagesize=self.page_size)
            
            # For each carry, create a page
            for i, carry in enumerate(carries):
                # Generate page content
                self.page += 1
                success = self.create_cover_page_for_carry(c, carry)
                
                if not success:
                    logger.warning(f"Failed to add page for carry {carry.name}")

                success = self.create_tutorial_pages_for_carry(c, carry)
                
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