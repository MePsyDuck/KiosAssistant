from tortoise import Model
from tortoise.fields import IntField, BigIntField, DatetimeField, CharField, ForeignKeyRelation, ReverseRelation, OneToOneField, CASCADE, ForeignKeyField


class User(Model):
    id = BigIntField(pk=True, generated=False)
    time_zone = CharField(max_length=255, null=True)
    time_format = CharField(max_length=255, null=True)

    messages: ReverseRelation['Message']

    def __str__(self):
        return f'{self.__class__}: {self.id}'


class Message(Model):
    id = BigIntField(pk=True)
    channel_id = BigIntField(null=False)

    user: ForeignKeyRelation[User] = ForeignKeyField('models.User', related_name='messages', null=False)

    user_event: ReverseRelation['Event']
    bot_event: ReverseRelation['Event']
    reminder: ReverseRelation['Reminder']

    def __str__(self):
        return f'{self.__class__}: {self.id}'


class Event(Model):
    id = IntField(pk=True, generated=True)
    name = CharField(max_length=255, null=True)
    scheduled_dt = DatetimeField()

    author_message = OneToOneField('models.Message', related_name='user_event', on_delete=CASCADE, null=False)
    bot_message = OneToOneField('models.Message', related_name='bot_event', on_delete=CASCADE, null=False)

    def __str__(self):
        return f'{self.__class__}: {self.id}'


class Reminder(Model):
    id = IntField(pk=True, generated=True)
    info = CharField(max_length=255, null=True)
    added_dt = DatetimeField()
    expire_dt = DatetimeField()

    for_message = OneToOneField('models.Message', related_name='reminder', on_delete=CASCADE, null=False)

    def __str__(self):
        return f'{self.__class__}: {self.id}'
