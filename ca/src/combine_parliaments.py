from parleh import Parleh

start_parl = 1
end_parl = 44

parleh = Parleh()
parleh.combine_parliament_csvs(start_parl, end_parl, include_current=True)
