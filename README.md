# parleh

Python scripts to download parliamentary data from offical sources.

## Supported sources
### Canadian Library of Parliament (https://lop.parl.ca)
- parliamentarians in each parliament
- candidates for each election

API: https://lop.parl.ca/ParlinfoWebAPI

## Instructions

### Canadian Parliamentarians

- visit https://lop.parl.ca/sites/ParlInfo/default/en_CA/People/parliamentarians
- take note of the latest parliament number
- if "Currently in Office" is shown, add one to the parliament number
- in `ca` directory:
    - edit `download_people.py` and update the `CURRENT_PARLIAMENT` number accordingly
    )
    - in shell, run `make clean download`
        - this downloads the people (parliamentarians) in each parliament to `data/parliaments/parliament-N-people.json` and converts each to a simplified .csv file
    - 

## ParlInfo API examples
- list of parliaments: `curl -H "Accept: application/json" "https://lop.parl.ca/ParlinfowebAPI/Parliament/GetParliamentSessionSittingList" | jq .`
- "refiners" (search options) for parliamentarians: `curl -H "Accept: application/json" "https://lop.parl.ca/ParlinfoWebAPI/Refiner/GetRefiners?collection=Person" | jq . `
    - note that the refiner with `"RefinerId": 4` selects which parliament(s) to include, but the listed options are in reverse order
    - e.g. `"OptionId": 1` is for "Currently in Office", while `"OptionId": 2` is for the most recent parliament, and `"OptionId": 3` is for the previous parliament

