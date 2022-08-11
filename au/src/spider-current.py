import pandas as pd
import scrapy
from urllib.parse import urlsplit, urlunsplit

APH_URL = 'https://www.aph.gov.au'
PARLIAMENTARIAN_URL = APH_URL + '/Senators%20and%20Members/Parliamentarian.aspx'
PARLINFO_SEARCH_URL = 'https://parlinfo.aph.gov.au/parlInfo/search/summary/summary.w3p'


def text(el, strip=True):
    txt = el.xpath('string(.)').get()
    if txt and strip:
        txt = txt.strip()
    return txt


class Spider(scrapy.Spider):
    name = 'parlinfo'
    start_urls = [PARLINFO_SEARCH_URL + ';adv=yes;orderBy=alphaAss;page=0;query=Dataset%3Amembers;resCount=200']
    # start_urls = ['https://www.aph.gov.au/Senators%20and%20Members/Parliamentarian.aspx?MPID=A9B']
    # start_urls = ['https://parlinfo.aph.gov.au/parlInfo/download/chamber/hansardr/1998-03-02/toc_unixml/reps%201998-03-02.xml;fileType=text%2Fxml']

    def parse(self, response):
        yield from self.parse_parliamentarians(response)

    def parse_parliamentarians(self, response):
        self.logger.info("Parsing top URL: %s", response.url)
        for href in response.css('.sumLink a::attr(href)'):
            self.logger.info("Following sumLink anchor: %s", href.get())
            yield response.follow(href, self.parse_parliamentarian)

    def parse_parliamentarian(self, response):
        profile = {
            'name': text(response.css('.profile h1')),
            'title': text(response.css('.profile h3'))
        }

        for dt, dd in zip(response.css('.profile dl dt'), response.css('.profile dl dd')):
            profile[text(dt).lower()] = text(dd)

        profile['electorate'] = text(response.css(
            'section[aria-label="Electorate details"] h3'))

        dls = response.css('article h2 + dl')  # not the most precise selector
        biography = None
        if len(dls) > 0:
            bio_dl = dls[0]
            biography = {
                text(dt): [text(li) for li in dd.css('li')] for dt, dd in zip(bio_dl.css('dt'), bio_dl.css('dd'))
            }

        # speeches = []
        for href in response.css('a[aria-label="Browse all speeches (Hansard)"]::attr(href)'):
            self.logger.info("Following parliamentarian speeches URL: %s", href.get())
            speeches_url = href.get() + '&ps=100'
            yield response.follow(speeches_url, self.parse_speeches)

        yield {
            'type': 'parliamentarian',
            'profile': profile,
            'biography': biography,
        }

    def parse_speeches(self, response):
        self.logger.info("parse_speeches: parsing speeches at: %s", response.url)

        for li in response.css('ul.search-filter-results li'):
            dts = li.css('dt::text').getall()
            dds = li.css('dd::text').getall()
            date = None
            for dt, dd in zip(dts, dds):
                if dt.upper() == 'DATE':
                    date = pd.to_datetime(dd)
            self.logger.info("speech li date: %s", date)
            if date < pd.Timestamp(2017, 1, 1):
                self.logger.warn("Skipping speech prior to 2017-01-01")
                continue

            for href in li.css('a[title="XML format"]::attr(href)'):
                self.logger.info("Following speeches XML format anchor: %s", href.get())
                yield response.follow(href, self.parse_session_xml)

        pg = response.css('.results-pagination')[0]
        for href in pg.css('li.next a::attr(href)'):
            self.logger.info("Following next speeches URL for anchor: %s", href.get())
            yield response.follow(href, self.parse_speeches)


    def parse_session_xml(self, response):
        self.logger.info("download_session_xml: parsing session XML at: %s", response.url)
        session_header = response.css('session\\.header')[0]
        date = text(session_header.css('date'))

        if pd.to_datetime(date) < pd.Timestamp(2017, 1, 1):
            self.logger.warn("Skipping session prior to 2017-01-01: %s", date)
            return

        yield {
            'type': 'session', 
            'sourceUrl': response.url,
            'date': date,
            'parliamentNum': text(session_header.css('parliament\\.no')),
            'periodNum': text(session_header.css('period\\.no')),
            'chamber': text(session_header.css('chamber')),
            'proof': text(session_header.css('proof')),
        }

        for debate in response.css('debate'):
            title1 = text(debate.css('debateinfo title'))
            for speech in debate.css('speech'):
                yield from self.parse_speech(speech, date, [title1])

            for subdebate1 in debate.css('subdebate\\.1'):
                title2 = text(subdebate1.css('subdebateinfo title'))
                for speech in subdebate1.css('speech'):
                    yield from self.parse_speech(speech, date, [title1, title2])

                for subdebate2 in subdebate1.css('subdebate\\.2'):
                    title3 = text(subdebate2.css('subdebateinfo title'))
                    for speech in subdebate2.css('speech'):
                        yield from self.parse_speech(speech, date, [title1, title2, title3])

    def parse_speech(self, speech, date, debateTitles):
        talkerId = text(speech.css('talker name\\.id'))

        timestamp = text(speech.css('talker time\\.stamp'))
        if timestamp == '':
            timestamp = None

        talker = {
            'type': 'talker',
            'talkerId': talkerId,
            'date': date,
            'timestamp': timestamp,
            'name': text(speech.css('talker name[role="metadata"]')),
            'displayName': text(speech.css('talker name[role="display"]')),
            'electorate': text(speech.css('talker electorate')),
            'party': text(speech.css('talker party')),
        }
        yield talker
        
        time = text(speech.css('.HPS-Time'))
        if time == '':
            time = None

        paragraphs = speech.css('talk\\.text p')
        if len(paragraphs) == 0:
            paragraphs = speech.css('para')
        speech_text = '\n\n'.join([text(p) for p in paragraphs])

        yield {
            'type': 'speech',
            'talkerId': talkerId,
            'date': date,
            'time': time,
            'debateTitles': '||'.join(debateTitles),
            'text': speech_text,
        }
