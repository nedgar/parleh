import json
import pandas as pd
import requests

parl_api_url = 'https://lop.parl.ca/ParlinfoWebAPI'
people_search_url = parl_api_url + '/Person/SearchAndRefine'

current_parliament = 43

regular_cols = ['PersonId', 'LastName', 'UsedFirstName', 'StraightDisplayName', 'Gender', 'LanguageEn',
    'PartyEn', 'ConstituencyEn', 'ProvinceEn', 'TypeOfParliamentarianEn', 
    'DateOfBirth', 'DateOfBirthIsApproximate', 
    'CityOfBirthEn', 'ProvinceOfBirthEn', 'CountryOfBirthEn', 'IsCanadianOrigin', 'DiedInOffice']
death_cols = ['DateOfDeath', 'DeceasedOnDuty']
date_cols = ['DateOfBirth', 'DateOfDeath']

def trim(s):
    return s.lstrip('<br>').rstrip('<br>').replace('<br>', '|') if isinstance(s, str) else s

def query_people(parliament):
    params = { 'refiners': '4-%s,' % (current_parliament - parliament + 1) }
    r = requests.get(people_search_url, params= params)
    # print(r.url)
    # print(r.text)
    r.raise_for_status()
    return r.json()

def iter_people(people, parliament):    
    for d in people:
        row = {'Parliament': parliament}
        row.update({col: trim(d[col]) for col in regular_cols})
        dd = d['Death']
        if dd:
            row.update({col: trim(dd[col]) for col in death_cols})
        yield row

def people_df(people, parliament):
    df = pd.DataFrame(iter_people(people, parliament), columns= regular_cols + death_cols)
    for col in date_cols:
        df[col] = pd.to_datetime(df[col]).dt.date
    return df.set_index('PersonId')

def download_people(parliament):
    print(f"Downloading people for parliament #{parliament}...")
    people = query_people(parliament)

    filename = 'parliament-%d-people.json' % parliament
    to_save = {'parliament': parliament, 'people': people}
    with open(filename, 'w') as f:
        json.dump(to_save, f, indent=2)

    filename = 'parliament-%d-people.csv' % parliament
    df = people_df(people, parliament)
    df.to_csv(filename, encoding='utf8')

for parliament in range(1, current_parliament + 1):
    download_people(parliament)
