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

class DbManager:

    def __init__(self, group_id):
        self.group_id = int(group_id)
        
    def get_strava_group(self) -> Strava_group:
        strava_group = Strava_group.objects(telegram_group_id=self.group_id).first()

        if not strava_group:
            self.add_strava_group()
            strava_group = Strava_group.objects(telegram_group_id=self.group_id).first()

        return strava_group

    def add_strava_group(self):
        return Strava_group(
            telegram_group_id=self.group_id,
            membros={},
            metas={},
            ignored_activities=[],
            segments_ids=[],
            medalhas={'ride':{}},
            cache_data=[]
        ).save()

    def list_strava_activities(self, user_id, first_day, last_day):
        query = {
            'group_id': self.group_id,
            'athlete.id': user_id,
            'start_date_local': {
                "$gte": first_day,
                "$lt": last_day,
            }
        }

        data = StravaActivity.objects(__raw__=query).order_by('-start_date_local').all()

        new_data = []
        for i in data:
            data_dict = i.to_mongo().to_dict()
            data_dict['type'] = data_dict['activity_type']
            data_dict['id'] = data_dict['activity_id']
            data_dict['map'] = data_dict['activity_map']
            del data_dict['activity_type']
            del data_dict['activity_id']
            del data_dict['activity_map']
            new_data.append(data_dict)
        return new_data

    def update_membro(self, user, data):
        group = self.get_strava_group()
        group.membros[user] = data
        group.save()

    def remove_strava_user(self, user_name):
        """
        Remove usuário do strava
        Args:
            user_name (str): nome do usuário
            user_name_admin (str): nome do admin
        """
        strava_group = self.get_strava_group()
        removed_user_id = strava_group.membros[user_name].get('athlete_id')
        strava_group.membros = {key: value for key, value in strava_group.membros.items() if key != user_name}

        query = {
            "athlete.id":  removed_user_id,
            "group_id": self.group_id,
        }
        StravaActivity.objects(__raw__=query).delete()
        strava_group.save()
        return strava_group.membros
    
    def update_meta(self, tipo_meta, km):
        strava_group = self.get_strava_group()
        metas = strava_group.metas

        if km:
            km = int(km)
            metas[tipo_meta] = km
        else:
            del metas[tipo_meta]
        
        strava_group.metas = metas
        strava_group.save()
        return strava_group.metas

    def add_ignore_activity(self, activity_id):
        """
        Ignora atividade
        Args:
            activity_id (str): id da atividade
        """
        strava_group = self.get_strava_group()
        ignored_activities = strava_group.ignored_activities or []
        ignored_activities.append(str(activity_id))
        strava_group.ignored_activities = ignored_activities
        strava_group.save()
        return strava_group.ignored_activities
    
    def process_activities(self, new_activity_list):
        if not new_activity_list:
            return

        mongo_lista = []
        for activity in new_activity_list:
            activity_dict = activity.copy()
            activity_dict['group_id'] = self.group_id
            activity_dict['activity_type'] = activity_dict['type']
            activity_dict['activity_id'] = activity_dict['id']
            activity_dict['activity_map'] = activity_dict['map']
            del activity_dict['type']
            del activity_dict['id']
            del activity_dict['map']
            mongo_lista.append(StravaActivity(**activity_dict))
        
        StravaActivity.objects.insert(mongo_lista)