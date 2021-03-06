from fiftystates.scrape import ScrapeError, NoDataForYear
from fiftystates.scrape.legislators import LegislatorScraper, Legislator

import lxml.html
import re, contextlib

class COLegislatorScraper(LegislatorScraper):
    state = 'co'
    
    @contextlib.contextmanager
    def lxml_context(self, url, sep=None, sep_after=True):
        try:
            body = self.urlopen(url)
        except:
            body = self.urlopen("http://www.google.com")
        
        if sep != None: 
            if sep_after == True:
                before, itself, body = body.rpartition(sep)
            else:
                body, itself, after = body.rpartition(sep)    
        
        elem = lxml.html.fromstring(body)
        
        try:
            yield elem
        except:
            print "FAIL"
            #self.show_error(url, body)
            raise

    def scrape(self, chamber, year):
        # Legislator data only available for the current session
        if year != '2009':
            raise NoDataForYear(year)
        
        if chamber == "upper":
            url = "http://www.leg.state.co.us/Clics/CLICS2010A/directory.nsf/MIWeb?OpenForm&chamber=Senate"
        else:
            url = "http://www.leg.state.co.us/Clics/CLICS2010A/directory.nsf/MIWeb?OpenForm&chamber=House"
            
        with self.lxml_context(url) as page:
            # Iterate through legislator names
            for element, attribute, link, pos in page.iterlinks():
                with self.lxml_context(link) as legislator_page:
                    leg_elements = legislator_page.cssselect('b')
                    leg_name = leg_elements[0].text_content()
                 
                    district = ""
                    district_match = re.search("District [0-9]+", legislator_page.text_content())
                    if (district_match != None):
                        district = district_match.group(0)
                    
                    email = ""
                    email_match = re.search('E-mail: (.*)', legislator_page.text_content())
                    if (email_match != None):
                        email = email_match.group(1)
                        
                    form_page_url = "http://www.leg.state.co.us//clics/clics2010a/directory.nsf/d1325833be2cc8ec0725664900682205?SearchView"
                    form_page = lxml.html.parse(form_page_url).getroot()
                    form_page.forms[0].fields['Query'] = leg_name
                    result = lxml.html.parse(lxml.html.submit_form(form_page.forms[0])).getroot()
                    elements = result.cssselect('td')
                    party_letter = elements[7].text_content()
                    
                    if party_letter == "D":
                        party = "Republican"
                    elif party_letter == "R":
                        party = "Democrat"
                    else:
                        party = "Independent"
                    
                    leg = Legislator(year, chamber, district, leg_name,
                                 "", "", "", party,
                                 official_email=email)
                    leg.add_source(link)
                    
                    self.save_legislator(leg)
