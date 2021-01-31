clean:
	rm -fr data

data-directories:
	mkdir -p data/parliaments
	mkdir -p data/people

download: data-directories
	cd src && python3 download_people.py

data/parliaments/parliaments.zip:
	cd data/parliaments && zip parliaments.zip parliament-*.csv parliament-*.json

data/people/people.zip:
	cd data/people && zip people.zip *-*.json

clean-zips:
	rm -f data/parliaments/parliaments.zip
	rm -f data/people/people.zip

zips: data/parliaments/parliaments.zip data/people/people.zip
