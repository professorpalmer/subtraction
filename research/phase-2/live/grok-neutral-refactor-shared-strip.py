def normalize_name(name):
    return name.strip()

def display_name(first, last):
    return normalize_name(first) + " " + normalize_name(last)
