from utils import colors_utils
from reportlab.platypus import Flowable


class HorizontalLine(Flowable):
    def __init__(self, width, thickness=0.5, color=colors_utils.LIGHTBLACK):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.height = thickness  # Minimal height to reserve space
        self.color = color

    def draw(self):
        self.canv.setLineWidth(self.thickness)
        self.canv.setStrokeColor(self.color)  # Set the color
        self.canv.line(0, 0, self.width, 0)
        # Reset to default color after drawing (optional but good practice)
        self.canv.setStrokeColor(colors_utils.LIGHTBLACK)
