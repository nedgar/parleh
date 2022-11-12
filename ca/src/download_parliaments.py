from parleh import Parleh

start_parl = 44
end_parl = 44

parleh = Parleh()
# for option in parleh.parliament_options():
#     print(option)
parleh.download_all_parliaments(start_parl, end_parl, include_current=False)
