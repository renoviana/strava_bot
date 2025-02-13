from mongoengine import (
    Document,
    EmbeddedDocumentField,
    IntField,
    StringField,
    BooleanField,
    DictField,
    FloatField,
    ListField,
    DateTimeField,
)
from model.athlete import Athlete


class StravaActivity(Document):
    resource_state = IntField()
    athlete = EmbeddedDocumentField(Athlete)
    name = StringField()
    distance = FloatField()
    moving_time = IntField()
    elapsed_time = IntField()
    total_elevation_gain = FloatField()
    activity_type = StringField()
    sport_type = StringField()
    activity_id = IntField()
    start_date = DateTimeField()
    start_date_local = DateTimeField()
    timezone = StringField()
    utc_offset = IntField()
    location_city = StringField()
    location_state = StringField()
    location_country = StringField()
    achievement_count = IntField()
    kudos_count = IntField()
    comment_count = IntField()
    athlete_count = IntField()
    photo_count = IntField()
    activity_map = DictField()
    trainer = BooleanField()
    commute = BooleanField()
    manual = BooleanField()
    private = BooleanField()
    visibility = StringField()
    flagged = BooleanField()
    gear_id = StringField()
    start_latlng = ListField()
    end_latlng = ListField()
    average_speed = FloatField()
    max_speed = FloatField()
    has_heartrate = BooleanField()
    average_heartrate = FloatField()
    max_heartrate = FloatField()
    heartrate_opt_out = BooleanField()
    display_hide_heartrate_option = BooleanField()
    elev_high = FloatField()
    elev_low = FloatField()
    upload_id = IntField()
    upload_id_str = StringField()
    external_id = StringField()
    from_accepted_tag = BooleanField()
    pr_count = IntField()
    total_photo_count = IntField()
    has_kudoed = BooleanField()
    average_watts = FloatField()
    average_temp = FloatField()
    device_watts = BooleanField()
    kilojoules = FloatField()
    workout_type = IntField()
    average_cadence = FloatField()
    suffer_score = IntField()
    group_id = IntField()
    weighted_average_watts = IntField(required=False)
    max_watts = IntField(required=False)
    description = StringField(required=False)
    calories = FloatField(required=False)
    segment_efforts = ListField(required=False)
    splits_metric = ListField(required=False)
    laps = ListField(required=False)
    gear = DictField(required=False)
    partner_brand_tag = StringField(required=False)
    photos = DictField(required=False)
    highlighted_kudosers = ListField(required=False)
    hide_from_home = BooleanField(required=False)
    device_name = StringField(required=False)
    embed_token = StringField(required=False)
    segment_leaderboard_opt_out = BooleanField(required=False)
    leaderboard_opt_out = BooleanField(required=False)
