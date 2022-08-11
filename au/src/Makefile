DROPBOX_PARLEH_AU=/Users/nedgar/Dropbox/Parleh/Australia

clean:
	rm -f all-profiles.jl current-*.jl

all-profiles.jl:
	scrapy runspider spider-all.py -O $@ --loglevel INFO

current.jl:
	scrapy runspider spider-current.py -O $@ --loglevel INFO

current-parliamentarians.jl: current.jl
	jq -c 'select(.type == "parliamentarian")' current.jl >$@

current-sessions.jl: current.jl
	jq -c 'select(.type == "session")' current.jl >$@

current-speeches.jl: current.jl
	jq -c 'select(.type == "speech")' current.jl >$@

current-talkers.jl: current.jl
	jq -c 'select(.type == "talker")' current.jl >$@

$(DROPBOX_PARLEH_AU)/all-profiles.zip: all-profiles.jl
	zip $@ $?

$(DROPBOX_PARLEH_AU)/current.zip: current-parliamentarians.jl current-sessions.jl current-speeches.jl current-talkers.jl
	zip $@ $?

zip-to-dropbox: $(DROPBOX_PARLEH_AU)/all-profiles.zip $(DROPBOX_PARLEH_AU)/current.zip
