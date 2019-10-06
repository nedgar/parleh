import json
import os.path
import pandas as pd
import requests
from requests.exceptions import HTTPError

def trim(s):
    return s.lstrip('<br>').rstrip('<br>').replace('<br>', '|') if isinstance(s, str) else s

class Parleh:
    PARL_API_URL = 'https://lop.parl.ca/ParlinfoWebAPI'
    PERSON_URL = PARL_API_URL + '/Person/'
    PERSON_SEARCH_URL = PERSON_URL + 'SearchAndRefine'
    PERSON_PROFILE_URL = PERSON_URL + 'GetPersonWebProfile/%d'

    CURRENT_PARLIAMENT = 43

    REGULAR_COLS = ['PersonId', 'LastName', 'UsedFirstName', 'StraightDisplayName', 'Gender', 'LanguageEn',
        'PartyEn', 'ConstituencyEn', 'ProvinceEn', 'TypeOfParliamentarianEn', 
        'DateOfBirth', 'DateOfBirthIsApproximate', 
        'CityOfBirthEn', 'ProvinceOfBirthEn', 'CountryOfBirthEn', 'IsCanadianOrigin', 'DiedInOffice']
    DEATH_COLS = ['DateOfDeath', 'DeceasedOnDuty']
    DATE_COLS = ['DateOfBirth', 'DateOfDeath']

    DATA_DIR = '../data/'
    PARLIAMENTS_DIR = DATA_DIR + 'parliaments/'
    PEOPLE_DIR = DATA_DIR + 'people/'

    def query_people(self, parliament):
        params = { 'refiners': '4-%s,' % (self.CURRENT_PARLIAMENT - parliament + 1) }
        r = requests.get(self.PERSON_SEARCH_URL, params= params)
        r.raise_for_status()
        return r.json()

    def query_profile(self, person_id):
        r = requests.get(self.PERSON_PROFILE_URL % person_id)
        r.raise_for_status()
        return r.json()
        
    def iter_people(self, people, parliament):    
        for d in people:
            row = {'Parliament': parliament}
            row.update({col: trim(d[col]) for col in self.REGULAR_COLS})
            dd = d['Death']
            if dd:
                row.update({col: trim(dd[col]) for col in self.DEATH_COLS})
            yield row

    def people_df(self, people, parliament):
        df = pd.DataFrame(self.iter_people(people, parliament), columns= self.REGULAR_COLS + self.DEATH_COLS)
        for col in self.DATE_COLS:
            df[col] = pd.to_datetime(df[col]).dt.date
        return df.set_index('PersonId')

    def download_parliament(self, parliament):
        print(f"Downloading people for parliament #{parliament}...")
        people = self.query_people(parliament)

        filename = self.PARLIAMENTS_DIR + 'parliament-%d-people.json' % parliament
        to_save = {'parliament': parliament, 'people': people}
        with open(filename, 'w') as f:
            json.dump(to_save, f, indent=2)

        filename = self.PARLIAMENTS_DIR + 'parliament-%d-people.csv' % parliament
        df = self.people_df(people, parliament)
        df.to_csv(filename, encoding='utf8')

    def download_all_parliaments(self):
        for parliament in range(1, self.CURRENT_PARLIAMENT + 1):
            parleh.download_parliament(parliament)
    
    def read_all_parliament_csvs(self):
        dfs = []
        for parliament in range(1, self.CURRENT_PARLIAMENT + 1):
            df = pd.read_csv(self.PARLIAMENTS_DIR + 'parliament-%d-people.csv' % parliament, encoding='utf8')
            df.insert(0, 'parliament', parliament)
            dfs.append(df)
        return pd.concat(dfs)

    def combine_parliament_csvs(self):
        print(f"Combining CSV data for all {self.CURRENT_PARLIAMENT} parliaments...")
        df = self.read_all_parliament_csvs()
        df.to_csv(self.PARLIAMENTS_DIR + 'all_parliaments.csv', index=False, encoding='utf8')

    def read_combined_parliaments_csv(self):
        return pd.read_csv(self.PARLIAMENTS_DIR + 'all_parliaments.csv', encoding='utf8')

    def download_profile(self, person_id, person):
        filename = f"{self.PEOPLE_DIR}{person_id}-{person['LastName']},{person['UsedFirstName'].replace(' ', '_')}.json"
        if os.path.exists(filename):
            return False
        print(f"Fetching profile {person_id}...")
        d = self.query_profile(person_id)
        print(f"  Writing to {filename}...")
        with open(filename, 'w') as f:
            json.dump(d, f, indent=2)
        return True

    def download_all_profiles(self):
        df = self.read_combined_parliaments_csv()[['PersonId', 'LastName', 'UsedFirstName']]
        df = df.drop_duplicates().set_index('PersonId').sort_index()
        # df = df[:20]

        print("Downloading profiles for:")
        print(df)
        for person_id, person in df.iterrows():
            try:
                self.download_profile(person_id, person)
            except HTTPError as err:
                print(f"  *** Error: {err}")


parleh = Parleh()
parleh.download_all_parliaments()
parleh.combine_parliament_csvs()
parleh.download_all_profiles()
