def normalize_name(name):
    return name.strip()


def first_name(first, last):
    return normalize_name(first)

def last_name(first, last):
    return normalize_name(last)

def display_name(first, last):
    return first_name(first, last) + " " + last_name(first, last)
