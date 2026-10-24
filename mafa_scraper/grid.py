"""Grid cells covering the Canggu bbox."""
from .config import BBOX, CELL_STEP


def cells(step=CELL_STEP):
    lat = BBOX["min_lat"] + step / 2
    out = []
    while lat <= BBOX["max_lat"]:
        lng = BBOX["min_lng"] + step / 2
        while lng <= BBOX["max_lng"]:
            out.append((round(lat, 5), round(lng, 5)))
            lng += step
        lat += step
    return out


if __name__ == "__main__":
    for c in cells():
        print(f"{c[0]},{c[1]}")
