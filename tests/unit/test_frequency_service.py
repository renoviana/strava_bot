from domain.services.frequency_service import FrequencyService
from datetime import datetime

def test_frequency_calculation():
    activities = [
        {"user_id": 1, "start_date": datetime(2025, 8, 1)},
        {"user_id": 1, "start_date": datetime(2025, 8, 2)},
        {"user_id": 2, "start_date": datetime(2025, 8, 1)},
        {"user_id": 2, "start_date": datetime(2025, 8, 1)},
    ]

    service = FrequencyService(activities)
    result = service.calculate()

    assert result[0] == (1, 2)
    assert result[1] == (2, 1)
