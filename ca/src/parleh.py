import json
import os.path
import pandas as pd
import re
import requests
from requests.exceptions import HTTPError

def trim(s):
    return s.lstrip('<br>').rstrip('<br>').replace('<br>', '|') if isinstance(s, str) else s

def num_prefix(str):
    return int(str.split('-')[0])

def name_suffix(str):
    return str.split('-')[-1]

def drop_time(df):
    date_cols = [col for col in df.columns if col.endswith('Date')]
    for col in date_cols:
        df[col] = df[col].str[:10]

def drop_french(df):
    to_drop = [col for col in df.columns if col.endswith('Fr')]
    df.drop(columns=to_drop, inplace=True)
    
def drop_empty_cols(df):
    to_drop = [col for col in df.columns if df[col].count() == 0]
    df.drop(columns=to_drop, inplace=True)

def drop_unsupported_cols(df):
    df.drop(columns=['Documents', 'Senator'], inplace=True, errors='ignore')
    
def cleanup(df):
    drop_time(df)
    drop_french(df)
    # drop_empty_cols(df)
    drop_unsupported_cols(df)

PARL_API_URL = 'https://lop.parl.ca/ParlinfoWebAPI'
PERSON_URL = PARL_API_URL + '/Person/'
PERSON_SEARCH_URL = PERSON_URL + 'SearchAndRefine'
PERSON_PROFILE_URL = PERSON_URL + 'GetPersonWebProfile/%d'
REFINERS_URL = PARL_API_URL + '/Refiner/GetRefiners'

REGULAR_COLS = ['PersonId', 'LastName', 'UsedFirstName', 'StraightDisplayName', 'Gender', 'LanguageEn',
    'PartyEn', 'ConstituencyEn', 'ProvinceEn', 'TypeOfParliamentarianEn', 
    'DateOfBirth', 'DateOfBirthIsApproximate', 
    'CityOfBirthEn', 'ProvinceOfBirthEn', 'CountryOfBirthEn', 'IsCanadianOrigin', 'DiedInOffice']
DEATH_COLS = ['DateOfDeath', 'DeceasedOnDuty']
DATE_COLS = ['DateOfBirth', 'DateOfDeath']

DATA_DIR = '../data/'
PARLIAMENTS_DIR = DATA_DIR + 'parliaments/'
PEOPLE_DIR = DATA_DIR + 'people/'

