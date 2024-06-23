from mongoengine import Document, ListField, DictField, IntField


class Strava_group(Document):
    telegram_group_id = IntField()
    ignored_activities = ListField()
    metas = DictField(default={})
    membros = DictField(default=[])
    segments_ids = ListField(required=False, default=[])
    medalhas = DictField(default={}, required=False)


def get_strava_group(telegram_group_id):
    return Strava_group.objects(telegram_group_id=telegram_group_id).first()

def add_strava_group(telegram_group_id, membros={}, metas={}, ignored_activities=[]):
    return Strava_group(telegram_group_id=telegram_group_id, membros=membros, metas=metas,ignored_activities=ignored_activities).save()