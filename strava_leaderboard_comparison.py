import requests
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
import pprint

base = 'https://www.strava.com/api/v3'

with open('token_file.txt', 'r') as f:
    token_data = f.readline()
TOKEN = 'Bearer {}'.format(token_data)


def get(url, session):
    r = session.get(url)
    r.raise_for_status()
    return r


s = requests.Session()
s.headers.update({'Authorization': TOKEN})
s.stream = False

# get ID
athlete_url = '{}/athlete'.format(base)
r = s.get(athlete_url)
data = r.json()
ID = data['id']


# get club id
club_url = '{}/athlete/clubs'.format(base)
r = s.get(club_url)
data = r.json()
club_id = data[0]['id']  # in only one club

# list all activities
list_url = '/athlete/activities'
per_page = 'per_page=100'
data = []
activities = []
i = 1
while not activities or data:
    page_param = '&page={}'.format(i)
    url = '{}{}?{}{}'.format(base, list_url, per_page, page_param)
    r = get(url, session=s)
    data = r.json()
    for activity in data:
        activities.append(activity['id'])
    i += 1


# for each activity get all the segments
act_urls = []
for activity in activities:
    activity_url = '{}/activities/{}'.format(base, activity)
    act_urls.append(activity_url)

get_partial = partial(get, session=s)
with ThreadPool(50) as pool:
    responses = pool.map(get_partial, act_urls)

seg_ids = []
for r in responses:
    data = r.json()
    seg_efforts = data['segment_efforts']
    for seg_effort in seg_efforts:
        seg_ids.append(seg_effort['segment']['id'])

seg_ids = set(seg_ids)

# Get Segment Leaderboard for each segment
club_id_param = 'club_id={}'.format(club_id)
seg_urls = []
for seg in seg_ids:
    seg_url = '{}/segments/{}/leaderboard?{}'.format(base, seg, club_id_param)
    seg_urls.append(seg_url)

print(seg_urls)

with ThreadPool(50) as pool:
    responses = pool.map(get_partial, seg_urls)

seg_leaders = []
for r in responses:
    data = r.json()
    seg_leaders.append(data)

pprint.pprint(seg_leaders)
