from .grabber import (
    BaseScrapingGrabber,
    TaggingGrabber,
)

from models import Tag

ONE_DORM = '1-dormitorio'
TWO_DORMS = '2-dormitorios'
THREE_DORMS = '3-dormitorios'


class ElDiaGrabber:
    def __init__(self, dorms=TWO_DORMS):
        self.scrape_uri = f'http://clasificados.eldia.com/clasificados-alquiler-departamentos-{dorms}-la-plata'
        tags = [
            {
                ONE_DORM: Tag.get(tag=ONE_DORM),
                TWO_DORMS: Tag.get(tag=TWO_DORMS),
                THREE_DORMS: Tag.get(tag=THREE_DORMS),
            }[dorms]
        ]
        self.grabbers = [
            ConFotoGrabber(self.scrape_uri, tags),
            ClasifGrabber(self.scrape_uri, tags),
        ]

    def grab(self):
        for grabber in self.grabbers:
            grabber.grab()


class ConFotoGrabber(TaggingGrabber, BaseScrapingGrabber):
    scrape_tags = ['div']
    scrape_classes = ['avisosconfoto']

    def __init__(self, scrape_uri, tags):
        super(ConFotoGrabber, self).__init__()
        self.scrape_uri = scrape_uri
        self.tags = tags

    def get_contents(self, element):
        try:
            url = element.a['href']
        except Exception:
            url = ''
        title = element.span.strong.string
        description = element.span.contents[-1]
        return f'{url} - *{title}* {description}'


class ClasifGrabber(TaggingGrabber, BaseScrapingGrabber):
    scrape_tags = ['div.avisos>p']
    scrape_classes = []

    def __init__(self, scrape_uri, tags):
        super(ClasifGrabber, self).__init__()
        self.scrape_uri = scrape_uri
        self.tags = tags

    def get_contents(self, element):
        description = element.string
        return f'{description}'
