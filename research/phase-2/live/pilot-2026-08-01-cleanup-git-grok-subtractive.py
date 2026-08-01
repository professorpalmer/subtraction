def parse_enabled(value):
    if value == "true":
        return True
    if value in {"false", "off"}:
        return False
    return bool(value)
