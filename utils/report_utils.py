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
from utils import colors_utils
from utils import db_utils
from utils import qr_utils
from reportlab.platypus import Flowable
from reportlab.lib import colors


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

    def __init__(self, font_config, page_size=A4, margin=inch, text_color=colors_utils.LIGHTBLACK):
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
        r, g, b = colors_utils.LIGHTBLACK
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
            max_width = (self.width - 2 * self.margin) * 0.6
            max_height = (self.height - 2 * self.margin) * 0.6

            # Preserve aspect ratio
            ratio = min(max_width / img_width, max_height / img_height)
            new_width = img_width * ratio
            new_height = img_height * ratio

            # Center image within the margins
            x = (self.width - new_width) / 2 + self.margin
            y = (self.height - new_height) / 2

            c.drawImage(img, x, y, width=new_width, height=new_height, mask='auto')

        except Exception as e:
            logger.error(f"Failed to load or draw image: {e}")


    def _add_page(self, c):
        # Page number under the line
        page_number_y = self.height - self.margin
        c.setFont("Poppins-Regular", 14)
        c.drawRightString(self.width - self.margin, page_number_y, f"{self.page}")
    
    def _add_text_content(self, c, carry):
        """
        Add formatted text to the cover page.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing title, finish, position, size, mmposition, and name
        """
        # Create Paragraphs
        title_paragraph, subtitle_paragraph = self._create_title_text(carry)

        # Define frame height for text content (adjust as needed based on text length)
        text_block_height = 475

        # Create a frame for text positioning
        frame = self._create_text_frame(text_block_height)

        # Add content to the frame
        self._add_title(c, frame, title_paragraph, subtitle_paragraph)

        # Add horizontal line and mmposition
        self._add_secondary_info(c, carry)

        # Add page number
        self._add_page(c)


    def _create_title_text(self, carry):
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
            fontSize=20,
            textColor=self.text_color,
            alignment=0,
            leading=22,
        )

        title_paragraph = Paragraph(carry.title, title_style)
        subtitle_paragraph = Paragraph(carry.finish, subtitle_style)

        return title_paragraph, subtitle_paragraph

    def _create_text_frame(self, text_block_height):
        """
        Create the frame for text positioning on the page.
        
        Args:
            text_block_height: Height for the text block
        
        Returns:
            Frame: The created frame for text content
        """
        frame = Frame(
            self.margin - 10,
            self.margin,  # Bottom margin
            self.width - 2 * self.margin,
            text_block_height,
            showBoundary=0  # No visual boundary
        )
        return frame

    def _add_title(self, c, frame, title_paragraph, subtitle_paragraph):
        """
        Add the content to the frame.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            frame (Frame): The frame where content is placed
            title_paragraph, subtitle_paragraph: The paragraphs to be added
        
        Returns:
            None
        """
        c.saveState()
        frame.addFromList([
            title_paragraph,
            Spacer(1, 25), 
            subtitle_paragraph,   
        ], c)
        c.restoreState()

    def _add_secondary_info(self, c, carry):
        """
        Add the horizontal line and the page number (mmposition) under the line.
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing mmposition
        """
        line_y = 1 * self.margin
        line = HorizontalLine(width=self.width - 2 * self.margin - 20, thickness=1)
        line.drawOn(c, self.margin, line_y)

        difficulty_text_y = line_y + 12
        c.setFont("Poppins-Light", 14)
        c.drawString(self.margin, difficulty_text_y, f"{carry.difficulty}")

        sizepos_text_y = self.height * 2.15 / 3
        c.setFont("Poppins-Light", 20)
        c.drawString(self.margin, sizepos_text_y, f"{carry.position} | {carry.size}")

        # Page number under the line
        mmposition_text_y = line_y + 36
        c.setFont("Poppins-Light", 14)
        c.drawString(self.margin, mmposition_text_y, f"{carry.mmposition}")

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
        
        # Calculate page layout
        num_pages = self._calculate_pages_needed(urls)
        image_width, image_height, gap_x = self._calculate_grid_layout()
        
        # Create temp directory
        temp_dir = "./temp_images"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create pages with grid layout
        for page_index in range(num_pages):
            self._create_tutorial_grid_page(c, urls, page_index, carry, image_width, image_height, gap_x)
        
        # Add blank page if needed to maintain even number of pages
        if num_pages % 2 == 0:
            c.showPage()
            self.page += 1
        
        return True

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

    def _draw_page_header(self, c, carry, line_y):
        """
        Draw the page header with title, finish text and horizontal line
        
        Args:
            c (canvas): The ReportLab canvas to draw on
            carry: Object containing carry information
            line_y: Y-position for the horizontal line
        """
        # Draw horizontal line at the top
        line = HorizontalLine(width=self.width - self.margin, thickness=1)
        line.drawOn(c, self.margin / 2, line_y)
        
        # Header text position - slightly above the line
        header_y = line_y + 5
        header_font = "NotoSerifDisplay-Italic"
        header_font_size = 10
        
        # Set font and draw header text
        c.setFont(header_font, header_font_size)
        c.drawString(self.margin / 2, header_y, carry.title)  # Left-aligned title
        c.drawRightString(self.width - self.margin / 2, header_y, carry.finish)  # Right-aligned finish
        
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
        line = HorizontalLine(width=2 * self.margin, thickness=1)
        line.drawOn(c, self.width / 2 - self.margin, line_y)
        
        # Draw page number
        c.setFont("AndaleMono", 12)
        c.drawCentredString(self.width / 2, page_number_y, f"{self.page:02}")

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
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
            return True
            
        except Exception as e:
            print(f"Error processing image from {url}: {e}")
            return False

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
        self.page += 1
        c.showPage()
        
        # Page layout
        line_y = self.height - self.margin
        
        # Draw header and footer
        self._draw_page_header(c, carry, line_y)
        self._draw_page_footer(c)
        
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

    def _create_background_rectangle(self, c, color=colors.lightgrey):
        # Calculate the positions for the rectangle (1/3 to 2/3 of height)
        y_bottom = self.height / 5 + 20  # 1/3 from bottom
        y_top = 4 * self.height / 5 + 20 # 2/3 from bottom
        
        # Save the current graphics state
        c.saveState()
        
        # To put this at the lowest z-index, we need to draw it first
        c.setFillColor(color)
        c.rect(0, y_bottom, self.width, y_top - y_bottom, fill=1, stroke=0)
        
        # Restore the graphics state
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
            self._create_background_rectangle(c)

            # Add background and overlay
            image_path = os.path.join("cover_pictures", f"{carry.name}.png")
            self._draw_background_image(c, image_path)
            
            # Add text content
            self._add_text_content(c, carry)

            # Draw border rectangle
            # self._draw_inset_rectangle(c)

            # Add QR
            self._add_carry_qr(c, carry.name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create cover page for {carry.name}: {e}")
            return False

    def _add_carry_qr(self, c, carry_name):
        # Load the image
        path = qr_utils.generate_qr(carry_name)
        img = ImageReader(path)
        img_width, img_height = img.getSize()
        
        # Define image dimensions for the square image
        # For this example, we'll make the image take up 20% of the page width
        image_size = self.width * 0.2
        
        # Calculate position for bottom right corner
        x_position = self.width - image_size - 0.75 * self.margin  # 10 points padding from right edge
        y_position = 0.75 * self.margin  # 10 points padding from bottom edge
        
        # Draw the image
        c.drawImage(
            path, 
            x_position, 
            y_position, 
            width=image_size, 
            height=image_size, 
            preserveAspectRatio=True
        )
    
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