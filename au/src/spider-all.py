import scrapy
from urllib.parse import urlsplit, urlunsplit

APH_URL = 'https://www.aph.gov.au'
PARLIAMENTARIAN_URL = APH_URL + '/Senators%20and%20Members/Parliamentarian.aspx'
PARLINFO_SEARCH_URL = 'https://parlinfo.aph.gov.au/parlInfo/guide/biography.w3p;list=3'


def text(el, strip=True):
    txt = el.xpath('string(.)').get()
    if txt and strip:
        txt = txt.strip()
    return txt


class Spider(scrapy.Spider):
    name = 'parlinfo'
    start_urls = [PARLINFO_SEARCH_URL]
    # start_urls = [
    #     'https://www.aph.gov.au/Senators%20and%20Members/Parliamentarian.aspx?MPID=IPZ']

    def parse(self, response):
        for opt in response.css('#memberList option'):
            code = opt.attrib['value']
            profile_url = f"https://parlinfo.aph.gov.au/parlInfo/search/display/display.w3p;query=Id%3A%22handbook%2Fallmps%2F{code}%22"
            yield response.follow(profile_url, self.parse_profile)

    def parse_profile(self, response):
        profile = {
            'url': response.url,
        }

        sumLinkPs = response.css('.box .sumLink p')
        if len(sumLinkPs) >= 2:
            profile['party'] = text(sumLinkPs[1])

        dts = [text(el) for el in response.css('dl dt')]
        dds = [text(el) for el in response.css('dl dd')]
        for dt, dd in zip(dts, dds):
            profile[dt.lower().strip().replace(' ', '_')] = dd.strip()

        if 'title' in profile:
            profile['title'] = profile['title'].replace('Biography for ', '')

        key = 'MISSING_KEY'
        for el in response.css('.box hr ~ *').css('span,p'):
            if el.root.tag == 'span':
                key = text(el).strip()
            else:
                value = text(el).strip()
                profile[key] = profile[key] + '||' + value if key in profile else value

        yield profile
