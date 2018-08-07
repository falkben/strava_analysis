import json
from pprint import pprint

with open('strava_analysis/data/leaderboards.json') as leaderfile:
    data = json.load(leaderfile)

with open('strava_analysis/data/leaderboards_urls.txt') as urlsfile:
    urls = [x.strip() for x in urlsfile.readlines()]


urls_beating = []
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
            urls_beating.append(seg_url)

with open('strava_analysis/data/segs_beating_josh.txt', 'w') as beat_file:
    for url in urls_beating:
        beat_file.write('{}\n'.format(url))
