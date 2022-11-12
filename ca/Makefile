all: download-parliaments data/parliaments/all_parliaments.csv download-profiles role-csvs

data-directories:
	mkdir -p data/parliaments data/people

download-parliaments: data-directories
	cd src && python3 download_parliaments.py

data/parliaments/all_parliaments.csv:
	cd src && python3 combine_parliaments.py

download-profiles: data/parliaments/all_parliaments.csv
	cd src && python3 download_profiles.py

role-csvs: data/people/education.csv data/people/federal_experience.csv data/people/military_experience.csv data/people/municipal_experience.csv data/people/provincial_experience.csv

data/people/education.csv:
	cd src && python3 extract_roles.py Education >../$@

data/people/federal_experience.csv:
	cd src && python3 extract_roles.py FederalExperience >../$@

data/people/military_experience.csv:
	cd src && python3 extract_roles.py MilitaryExperience >../$@

data/people/municipal_experience.csv:
	cd src && python3 extract_roles.py MunicipalExperience >../$@

data/people/provincial_experience.csv:
	cd src && python3 extract_roles.py ProvincialExperience >../$@

clean:
	rm -fr data

zips: data/parliaments/parliaments.zip data/people/people.zip

data/parliaments/parliaments.zip:
	cd data/parliaments && zip parliaments.zip parliament-*.csv parliament-*.json

data/people/people.zip:
	cd data/people && zip people.zip *-*.json

clean-zips:
	rm -f data/parliaments/parliaments.zip
	rm -f data/people/people.zip