class Parleh:
    _refiners = None
    
    def query_refiners(self):
        r = requests.get(REFINERS_URL, headers=dict(Accept='application/json'))
        r.raise_for_status()
        # print("refiners body:", r.text)
        return r.json()

    def refiners(self):
        self._refiners = self._refiners or self.query_refiners()
        return self._refiners

    def parliament_refiner(self):
        for refiner in self.refiners():
            if refiner['Name'] == 'Parliament':
                return refiner
        raise Exception("parliament refiner not found")

    def parliament_options(self):
        refiner = self.parliament_refiner()
        options = refiner['Options']
        if options[0]['DisplayNameEn'].startswith('1st'):
            pass
        elif options[-1]['DisplayNameEn'].startswith('1st'):
            options = list(reversed(options))
        for i, option in enumerate(options):
            parliament_number = i + 1
            if option['DisplayNameEn'].startswith(str(parliament_number)):
                option['ParliamentNumber'] = parliament_number
            elif option['DisplayNameEn'] == 'Currently in Office':
                option['Current'] = True
        return options
        
    def query_people(self, parl_option):
        refiner_id = self.parliament_refiner()['RefinerId']
        option_id = parl_option['OptionId']
        r = requests.get(PERSON_SEARCH_URL, params=dict(refiners=f'{refiner_id}-{option_id},'))
        r.raise_for_status()
        return r.json()

    def query_profile(self, person_id):
        r = requests.get(PERSON_PROFILE_URL % person_id)
        r.raise_for_status()
        return r.json()
        
    def iter_people(self, people, parl_id):    
        for d in people:
            row = {'Parliament': parl_id}
            row.update({col: trim(d[col]) for col in REGULAR_COLS})
            dd = d['Death']
            if dd:
                row.update({col: trim(dd[col]) for col in DEATH_COLS})
            yield row

    def people_df(self, people, parl_id):
        df = pd.DataFrame(self.iter_people(people, parl_id), columns= REGULAR_COLS + DEATH_COLS)
        for col in DATE_COLS:
            df[col] = pd.to_datetime(df[col]).dt.date
        return df.set_index('PersonId')

    def download_parliament(self, parl_option):
        parl_num = parl_option.get('ParliamentNumber')
        parl_id = 'current' if parl_option.get('Current') else str(parl_num)

        print(f"Downloading people for parliament {parl_id}...")
        people = self.query_people(parl_option)

        filename = PARLIAMENTS_DIR + f'parliament-{parl_id}-people.json'
        to_save = {'parliament': parl_id, 'people': people}
        with open(filename, 'w') as f:
            json.dump(to_save, f, indent=2)

        filename = PARLIAMENTS_DIR + f'parliament-{parl_id}-people.csv'
        df = self.people_df(people, parl_id)
        df.to_csv(filename, encoding='utf8')

    def download_all_parliaments(self, start_parl, end_parl, include_current=False):
        for parl_option in self.parliament_options():
            is_current = parl_option.get('Current', False)
            parl_num = parl_option.get('ParliamentNumber')
            if (is_current and include_current) or (parl_num is not None and parl_num >= start_parl and parl_num <= end_parl):
                self.download_parliament(parl_option)
    
    def read_parliament_csv(self, parl_id):
        path = os.path.join(PARLIAMENTS_DIR, f'parliament-{parl_id}-people.csv')
        print("reading from:", path)
        df = pd.read_csv(path, encoding='utf8')
        df.insert(0, 'parliament', parl_id)
        return df

    def read_all_parliament_csvs(self, start_parl, end_parl, include_current=False):
        dfs = []
        for parl_num in range(start_parl, end_parl + 1):
            df = self.read_parliament_csv(parl_num)
            dfs.append(df)

        if include_current:
            df = self.read_parliament_csv('current')
            dfs.append(df)

        return pd.concat(dfs)

    def combine_parliament_csvs(self, start_parl, end_parl):
        print(f"Combining CSV data for parliaments {start_parl} to {end_parl}...")
        df = self.read_all_parliament_csvs(start_parl, end_parl)
        df.to_csv(PARLIAMENTS_DIR + 'all_parliaments.csv', index=False, encoding='utf8')

    def read_combined_parliaments_csv(self):
        return pd.read_csv(PARLIAMENTS_DIR + 'all_parliaments.csv', encoding='utf8')

    def download_profile(self, person_id, person):
        filename = f"{PEOPLE_DIR}{person_id}-{person['LastName']},{person['UsedFirstName'].replace(' ', '_')}.json"
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

    # Match people .json files
    def person_files(self):
        pattern = re.compile('[0-9]+-.+\.json$')
        matching_files = filter(lambda d: pattern.match(d), os.listdir(PEOPLE_DIR))
        return sorted(matching_files, key=name_suffix)

    def person_recs(self, n = None):
        files = self.person_files()
        for file in files[:n] if n else files:
            with open(os.path.join(PEOPLE_DIR, file)) as f:
                yield json.load(f)

    def extract_roles(self, role_type):
        person_cols = ['PersonId', 'LastName', 'UsedFirstName']

        rows = []
        for rec in self.person_recs():
            person = {col: rec['Person'][col] for col in person_cols}
            roles = rec[role_type] or []
            for role in roles:
                classes = role.get('Classes')
                if classes is not None:
                    class_names = [c['RoleClassNameEn'] for c in classes]
                    if None in class_names:
                        print(person, "class names:", class_names)
                    role['Classes'] = '|'.join(filter(None, class_names))

                # MP info is a dict with keys OccupationTypeEn, OccupationTypeFr. Use the former.
                mp_info = role.get('MemberOfParliament')
                if mp_info is not None:
                    role['MemberOfParliament'] = mp_info['OccupationTypeEn']
                    
                row = {**person, **role}
                rows.append(row)
                    
        df = pd.DataFrame(rows) if len(rows) > 0 else pd.DataFrame(rows, columns=person_cols)
        # print("df:", df)
        # since run on 2021-09-08, RoleId, PersonRoleId, and StartDate are not available for Education roles
        df = df.sort_values([col for col in ['LastName', 'UsedFirstName', 'PersonId', 'StartDate', 'GraduationYear', 'RoleId'] if col in df.columns])
        df = df.set_index([col for col in ['PersonRoleId', 'PersonId'] if col in df.columns])
        cleanup(df)
        df = df.drop_duplicates()
        return df
