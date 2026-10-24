"""Shared config for the Canggu business scraper. Stdlib only."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # repo root: mafa-scraper/
OUT_DIR = os.environ.get("CANGGU_OUT", os.path.join(ROOT, "out"))

# Entire Canggu bbox. Membership = inside this box. No distance math.
BBOX = {
    "min_lat": -8.68,
    "max_lat": -8.60,
    "min_lng": 115.10,
    "max_lng": 115.18,
}

# ~3km cells -> 3x3 grid over the bbox. Keeps search count sane.
CELL_STEP = 0.03

KEYWORDS = [
    "cafe", "restaurant", "villa", "hotel", "guest house",
    "salon", "spa", "gym", "yoga", "coworking",
    "surf shop", "minimarket", "laundry", "clinic", "tattoo",
    "kos", "kost", "kontrakan", "penginapan", "indekos",
]

RAW_JSONL = os.path.join(OUT_DIR, "gmaps_raw.jsonl")
DETAIL_JSONL = os.path.join(OUT_DIR, "gmaps_detail.jsonl")
WEB_JSONL = os.path.join(OUT_DIR, "webcheck.jsonl")
CSV_OUT = os.path.join(OUT_DIR, "canggu_businesses.csv")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def in_bbox(lat, lng):
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return False
    return (BBOX["min_lat"] <= lat <= BBOX["max_lat"]
            and BBOX["min_lng"] <= lng <= BBOX["max_lng"])
