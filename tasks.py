import logging
from invoke import run, task

logger = logging.getLogger(__name__)


@task
def install_deps():
    """Install backend and frontend dependencies."""
    run("pip install -r requirements/all.txt")
    run("bower install")


@task
def dump_db():
    """Install backend and frontend dependencies."""
    run("pip install -r requirements/all.txt")
    run("bower install")


@task
def restore_db(path, host='localhost', port='27017', username='', password=''):
    """Restore DB."""
    run("mongorestore --host {host} --port {port} "
        "--username {username} --password {password} {path}".format(
        path=path, host=host, port=port, username=username, password=password))


@task
def syncdb():
    from pymongo import MongoClient
    from settings import MONGO_DB
    from core.models import User, City, Event

    db = MongoClient(host=MONGO_DB['host'],
                     port=MONGO_DB['port']
                     )[MONGO_DB['db_name']]

    models = [User, City, Event]
    for model in models:
        if hasattr(model, 'NEED_SYNC'):
            collection = model.MONGO_COLLECTION
            # db.drop_collection(collection)
            for index in model.INDEXES:
                i_name = index.pop('name')
                db[collection].create_index(i_name, **index)
                logger.info('Create index on {0}'.format(collection))
    logger.info('All collections is synchronized!')
