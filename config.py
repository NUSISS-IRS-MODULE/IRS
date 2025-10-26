import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    OPENTRIPMAP_KEY = os.getenv("OPENTRIPMAP_KEY", "")
    OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")
    GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "")
    DEFAULT_RADIUS = float(os.getenv("DEFAULT_RADIUS", 10000))  # meters
    # GA settings
    GA_POP_SIZE = int(os.getenv("GA_POP_SIZE", 40))
    GA_GENERATIONS = int(os.getenv("GA_GENERATIONS", 120))
    GA_MUTATION_RATE = float(os.getenv("GA_MUTATION_RATE", 0.12))