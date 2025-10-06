from mongoengine import Document, IntField, DictField, ListField, DateTimeField


class StravaGroup(Document):
    telegram_group_id = IntField()
    metas = DictField(default={})
    membros = DictField(default={})
    segments_ids = ListField(required=False, default=[])
    medalhas = DictField(default={}, required=False)
    last_sync = DateTimeField(required=False)

    def get_group(self, group_id: int):
        return StravaGroup.objects(telegram_group_id=group_id).first()
