from urllib.parse import SplitResult, urlsplit

import scrapy

from kuntavaalit.items import *


class SiteSpider(scrapy.Spider):
    allowed_domains = [
        'api.prod.vaalit.almamedia.fi',
    ]
    start_urls = [
        'https://api.prod.vaalit.almamedia.fi/public/election/34/constituency/',
    ]

    def parse(self, response: scrapy.http.Response):
        raise NotImplemented

    def load_questions(self, response: scrapy.http.TextResponse):
        url: SplitResult = urlsplit(response.url)
        municipality = url.path.strip('/').split('/')[-1]

        yield Question(
            url=response.url,
            data=response.json(),
            municipality=municipality,
        )

    def load_candidates(self, response: scrapy.http.TextResponse):
        url: SplitResult = urlsplit(response.url)
        municipality = url.path.strip('/').split('/')[-1]
        data = response.json()

        for i in data:
            yield Answer(
                url=response.url,
                data=i,
                municipality=municipality,
                candidateid=i['id'],
            )

    def load_parties(self, response: scrapy.http.TextResponse):
        yield Party(
            url=response.url,
            data=response.json(),
        )


class KuntaSpider(SiteSpider):
    """
    Fetch all from municipality X
    """

    name = 'kunta'
    id: str = ""

    def __init__(self, id: str = ""):
        if id == "":
            id = None

        if id is None:
            raise ValueError("no id")

        self.id = id

    def parse(self, response: scrapy.http.TextResponse):
        data = response.json()

        found: bool = False
        for i in data:
            if str(i['id']) == self.id:
                found = True
                break

        if not found:
            raise ValueError(f"id {self.id} not found")

        yield Municipality(
            url=response.url,
            data=data,
        )

        yield scrapy.Request(
            response.urljoin(f"/public/election/34/party"),
            callback=self.load_parties,
        )

        yield scrapy.Request(
            response.urljoin(f"/public/election/34/question/{self.id}"),
            callback=self.load_questions,
        )

        yield scrapy.Request(
            response.urljoin(f"/public/election/34/candidate/{self.id}"),
            callback=self.load_candidates,
        )


class KVSpider(SiteSpider):
    """
    Fetch all
    """

    name = 'kaikki'

    def parse(self, response: scrapy.http.TextResponse):
        data = response.json()

        yield Municipality(
            url=response.url,
            data=data,
        )

        yield scrapy.Request(
            response.urljoin(f"/public/election/34/party"),
            callback=self.load_parties,
        )

        for i in data:
            yield scrapy.Request(
                response.urljoin(f"/public/election/34/question/{i['id']}"),
                callback=self.load_questions,
            )

            yield scrapy.Request(
                response.urljoin(f"/public/election/34/candidate/{i['id']}"),
                callback=self.load_candidates,
            )
