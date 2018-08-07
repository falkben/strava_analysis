import json
import pprint
import queue
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool

import requests

TOKEN_FILE = 'token_file.txt'
LEADERBOARD_URLS_FILE = 'data/leaderboards_urls.txt'
LEADERBOARD_DATA_FILE = 'data/leaderboards.json'


def get_token():
    with open(TOKEN_FILE, 'r') as f:
        token_data = f.readline().strip()
    return 'Bearer {}'.format(token_data)


def get(url, session):
    r = session.get(url)
    r.raise_for_status()
    return r


def put_resp_queue(url, session, q):
    q.put(get(url, session))


def set_session(TOKEN):
    s = requests.Session()
    s.headers.update({'Authorization': TOKEN})
    s.stream = False
    return s


def get_athlete():
    # get ID
    athlete_url = '{}/athlete'.format(BASE)
    r = get(athlete_url, SESSION)
    data = r.json()
    return data['id']


def get_club():
    club_url = '{}/athlete/clubs'.format(BASE)
    r = get(club_url, SESSION)
    data = r.json()
    return data[0]['id']  # in only one club


def get_activities():
    # list all activities
    list_url = '/athlete/activities'
    per_page = 'per_page=123'
    data = []
    activities = []
    i = 1
    while not activities or data:
        page_param = '&page={}'.format(i)
        url = '{}{}?{}{}'.format(BASE, list_url, per_page, page_param)
        r = get(url, SESSION)
        data = r.json()
        for activity in data:
            activities.append(activity['id'])
        i += 1
    return activities


def get_all_segs(activities):
    # for each activity get all the segments
    act_urls = []
    for activity in activities:
        activity_url = '{}/activities/{}'.format(BASE, activity)
        act_urls.append(activity_url)

    get_partial = partial(get, session=SESSION)
    with ThreadPool(50) as pool:
        # responses = pool.map(get_partial, act_urls)
        responses = pool.map(get_partial, act_urls)

    # parse the responses
    seg_ids = []
    for r in responses:
        data = r.json()
        seg_efforts = data['segment_efforts']
        for seg_effort in seg_efforts:
            seg_ids.append(seg_effort['segment']['id'])

    return set(seg_ids)


def get_leaderboard_urls(seg_ids, club_id):
    # Get Segment Leaderboard for each segment
    club_param = 'club_id={}'.format(club_id)
    lead_urls = []
    for seg in seg_ids:
        seg_url = '{}/segments/{}/leaderboard?{}'.format(BASE, seg, club_param)
        lead_urls.append(seg_url)
    return lead_urls


BASE = 'https://www.strava.com/api/v3'
TOKEN = get_token()
SESSION = set_session(TOKEN)

ID = get_athlete()
CLUB_ID = get_club()
activities = get_activities()
seg_ids = get_all_segs(activities)
lead_urls = get_leaderboard_urls(seg_ids, CLUB_ID)


# load any existing loaderboard data in and only attempt URLs from missing seg urls
existing_urls = []
existing_data = []
try:
    with open(LEADERBOARD_URLS_FILE, 'r') as urlfile:
        for line in urlfile:
            existing_urls.append(line)
        existing_urls = [x.strip() for x in existing_urls]
    with open(LEADERBOARD_DATA_FILE, 'r') as datafile:
        existing_data = json.load(datafile)
except:
    print('no existing data found')

load_urls = set(lead_urls) - set(existing_urls)

q = queue.Queue()

put_resp_queue_partial = partial(put_resp_queue, session=SESSION, q=q)
try:
    with ThreadPool(50) as pool:
        pool.map(put_resp_queue_partial, load_urls)
except Exception as e:
    print(e)

leaderboards = []
leaderboard_urls = []
for r in list(q.queue):
    data = r.json()
    data['url'] = r.url
    leaderboards.append(data)
    leaderboard_urls.append(r.url)

# pprint.pprint(leaderboards)

existing_urls.extend(leaderboard_urls)
leaderboards = leaderboards + existing_data

with open(LEADERBOARD_DATA_FILE, 'w') as savefile:
    json.dump(leaderboards, savefile, indent=2, sort_keys=True)
with open(LEADERBOARD_URLS_FILE, 'w') as savefile:
    for url in existing_urls:
        savefile.write('{}\n'.format(url))
