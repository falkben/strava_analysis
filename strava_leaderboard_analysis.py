import json
from pprint import pprint

LEADERBOARD_URLS_FILE = 'data/leaderboards_urls.txt'
LEADERBOARD_DATA_FILE = 'data/leaderboards.json'
BEAT_JOSH_FILE = 'data/segs_beating_josh.txt'

with open(LEADERBOARD_DATA_FILE) as leaderfile:
    data = json.load(leaderfile)

with open(LEADERBOARD_URLS_FILE) as urlsfile:
    urls = [x.strip() for x in urlsfile.readlines()]


urls_beating = set()
for d in data:
    athletes = d['entries']
    a_names = [a['athlete_name'] for a in athletes]
    ranks = [a['rank'] for a in athletes]
    if 'Joshua V.' in a_names:
        idx_josh = a_names.index('Joshua V.')
        idx_ben = a_names.index('Ben F.')
        if ranks[idx_josh] > ranks[idx_ben]:
            # https://www.strava.com/segments/{id}
            url_parts = d['url'].split('/')
            seg_id = url_parts[-2]
            seg_url = 'https://www.strava.com/segments/{}'.format(seg_id)

            print(seg_url)
            urls_beating.add(seg_url)

with open(BEAT_JOSH_FILE, 'w') as beat_file:
    for url in urls_beating:
        beat_file.write('{}\n'.format(url))
