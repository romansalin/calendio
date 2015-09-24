import logging

from ..core.handlers import BaseHandler
from ..core.utils import authenticated

logger = logging.getLogger(__name__)


class MainHandler(BaseHandler):
    @authenticated()
    def get(self):
        self.render('index.html')
