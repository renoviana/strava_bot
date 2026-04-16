import sys
from unittest.mock import MagicMock

mock_config = MagicMock()
mock_config.STRAVA_CLIENT_ID = "test_client_id"
mock_config.STRAVA_CLIENT_SECRET = "test_client_secret"
mock_config.TELEGRAM_TOKEN = "test_token"
mock_config.MONGO_URI = "mongodb://localhost:27017/test"
mock_config.REDIRECT_URI = "http://test/{}"
sys.modules["config"] = mock_config
