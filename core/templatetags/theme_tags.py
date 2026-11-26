from django import template

register = template.Library()


@register.filter
def hexrgb(value):
    """Convertit '#rrggbb' en 'r, g, b' pour color-mix / rgba."""
    fallback = "13, 110, 253"
    try:
        s = str(value).strip().lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) != 6:
            return fallback
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        return "{}, {}, {}".format(r, g, b)
    except Exception:
        return fallback
