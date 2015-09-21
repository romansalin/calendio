import logging
from datetime import datetime

from bson.objectid import ObjectId
from tornado import gen
import motor
from schematics.models import Model
from schematics.types import (NumberType, StringType, EmailType, DateType,
                              DateTimeType)

from .utils import check_pass, make_pass

logger = logging.getLogger(__name__)
MAX_FIND_LIST_LEN = 100


class BaseModel(Model):
    """
    Provides generic methods to work with model.
    Why use `MyModel.find_one` instead of `db.collection.find_one` ?
    1. Collection name is declared inside the model, so it is not needed
        to provide it all the time
    2. This `MyModel.find_one` will return MyModel instance, whereas
        `db.collection.find_one` will return dictionary
    Example with directly access:
        db_result = yield motor.Op(db.collection_name.find_one({"i": 3}))
        obj = MyModel(db_result)
    Same example, but using MyModel.find_one:
        obj = yield MyModel.find_one(db, {"i": 3})
    """

    _id = NumberType(number_class=ObjectId, number_type="ObjectId")

    def __init__(self, *args, **kwargs):
        self.set_db(kwargs.pop('db', None))
        super(BaseModel, self).__init__(*args, **kwargs)

    @property
    def db(self):
        return getattr(self, '_db', None)

    def set_db(self, db):
        self._db = db

    @classmethod
    def process_query(cls, query):
        """
        query can be modified here before actual providing to database.
        """
        return dict(query)

    @property
    def pk(self):
        return self._id

    @classmethod
    def get_model_name(cls):
        return cls.MONGO_COLLECTION

    @classmethod
    def get_collection(cls):
        return getattr(cls, 'MONGO_COLLECTION', None)

    @classmethod
    def check_collection(cls, collection):
        return collection or cls.get_collection()

    @classmethod
    def find_list_len(cls):
        return getattr(cls, 'FIND_LIST_LEN', MAX_FIND_LIST_LEN)

    @classmethod
    @gen.coroutine
    def find_one(cls, db, query, collection=None, model=True):
        query = cls.process_query(query)
        result = yield motor.Op(
            db[cls.check_collection(collection)].find_one, query)
        if model and result:
            result = cls.make_model(result, "find_one", db=db)
        raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def remove_entries(cls, db, query, collection=None):
        """
        Removes documents by given query.
        Example:
            obj = yield ExampleModel.remove_entries(
                self.db, {"first_name": "Hello"})
        """
        c = cls.check_collection(collection)
        query = cls.process_query(query)
        yield motor.Op(db[c].remove, query)

    @gen.coroutine
    def remove(self, db, collection=None):
        """
        Removes current instance from database.
        Example:
            obj = yield ExampleModel.find_one(self.db, {"last_name": "Sara"})
            yield obj.remove(self.db)
        """
        _id = self.to_primitive()['_id']
        yield self.remove_entries(db, {"_id": _id}, collection)

    @gen.coroutine
    def save(self, db=None, collection=None, ser=None):
        """
        If object has _id, then object will be created or fully rewritten.
        If not, object will be inserted and _id will be assigned.
        Example:
            obj = ExampleModel({"first_name": "Vasya"})
            yield obj.save(self.db)
        """
        db = db or self.db
        c = self.check_collection(collection)
        data = self.get_data_for_save(ser)
        result = yield motor.Op(db[c].save, data)
        if result:
            self._id = result

    @gen.coroutine
    def insert(self, db=None, collection=None, ser=None, **kwargs):
        """
        If object has _id, then object will be inserted with given _id.
        If object with such _id is already in database, then
        pymongo.errors.DuplicateKeyError will be raised.
        If object has no _id, then object will be inserted and _id will be
        assigned.
        Example:
            obj = ExampleModel({"first_name": "Vasya"})
            yield obj.insert()
        """
        db = db or self.db
        c = self.check_collection(collection)
        data = self.get_data_for_save(ser)
        result = yield motor.Op(db[c].insert, data, **kwargs)
        if result:
            self._id = result

    @gen.coroutine
    def update(self, db=None, query=None, collection=None, update=None,
               ser=None, upsert=False, multi=False):
        """
        Updates the object. If object has _id, then try to update the object.
        If object with given _id is not found in database, or object doesn't
        have _id field, then save it and assign generated _id.
        Difference from save:
            Suppose such object in database:
                {"_id": 1, "foo": "egg1", "bar": "egg2"}
            We want to save following data:
                {"_id": 1, "foo": "egg3"}
            If we'll run save, then in database will be following data:
                {"_id": 1, "foo": "egg3"} # "bar": "egg2" is removed
            But if we'll run update, then existing fields will be kept:
                {"_id": 1, "foo": "egg3", "bar": "egg2"}
        Example:
            obj = yield ExampleModel.find_one(self.db, {"first_name": "Foo"})
            obj.last_name = "Bar"
            yield obj.update(self.db)
        """
        db = db or self.db
        # TODO: refactor, update and ser arguments are very similar, left only one
        c = self.check_collection(collection)
        if update is None:
            data = self.get_data_for_save(ser)
        else:
            data = update
        if not query:
            _id = self.pk or data.pop("_id")
            query = {"_id": _id}
        if update is None:
            data = {"$set": data}
        result = yield motor.Op(db[c].update, query, data, upsert=upsert,
                                multi=multi)
        logger.debug("Update result: {0}".format(result))
        raise gen.Return(result)

    @classmethod
    def get_cursor(cls, db, query, collection=None, fields={}):
        c = cls.check_collection(collection)
        query = cls.process_query(query)
        return db[c].find(query, fields) if fields else db[c].find(query)

    @classmethod
    @gen.coroutine
    def find(cls, cursor, model=True, list_len=None):
        """
        Returns a list of found documents.
        :arg cursor: motor cursor for find
        :arg model: if True, then construct model instance for each document.
            Otherwise, just leave them as list of dicts.
        :arg list_len: list of documents to be returned.
        Example:
            cursor = ExampleModel.get_cursor(self.db, {"first_name": "Hello"})
            objects = yield ExampleModel.find(cursor)
        """
        list_len = list_len or cls.find_list_len() or MAX_FIND_LIST_LEN
        result = yield motor.Op(cursor.to_list, list_len)
        if model:
            field_names_set = set(cls._fields.keys())
            for i in range(len(result)):
                result[i] = cls.make_model(
                    result[i], "find", field_names_set)
        raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def aggregate(cls, db, pipe_list, collection=None):
        c = cls.check_collection(collection)
        result = yield motor.Op(db[c].aggregate, pipe_list)
        raise gen.Return(result)

    def get_data_for_save(self, ser):
        data = ser or self.to_primitive()
        if '_id' in data and data['_id'] is None:
            del data['_id']
        return data

    @classmethod
    def make_model(cls, data, method_name, field_names_set=None, db=None):
        """
        Create model instance from data (dict).
        """
        if field_names_set is None:
            field_names_set = set(cls._fields.keys())
        else:
            if not isinstance(field_names_set, set):
                field_names_set = set(field_names_set)
        new_keys = set(data.keys()) - field_names_set
        if new_keys:
            logger.warning(
                "'{0}' has unhandled fields in DB: "
                "'{1}'. {2} returned data: '{3}'"
                .format(cls.__name__, new_keys, data, method_name))
            for new_key in new_keys:
                del data[new_key]
        return cls(raw_data=data, db=db)


class User(BaseModel):
    name = StringType(default='', max_length=None)
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
        return "User {0} ({1})".format(self.name or self._id, self.email)


class Country(BaseModel):
    pass


class City(BaseModel):
    pass


class Event(BaseModel):
    pass
