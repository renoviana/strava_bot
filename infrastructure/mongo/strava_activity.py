from datetime import datetime
from typing import Optional
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
from infrastructure.mongo.athlete import Athlete


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

    def get_activities(self, group_id: int, start: datetime, end: datetime, member_id_list:Optional[list] = None, sort = "-start_date_local"):
        query = {
            "group_id": group_id,
            "start_date_local": {"$gte": start, "$lt": end}
        }

        if member_id_list:
            query["athlete.id"] = {"$in": member_id_list}

        return StravaActivity.objects(
            __raw__=query
        ).order_by(sort).all()

    def exists(self, activity_id: str, group_id: int) -> bool:
        return StravaActivity.objects(activity_id=activity_id, group_id=group_id).count() > 0
    
    def rules(self, activity_data: dict) -> bool:
        if activity_data.get("flagged"):
            return False
        return True


    def save_activity(self, group_id: int, activity_data: dict):
        if not self.rules(activity_data):
            return

        activity_data["group_id"] = group_id
        activity_data["activity_type"] = activity_data["type"]
        activity_data["activity_id"] = activity_data["id"]
        activity_data["activity_map"] = activity_data["map"]
        del activity_data["type"]
        del activity_data["id"]
        del activity_data["map"]
        activity_data['start_date'] = datetime.strptime(activity_data["start_date"], '%Y-%m-%dT%H:%M:%SZ')
        activity_data['start_date_local'] = datetime.strptime(activity_data["start_date_local"], '%Y-%m-%dT%H:%M:%SZ')

        if self.exists(activity_data["activity_id"], group_id):
            return

        StravaActivity(**activity_data).save()

    def list_sports(self, group_id:int, start_date:datetime, end_date:datetime) -> list[str]:
        return StravaActivity.objects(
            __raw__={
                "group_id": group_id,
                "start_date_local": {"$gte": start_date, "$lt": end_date}
            }
        ).only("sport_type").distinct("sport_type")

    def remove_activity_member(self, group_id: int, member_id: int):
        StravaActivity.objects(
            __raw__={
                "group_id": group_id,
                "athlete.id": member_id
            }
        ).delete()
