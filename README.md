# calendio

Календарь с возможностью создавать события на Tornado.

## Requirements

- Python 3.3+
- pip
- MongoDB
- Redis

## Installation

Установить зависимости:

```bash
$ pip install -r requirements/common.txt
$ bower install
```

Создать схему БД:

```bash
$ invoke setup_db
```

Запустить сервер:

```bash
$ python app.py
```

## TODO

- сборка assets
- form validation
- вынести handlers

http://habrahabr.ru/post/231201/
https://github.com/bgolub/tornado-blog/blob/master/blog.py
https://github.com/gkuhn1/tornado-and-motor-lab/tree/2b4f9088d09b0cf9fe14e99f3cbd2a70448ed913/livechat
https://github.com/narenaryan/thinktor/blob/master/app.py
