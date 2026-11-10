"""Constants for Strasbourg Parkings."""

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "strasbourg_parkings"
NAME: Final = "Strasbourg Parkings"
LOVELACE_CARD_URL: Final = f"/{DOMAIN}/strasbourg-parkings-card.js"
DATA_LOVELACE_CARD_REGISTERED: Final = "lovelace_card_registered"
DATA_ATTRIBUTION: Final = "Données issues de l'Eurométropole de Strasbourg"
DATA_SOURCE_URL: Final = (
    "https://data.strasbourg.eu/explore/dataset/occupation-parkings-temps-reel/"
)
API_URL: Final = (
    "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/"
    "occupation-parkings-temps-reel/records?limit=100"
)

CONF_PARKINGS: Final = "parkings"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# The source dataset itself is refreshed every three minutes. Polling more often
# would only create unnecessary load and duplicate observations.
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 3
MIN_SCAN_INTERVAL_MINUTES: Final = 3
MAX_SCAN_INTERVAL_MINUTES: Final = 15
DEFAULT_UPDATE_INTERVAL: Final = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)

PLATFORMS: Final = [Platform.SENSOR, Platform.BINARY_SENSOR]
