from mongoengine import EmbeddedDocument, IntField

class Athlete(EmbeddedDocument):
    id = IntField()
    resource_state = IntField()
