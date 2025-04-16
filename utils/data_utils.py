# Font configuration
FINISHES = [
    "tied tibetan",
    "knotless tibetan",
    "tied in front",
    "buleria",
    "CCCB",
    "tied under bum",
    "shoulder to shoulder with a ring",
    "shoulder to shoulder knotless",
    "shoulder to shoulder",
    "with a ring",
    "candy cane chest belt",
    "with a pond finish",
    "with a sweetheart chest pass",
    "tied at shoulder",
    "with a xena finish",
    "strangleproof",
    "with a lexi twist",
    "with spread passes",
    "knotless tibetan",
    "with a waist band and chest belt",
    "with a celtic knot",
    "with a lacuna finish",
    "with waist band and chest belt",
    "with 2 rings",
    "single pocket",
    "separate pockets",
    "with a Date night or Goddess Finish",
    "Armpit to Shoulder",
    "with a Rainer's Heart",
    "with a Bandeau Bikini Finish",
    "with a Ruckless Bikini Finish",
    "knotless",
    "sweetheart",
]


class Carry:
    def __init__(self, name, longtitle, mmposition, position, size):
        self.name = name
        self.title, self.finish = split_title(longtitle)
        self.mmposition = format_mmposition(mmposition)
        self.position = format_position(position)
        self.size = format_size(size)

def split_title(title: str):
    title_lower = title.lower()

    for finish in FINISHES:
        finish_lower = finish.lower()

        if finish_lower in title_lower:
            index = title_lower.index(finish_lower)
            before = title[:index]
            after = title[index + len(finish):]
            return before, finish

    return title, ""

def format_size(size: int):
    if size == 0:
        return "BASE"

    return f"BASE {size}"

def format_position(position: str):
    return f"{position.upper()} CARRY"

def format_mmposition(mmposition: int):
    return "Starts 1 DH off centre"