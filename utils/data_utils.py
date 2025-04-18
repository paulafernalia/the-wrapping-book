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


MMPOSITIONS={
    -1: "Follow tutorial for MM start position",
    0: "MM starts centred",
    6: "MM starts 0.5 DH off centre",
    1: "MM starts 1 DH off centre",
    7: "MM starts 1.5 DH off centre",
    2: "MM starts 2 DH off centre",
    3: "MM starts centred on your chest",
    4: "MM starts centred on your back",
    5: "MM starts under your armpit",
}

DIFFICULTY={
    1: "Beginner",
    2: "Beginner+",
    3: "Intermediate",
    4: "Advanced",
    5: "Guru",
}


class Carry:
    def __init__(self, name, longtitle, mmposition, position, size, difficulty):
        self.name = name
        self.title, self.finish = split_title(longtitle)
        self.mmposition = format_mmposition(mmposition)
        self.position = format_position(position)
        self.size = format_size(size)
        self.difficulty = format_difficulty(difficulty)

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

    if size > 0:
        return f"BASE + {size}"

    return f"BASE {size}"

def format_difficulty(difficulty: int):
    diff_int = round(difficulty)
    return f"Difficulty: {DIFFICULTY[diff_int]}"

def format_position(position: str):
    return f"{position.upper()} CARRY"

def format_mmposition(mmposition: int):
    return MMPOSITIONS[mmposition]
