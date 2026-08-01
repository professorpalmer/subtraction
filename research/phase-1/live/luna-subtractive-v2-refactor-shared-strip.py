def clean_name(value):
    return value.strip()

def display_name(first, last):
    return clean_name(first) + " " + clean_name(last)
