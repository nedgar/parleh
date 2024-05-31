# parleh

Python scripts to download parliamentary data from offical sources.

## Supported sources
### Canadian Library of Parliament (https://lop.parl.ca)
- parliamentarians in each parliament
- candidates for each election

API: https://lop.parl.ca/ParlinfoWebAPI

## Instructions

### Python 3 environment

This project uses `pipenv` to manage the Python application environment and required packages (e.g. `requests`, `pandas`).
For details, see https://packaging.python.org/en/latest/tutorials/managing-dependencies/.
Steps:
- On Mac, ensure `pipenv` is installed using `brew install pipenv`.
- To switch the command line (shell) to the project's Python environment: `pipenv shell`.
- To install packages (already done): `pipenv install pandas requests`.

### Canadian Parliamentarians

- visit https://lop.parl.ca/sites/ParlInfo/default/en_CA/People/parliamentarians
- take note of the latest parliament number and whether "Currently in Office" is shown
- in `ca` directory:
    - edit `config.py` and update the `start_parl`, `end_parl` numbers and the `include_current` flag accordingly
    - in shell, run `make clean all` which does:
        - downloads the people (parliamentarians) in each parliament to `data/parliaments/parliament-N-people.json`
        - generates a corresponding, simplified CSV file for each: `data/parliaments/parliament-N-people.csv`
        - generates a combined, simplified CSV file: `data/parliaments/all_parliaments.csv` 
        - downloads the full person record for each parliamentarian to `data/people/ID-LAST_NAME,FIRST_NAME.json`
        - compresses the above into two zip files: `data/parliaments/parliaments.zip` and `data/people/people.zip`

## ParlInfo API examples
- list of parliaments: `curl -H "Accept: application/json" "https://lop.parl.ca/ParlinfowebAPI/Parliament/GetParliamentSessionSittingList" | jq .`
- "refiners" (search options) for parliamentarians: `curl -H "Accept: application/json" "https://lop.parl.ca/ParlinfoWebAPI/Refiner/GetRefiners?collection=Person" | jq . `
    - note that the refiner with `"RefinerId": 4` selects which parliament(s) to include, but the listed options are in reverse order
    - e.g. `"OptionId": 1` is for "Currently in Office", while `"OptionId": 2` is for the most recent parliament, and `"OptionId": 3` is for the previous parliament

