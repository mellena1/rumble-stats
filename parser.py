from datetime import datetime
import logging
from multiprocessing import Pool
import os
import sys
from typing import Dict, List, Tuple

import carball
import psycopg


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger("rumbleStats")

item_translation = {
    'BALL_FREEZE': 'FREEZE',
    'BALL_GRAPPLING_HOOK': 'GRAPPLE',
    'BALL_SPRING': 'HAYMAKER',
    'BALL_VELCRO': 'SPIKES',
    'BATARANG': 'PLUNGER',
    'BOOST_OVERRIDE': 'DISRUPTOR',
    'CAR_SPRING': 'BOOT',
    'GRAVITY_WELL': 'MAGNET',
    'STRONG_HIT': 'GOLD FIST',
    'SWAPPER': 'TELEPORT',
    'TORNADO': 'TORNADO'
}


def main(directory: str):
    with psycopg.connect(
        host="localhost", dbname="rumble", user="rumble", password="rumble"
    ) as conn:
        parse_replays(conn, directory)


def parse_replays(db: psycopg.Connection, directory: str):
    already_in_db = done_replays(db)
    print(already_in_db)

    replays = []
    for file in os.listdir(directory):
        if not file.endswith(".replay"):
            continue

        full_path = os.path.join(directory, file)
        if full_path in already_in_db:
            continue

        replays.append(full_path)

    parsed_replays = []
    with Pool() as pool:
        parsed_replays = pool.map(parse_replay, replays)

    for r in parsed_replays:
        logger.info("inserting %s", r[0])
        insert_game(db, r[0], r[1])

    db.commit()


def parse_replay(file_path: str) -> Tuple[str, Dict]:
    logger.info("parsing %s", file_path)

    return (file_path, get_replay_data(file_path))


def insert_game(db: psycopg.Connection, file_name: str, game_data: Dict):
    game_id = game_data["gameMetadata"]["id"]
    match_length = game_data["gameMetadata"]["length"]
    match_date = datetime.utcfromtimestamp(int(game_data["gameMetadata"]["time"]))
    team0_score = game_data["gameMetadata"]["score"]["team0Score"]
    team1_score = game_data["gameMetadata"]["score"]["team1Score"]

    team0_is_orange = bool(game_data["teams"][0]["isOrange"])
    orange_score = 0
    blue_score = 0
    if team0_is_orange:
        orange_score = team0_score
        blue_score = team1_score
    else:
        orange_score = team1_score
        blue_score = team0_score

    vals = (game_id, file_name, orange_score, blue_score, match_length, match_date)
    db.execute(
        """
        INSERT INTO Game (ID, ReplayFileName, OrangeScore, BlueScore, MatchLengthSeconds, MatchDate)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
    """,
        vals,
    )

    insert_players(db, game_data)

    insert_goals(db, game_id, game_data["gameMetadata"]["goals"])

    insert_team_rumble_item(
        db,
        game_id,
        team0_is_orange,
        game_data["teams"][0]["stats"]["rumbleStats"]["rumbleItems"],
    )
    insert_team_rumble_item(
        db,
        game_id,
        not team0_is_orange,
        game_data["teams"][1]["stats"]["rumbleStats"]["rumbleItems"],
    )


def insert_players(db: psycopg.Connection, game_data: Dict):
    game_id = game_data["gameMetadata"]["id"]

    for player in game_data["players"]:
        player_id = player["id"]["id"]
        player_name = player["name"]
        is_orange = bool(player["isOrange"])

        db.execute(
            """
            INSERT INTO Player (ID, UserName) VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """,
            (player_id, player_name),
        )

        db.execute(
            """
            INSERT INTO PlayerToGame (GameID, PlayerID, IsOrange) VALUES (%s, %s ,%s)
            ON CONFLICT DO NOTHING;
        """,
            (game_id, player_id, is_orange),
        )

        insert_player_rumble_item(
            db, game_id, player_id, player["stats"]["rumbleStats"]["rumbleItems"]
        )


def insert_player_rumble_item(
    db: psycopg.Connection, game_id: str, player_id: str, rumble_items: List[Dict]
):
    for item in rumble_items:
        db.execute(
            """
            INSERT INTO PlayerItemStat (GameID, PlayerID, Item, Used, Unused, AverageHold)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """,
            (
                game_id,
                player_id,
                item_translation[item["item"]],
                item["used"],
                item["unused"],
                item["averageHold"],
            ),
        )


def insert_team_rumble_item(
    db: psycopg.Connection, game_id: str, is_orange: bool, rumble_items: List[Dict]
):
    for item in rumble_items:
        db.execute(
            """
            INSERT INTO TeamItemStat (GameID, IsOrange, Item, Used, Unused, AverageHold)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """,
            (
                game_id,
                is_orange,
                item_translation[item["item"]],
                item["used"],
                item["unused"],
                item["averageHold"],
            ),
        )


def insert_goals(db: psycopg.Connection, game_id: str, goals: List[Dict]):
    for goal in goals:
        player_id = goal["playerId"]["id"]
        frame = goal["frameNumber"]
        pre_items = goal["extraModeInfo"]["preItems"]
        item_scored_with = None
        if goal["extraModeInfo"]["scoredWithItem"]:
            item_scored_with = item_translation[goal["extraModeInfo"]["usedItem"]]

        db.execute(
            """
            INSERT INTO Goal (GameID, PlayerID, Frame, PreItems, ItemScoredWith)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """,
            (game_id, player_id, frame, pre_items, item_scored_with),
        )


def get_replay_data(file: str) -> Dict:
    analysis_manager = carball.analyze_replay_file(file, logging_level=logging.FATAL)
    return analysis_manager.get_json_data()


def done_replays(db: psycopg.Connection) -> List[str]:
    rows = db.execute("""SELECT ReplayFileName FROM Game;""").fetchall()
    return [r[0] for r in rows]


if __name__ == "__main__":
    main("replays")
