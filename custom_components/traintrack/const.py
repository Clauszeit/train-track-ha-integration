"""Constants for the TrainTrack integration."""

DOMAIN = "traintrack"
CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 3600
PLATFORMS = ["sensor"]

API_SESSION_PATH = "/api/session"
API_CONNECTIONS_PATH = "/api/connections"
