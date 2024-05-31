from config import *
from parleh import Parleh

parleh = Parleh()
print(f"Downloading data for parliaments {start_parl} through {end_parl}, including current: {include_current}")
print("Options:")
for option in parleh.parliament_options():
    print(option)

parleh.download_all_parliaments(start_parl, end_parl, include_current)
parleh.combine_parliament_csvs(start_parl, end_parl, include_current)
