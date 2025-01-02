from mongoengine import Document, IntField, DictField, ListField

class Strava_group(Document):
    telegram_group_id = IntField()
    ignored_activities = ListField()
    metas = DictField(default={})
    membros = DictField(default=[])
    segments_ids = ListField(required=False, default=[])
    medalhas = DictField(default={}, required=False)
    cache_data = ListField(required=False, default=[])
