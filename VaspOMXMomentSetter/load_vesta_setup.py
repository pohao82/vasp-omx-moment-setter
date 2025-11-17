from pathlib import Path
import os

def load_vesta_colors():

    current_dir = Path(__file__).parent

    filepath = current_dir / 'elements.ini'

    """
    Parses VESTA's element.ini file to create a color map.
    Returns a dictionary mapping element symbols to 'rgb(r,g,b)' strings.
    """
    color_map = {}
    radii_dict = {}
    if not os.path.exists(filepath):
        return color_map # Return empty map if file doesn't exist

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith(';'):
                continue

            parts = line.split()
            try:
                symbol = parts[1]
                radii = parts[3]
                r, g, b = parts[5], parts[6], parts[7]
                # limit the maximum to 0.99 to avoid display issues in scatter3d
                r, g, b = min(float(r), 0.99), min(float(g), 0.99), min(float(b), 0.99)
                color_map[symbol] = f'rgb({r},{g},{b})'
                radii_dict[symbol] = radii
            except (IndexError, ValueError):
                # Ignore malformed lines
                continue

    return color_map, radii_dict

