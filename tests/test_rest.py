import datetime
import logging
from mongoengine import connect
from rest import StravaGroup
from secure import MONGO_URI, TELEGRAM_GROUP_ID
logger = logging.getLogger(__name__)

connect(host=MONGO_URI)
strava_group = StravaGroup(TELEGRAM_GROUP_ID)

def test_strava_commands():
    assert strava_group.strava_entity

def test_get_ranking_str():
    assert "Ranking June" in strava_group.get_ranking_str('Ride')

def test_get_ranking_year():
    assert str(datetime.datetime.now().year) in strava_group.get_ranking_str('Ride', year_rank=True)

def test_get_point_str():
    assert isinstance(strava_group.get_point_str(), list)

def test_get_stats_str():
    assert "Estatísticas do mês" in strava_group.get_stats_str()

def test_get_segments_str():
    assert "Segmentos do mês:" in strava_group.get_segments_str()