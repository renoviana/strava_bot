from mongoengine import Document, IntField, DictField, ListField


class StravaGroup(Document):
    telegram_group_id = IntField()
    ignored_activities = ListField()
    ignored_activities_rank = ListField()
    metas = DictField(default={})
    membros = DictField(default={})
    segments_ids = ListField(required=False, default=[])
    medalhas = DictField(default={}, required=False)
    cache_data = ListField(required=False, default=[])

    def get_group(self, group_id: int):
        return StravaGroup.objects(telegram_group_id=group_id).first()
