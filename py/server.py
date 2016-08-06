"""The Cat Herder server routing module.

"""

import json
import os

from .bottle import (
    abort,
    delete,
    get,
    put,
    redirect,
    request,
    run,
    static_file,
    view,
)

from .model import (
    GAMES,
    EventWeek,
    Participant,
)

DATABASE_PATH = "local/database.json"
PROCESS_ID = os.getpid()


def load_data(game_id, week_id=None):
    """Loads the schelude for the requested week.

    Cat Herder only supports a single event per week, so `week_id` is a unique
    identifier for the schedule.

    """
    if not os.path.exists(DATABASE_PATH):
        with file(DATABASE_PATH, "w+") as f:
            f.write("{}")
    with open(DATABASE_PATH) as f:
        data = json.load(f)
    week_data = data.get(game_id, {}).get(week_id, {})
    return EventWeek.from_dict(game_id, week_data)


def write_data(week_data):
    with open(DATABASE_PATH) as f:
        file_data = json.load(f)
    game_data = file_data.get(week_data.game_id, {})
    game_data[week_data.id] = week_data.to_dict()
    file_data[week_data.game_id] = game_data
    with open(DATABASE_PATH, 'w') as f:
        json.dump(file_data, f)


@get('/static/<filename>')
def static(filename):
    """Loads static files (e.g. CSS, Javascript).

    """
    return static_file(filename, root='static')


@get('/')
def index():
    redirect("/edh")


@get('/<game_id>')
@view('index')
def game(game_id):
    """Loads the main page.

    This loads the current state of the schedule from the database, and adds a
    new participant for the current user.
    """
    if game_id not in GAMES:
        abort(404, "No such event.")
    data = load_data(game_id, "20160808")  # todo
    return {
        "data": data,
        "participants": data.participants + [Participant()],
    }


@put('/game/<game_id>/event/<week_id>/participant/<old_participant_name>')
def update(game_id, week_id, old_participant_name):
    data = request.json
    new_participant_name = data['new_name']
    event_ids = data['event_ids']
    week_data = load_data(game_id, week_id)
    week_data.upsert_participant(
        old_participant_name,
        new_participant_name,
        event_ids,
    )
    write_data(week_data)
    return


@delete('/game/<game_id>/event/<week_id>/participant/<participant_name>')
def delete(game_id, week_id, participant_name):
    week_data = load_data(game_id, week_id)
    week_data.delete_participant(participant_name)
    write_data(week_data)
    return


def run_server():
    with open('temp/server.pid', 'wt') as f:
        f.write(str(PROCESS_ID))
    run(
        host='localhost',
        port=5800,
        debug=True,
    )

run_server()