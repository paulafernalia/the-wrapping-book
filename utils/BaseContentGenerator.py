from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import requests
import os
import io
from PIL import Image
from utils import image_utils
from utils import qr_utils
from utils import fonts
from utils import colors_utils


class BaseContentGenerator:
    """Class for generating PDF cover pages with background images and formatted text."""

    def __init__(self, page_size=A4, margin=inch):
        """
        Initialize the cover page generator with basic settings.
        
        Args:
            page_size (tuple): Width and height of the page
            margin (float): Margin size in points
                               each containing a dict with 'name' and 'path'
        """
        self.page_size = page_size
        self.width, self.height = page_size
        self.margin = margin
        self.registered_fonts = set()
        self.page = 0

        # Register fonts
        for font_info in fonts.FONTCONFIG:
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

    
    def _draw_background_image(self, c, image_path, color, w, h, x, y):
        """
        Draw a background image with a translucent overlay.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            image_path (str): Path to the background image
        """
        hex_color = colors_utils.rgb_to_hex(color)
        img = image_utils.transform_svg_cover(os.path.join(image_path), hex_color)

        img_width, img_height = img.getSize()            

        # Preserve aspect ratio
        ratio = min(w / img_width, h / img_height)
        new_width = img_width * ratio
        new_height = img_height * ratio            

        c.drawImage(img, x, y, width=new_width, height=new_height, mask='auto')


    def _add_page(self, c):
        # Page number under the line
        page_number_y = self.height - self.margin
        c.setFont("Poppins-Regular", 14)
        c.drawRightString(self.width - self.margin, page_number_y, f"{self.page}")
    
    def _add_title(self, c, carry, text_color, frame_height):
        """
        Add formatted text to the cover page.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing title, finish, position, size, mmposition, and name
        """
        # Create Paragraphs
        title_paragraph, subtitle_paragraph = self._create_title_content(carry, text_color)

        # Define frame height for text content (adjust as needed based on text length)
        text_block_height = 300

        # Create a frame for text positioning
        frame = Frame(
            self.margin - 10,
            frame_height,
            self.width - 2 * self.margin,
            text_block_height,
            showBoundary=0  # No visual boundary
        )

        # Add content to the frame
        c.saveState()
        frame.addFromList([
            title_paragraph,
            Spacer(1, 25), 
            subtitle_paragraph,   
        ], c)
        c.restoreState()


    def _create_title_content(self, carry, text_color):
        """
        Create the paragraphs for the title, subtitle, size, and mmposition.

        Args:
            carry: Object containing title, finish, position, size, mmposition, and name
            title_style, subtitle_style, size_style, mmposition_style: Styles for the paragraphs
        
        Returns:
            tuple: The paragraphs for title, subtitle, size, and mmposition
        """
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='PlayfairDisplay',
            fontSize=72,
            textColor=text_color,
            alignment=0,
            leading=60,
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName='NotoSerifDisplay-Italic',
            fontSize=32,
            textColor=text_color,
            alignment=0,
            leading=22,
        )

        size_style = ParagraphStyle(
            'SizeStyle',
            parent=styles['Normal'],
            fontName='Poppins-Light',
            fontSize=20,
            textColor=text_color,
            alignment=0,
            leading=22,
        )

        title_paragraph = Paragraph(carry.title, title_style)
        subtitle_paragraph = Paragraph(carry.finish, subtitle_style)

        return title_paragraph, subtitle_paragraph


    def _add_size(self, c, carry, text_color):
        # Set text color
        c.setFillColor(text_color)
        
        # Add the text
        sizepos_text_y = self.height * 2.15 / 3
        c.setFont("Poppins-Light", 20)
        c.drawString(self.margin, sizepos_text_y, f"{carry.position} | {carry.size}")


    def _calculate_pages_needed(self, urls):
        """
        Calculate how many pages needed for the tutorial images
        
        Args:
            urls (list): List of image URLs
            
        Returns:
            int: Number of pages needed
        """
        grid_size = 9  # 3x3 grid
        num_pages = len(urls) // grid_size
        if len(urls) % grid_size > 0:
            num_pages += 1
        return num_pages

    def _calculate_grid_layout(self):
        """
        Calculate dimensions for the 3x3 image grid
        
        Returns:
            tuple: (image_width, image_height, gap_x)
        """
        gap_x = 20  # Horizontal gap between images
        available_width = self.width - self.margin
        available_height = self.height - (2 * self.margin)
        
        image_width = (available_width - (2 * gap_x)) / 3  # Width for each image in the grid
        image_height = available_height / 3  # Height for each image in the grid
        
        return image_width, image_height, gap_x


    def _download_and_place_image(self, c, url, x, y, width, height):
        """
        Download an image from URL and place it on the canvas
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            url (str): URL of the image to download
            x (float): X-position on the canvas
            y (float): Y-position on the canvas
            width (float): Width to render the image
            height (float): Height to render the image
        """
        # Download image
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Process image data
        img_data = io.BytesIO(response.content)
        img = Image.open(img_data).convert('RGB')
        
        # Save to buffer for ReportLab
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        # Draw image on canvas
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, x, y, width=width, height=height, preserveAspectRatio=True)
            

    def _create_tutorial_grid_page(self, c, urls, page_index, carry, image_width, image_height, gap_x):
        """
        Create a single tutorial page with images arranged in a 3x3 grid
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            urls (list): List of all image URLs
            page_index (int): Current page index (zero-based)
            carry: Object containing carry information
            image_width (float): Width for each image
            image_height (float): Height for each image
            gap_x (float): Horizontal gap between images
        """
        # Start a new page and increment counter
        # Page layout
        line_y = self.height - self.margin
        
        # Calculate which images to show on this page
        grid_size = 9  # 3x3 grid
        start_idx = page_index * grid_size
        end_idx = min(start_idx + grid_size, len(urls))
        
        # Place each image in the grid
        for j in range(start_idx, end_idx):
            i = j % grid_size  # Local index within the grid (0-8)
            
            # Calculate grid position
            row = 2 - (i // 3)  # Convert to 0-indexed rows from top to bottom
            col = i % 3         # Column index (0-2)
            
            # Calculate coordinates
            x = self.margin / 2 + (col * (image_width + gap_x))
            y = self.margin + (row * image_height)
            
            # Place the image
            self._download_and_place_image(c, urls[j], x, y, image_width, image_height)