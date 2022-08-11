import pandas as pd
import scrapy
from urllib.parse import urlsplit, urlunsplit

NZ_PARL_URL = 'https://www.parliament.nz'
CURRENT_MPS_URL = NZ_PARL_URL + '/en/mps-and-electorates/members-of-parliament'
FORMER_MPS_URL = NZ_PARL_URL + '/en/mps-and-electorates/former-members-of-parliament'


def text(el, strip=True):
    s = el.xpath('string(.)').get()
    if s is None:
        return ''
    s = s.replace('\xa0', ' ')  # &nbsp; -> space
    return s.strip() if strip else s


class Spider(scrapy.Spider):
    name = 'nz-mps'
    start_urls = [CURRENT_MPS_URL]

    def parse(self, response):
        self.logger.info(f"Parsing start page at: {response.url}")

        for a in response.css('td a'):
            yield response.follow(a.attrib['href'], self.parse_profile)

    # def parse(self, response):
    #     yield from self.parse_profile(response)

    def parse_profile(self, response):
        self.logger.info(f"Parsing profile at: {response.url}")

        main = response.css('.main')[0]
        cf = main.css('.cf')[0]
        profile = {
            'name': text(main.css('h1')),
            'title': text(cf.css('h2')),
            'profile': {},
        }

        for li in cf.css('h2+ul li'):
            (key, val) = text(li).split(': ', 1)
            profile['profile'][key] = val

        roles = []
        cur_h2 = None
        for el in cf.css('h2,table,button.accordion__header')[1::]:  # skip first h2 for title, processed above
            if el.root.tag in ['table']:
                if cur_h2 in [None, 'Current Roles', 'Former Roles']:
                    parsed_table = self.parse_roles(el)
                    roles += parsed_table
                else:
                    self.logger.info(f"Skipping table after h2: {cur_h2}")                    
            else:
                cur_h2 = text(el)
        profile['roles'] = roles

        yield profile

    def parse_roles(self, table):
        rows = []
        headings = [text(td) for td in table.css('thead td')]
        for tr in table.css('tbody tr'):
            values = [text(td) for td in tr.css('td')]
            row = {}
            for key, val in zip(headings, values):
                if key == headings[0]:
                    row['_RoleType'] = key
                    key = '_RoleTitle'
                if key == 'Finish':
                    key = 'End'
                row[key] = val
            for key in ['Start', 'End']:
                if key in row:
                    row[key] = str(pd.to_datetime(row[key], dayfirst=True).date())
            rows.append(row)
        return rows
