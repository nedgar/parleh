import pandas as pd
import scrapy
from urllib.parse import urlsplit, urlunsplit

PARLINFO_SEARCH_URL = 'https://parlinfo.aph.gov.au/parlInfo/search'
PARLINFO_PRIVATE_BILLS_SEARCH_URL = 'https://parlinfo.aph.gov.au/parlInfo/search/summary/summary.w3p;adv=yes;orderBy=date-eFirst;page=0;query=Dataset%3AbillsCurBef,billsCurNotBef,billsPrevParl%20Dataset_Phrase%3A%22billhome%22%20BillType_Phrase%3A%22private%22;resCount=200'
PARLINFO_PRIVATE_BILL_EXAMPLE_URL = 'https://parlinfo.aph.gov.au/parlInfo/search/display/display.w3p;adv=yes;orderBy=date-eFirst;page=0;query=Dataset%3AbillsCurBef,billsCurNotBef,billsPrevParl%20Dataset_Phrase%3A%22billhome%22%20BillType_Phrase%3A%22private%22;rec=0;resCount=Default'

def text(el, strip=True):
    txt = el.xpath('string(.)').get()
    if txt and strip:
        txt = txt.strip()
    return txt


class Spider(scrapy.Spider):
    name = 'parlinfo-private-bills'
    start_urls = [PARLINFO_PRIVATE_BILLS_SEARCH_URL]

    def parse(self, response):
        yield from self.parse_bills_search(response)

    def parse_bills_search(self, response):
        for a in response.css('.result .sumLink a'):
            yield response.follow(a, self.parse_bill)

        for a in response.css('.resultsNav a'):
            alt = a.css('img').attrib.get('alt')
            # self.logger.info("Checking nav link with alt: %s", alt)
            if alt == 'Next Page':
                # self.logger.info("Following to next page: %s", a.attrib['href'])
                yield response.follow(a)

    def parse_bill(self, response):
        bill = {
            # 'url': response.url,
            'permalink': response.css('a.permalink').attrib['href'],
            'title': text(response.css('short-title')),
            **self.parse_bill_properties(response),
            'summary': text(response.css('summary')),
        }

        progress = self.parse_bill_progress(response)
        bill['progress'] = progress
        if len(progress) > 0:
            bill['earliestDate'] = min([item['date'] for item in bill['progress']])

        yield bill

    def parse_bill_properties(self, response):
        table = response.css('h1 ~ table')[0]
        return {
            'type': text(table.css('type')),
            'originatingChamber': text(table.css('originating-chamber')),
            'status': text(table.css('status')),
            'sponsor': text(table.css('sponsor')),
        }

    def parse_bill_progress(self, response):
        heading = None
        items = []
        table = response.css('table.bills-progress')[0]
        # self.logger.info("bills-progress table: %s", table.get())
        for tr in table.css('tr'):
            # self.logger.info("tr attrib: %s", tr.attrib)
            css_class = tr.attrib.get('class')
            if css_class == 'bills-progress-heading':
                heading = text(tr.css('td'))
            elif css_class == 'bills-progress-item':
                label, date, note = [text(td) for td in tr.css('td')]
                date = date.replace('(after midnight)', '')
                date = str(pd.to_datetime(date, dayfirst=True).date())
                items.append({
                    'heading': heading,
                    'label': label,
                    'date': date,
                    'note': note if note != '' else None,
                })
            elif css_class is None:
                # blank row is common
                continue
            else:
                self.logger.warn("unknown class in bills-progress table row: %s", css_class)

        return items
