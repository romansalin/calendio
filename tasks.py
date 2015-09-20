from invoke import run, task


@task
def restore_db(path, host='localhost', port='27017', username='', password=''):
    """Restore DB."""
    run("mongorestore --host {host} --port {port} "
        "--username {username} --password {password} {path}".format(
        path=path, host=host, port=port, username=username, password=password))


@task
def dump_db():
    """Install backend and frontend dependencies."""
    run("pip install -r requirements/all.txt")
    run("bower install")


@task
def install_deps():
    """Install backend and frontend dependencies."""
    run("pip install -r requirements/all.txt")
    run("bower install")
