from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, IntField, StringField, BooleanField, DictField, FloatField, ListField, DateTimeField

class Strava_group(Document):
    telegram_group_id = IntField()
    ignored_activities = ListField()
    metas = DictField(default={})
    membros = DictField(default=[])
    segments_ids = ListField(required=False, default=[])
    medalhas = DictField(default={}, required=False)
    cache_data = ListField(required=False, default=[])

class Athlete(EmbeddedDocument):
    id = IntField()
    resource_state = IntField()

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
    




def get_strava_group(telegram_group_id):
    return Strava_group.objects(telegram_group_id=telegram_group_id).first()

def add_strava_group(telegram_group_id, membros={}, metas={}, ignored_activities=[], segments_ids=[], medalhas={'ride':{}}, cache_data=[]):
    return Strava_group(
        telegram_group_id=telegram_group_id,
        membros=membros,
        metas=metas,
        ignored_activities=ignored_activities,
        segments_ids=segments_ids,
        medalhas=medalhas,
        cache_data=cache_data
    ).save()

def add_strava_activity(data):
    if StravaActivity.objects(activity_id=data['id']).first():
        return

    data_copy = data.copy()
    data_copy['activity_type'] = data_copy['type']
    data_copy['activity_id'] = data_copy['id']
    data_copy['activity_map'] = data_copy['map']
    del data_copy['type']
    del data_copy['id']
    del data_copy['map']
    return StravaActivity(**data_copy).save()

def get_strava_activity(activity_id):
    return StravaActivity.objects(activity_id=activity_id).first()

def list_strava_activities(group_id, query=None, order_by='-start_date_local'):
    if not query:
        return StravaActivity.objects(group_id=group_id).order_by(order_by).all()
    
    query['group_id'] = group_id
    return StravaActivity.objects(__raw__=query).order_by(order_by).all()

def get_last_strava_activity(group_id, athlete_id):
    query = {
        'group_id': group_id,
        "athlete.id": athlete_id
    }
    return StravaActivity.objects(group_id=group_id, **{"athlete__id": athlete_id}).order_by('-start_date_local').first()