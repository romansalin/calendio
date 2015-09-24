from datetime import datetime

from schematics.types import (StringType, EmailType, DateType,
                              DateTimeType)

from ..core.models import BaseModel
from ..core.utils import check_pass, make_pass


class User(BaseModel):
    name = StringType(default='', max_length=50)
    email = EmailType(required=True)
    phone = StringType(default=None)
    city_id = StringType(default=None)
    photo = StringType(default=None)
    birth_date = DateType(default=None)
    password_hash = StringType(default='')
    password_salt = StringType(default='')
    created_at = DateTimeType(default=datetime.now)

    MONGO_COLLECTION = 'accounts'
    NEED_SYNC = True
    INDEXES = (
        {'name': 'email', 'unique': True},
    )

    def check_password(self, password):
        return check_pass(password, self.password_hash, self.password_salt)

    def set_password(self, password):
        self.password_salt, self.password_hash = make_pass(password)

    def __str__(self):
        return "{0} ({1})".format(self.name or self._id, self.email)


class Country(BaseModel):
    pass


class City(BaseModel):
    pass
