from datetime import datetime
import logging
import requests
import bs4

from models.message import (
    Message, MessageToTags,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Grabber(requests.Session):
    def grab(self):
        raise NotImplementedError()

    def save_message(self, message):
        return message.save()


class TaggingGrabber(Grabber):
    def tag_message(self, message):
        for tag in self.tags:
            MessageToTags.create(message=message, tag=tag)

    def save_message(self, message):
        super(TaggingGrabber, self).save_message(message)
        self.tag_message(message)


class BaseScrapingGrabber(Grabber):
    scrape_uri = None
    scrape_classes = []
    scrape_tags = []
    parser = 'html.parser'

    def get_contents(self, element):
        return element.string

    def grab(self):
        data = self.get(self.scrape_uri).content
        soup = bs4.BeautifulSoup(data, self.parser)
        for element in self.filter_soup(soup):
            m = Message(content=self.get_contents(element), date=datetime.now())
            self.save_message(m)


    def filter_soup(self, soup):
        for tag in self.scrape_tags:
            for el in soup.select('.'.join([tag, *self.scrape_classes])):
                yield el
