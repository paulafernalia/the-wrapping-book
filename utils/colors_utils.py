LIGHTBLACK = (51 / 255, 51 / 255, 51 / 255)

FRONTPOSTBACKGROUND = (226 / 255, 218 / 255, 219 / 255)
FRONTPOSTLINE =  (178 / 255, 147 / 255, 146 / 255)

BACKPOSTBACKGROUND = (148 / 255, 136 / 255, 114 / 255)
BACKPOSTLINE =  (100 / 255, 87 / 255, 69 / 255)

BOOKLINECOLOR = (100 / 255, 87 / 255, 69 / 255)

def rgb_to_hex(rgb):
    """
    Convert an RGB tuple with values from 0-1 to a hex string (e.g., '645745').
    """
    return ''.join(f'{int(255 * c):02x}' for c in rgb)