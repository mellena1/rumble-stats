import logging
from multiprocessing import Pool
import os
import sqlite3
import sys
from typing import Dict, List

import carball


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger("rumbleStats")
db_con = sqlite3.connect("rumbleStats.db")

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


def parse_replays(directory: str):
    replays = []
    for file in os.listdir(directory):
        if not file.endswith(".replay"):
            continue

        full_path = os.path.join(directory, file)
        replays.append(full_path)

    with Pool() as pool:
        pool.map(parse_replay, replays)

    db_con.close()


def parse_replay(file_path: str):
    logger.info("parsing %s", file_path)

    replay_data = get_replay_data(file_path)
    insert_game_data(db_con, file_path, replay_data)
    db_con.commit()


def insert_game_data(db: sqlite3.Connection, file_name: str, game_data: Dict):
    insert_game(db, file_name, game_data)
    insert_players(db, game_data)


def insert_game(db: sqlite3.Connection, file_name: str, game_data: Dict):
    game_id = game_data["gameMetadata"]["id"]
    match_length = game_data["gameMetadata"]["length"]
    match_date = game_data["gameMetadata"]["time"]
    team0_score = game_data["gameMetadata"]["score"]["team0Score"]
    team1_score = game_data["gameMetadata"]["score"]["team1Score"]

    team0_is_orange = game_data["teams"][0]["isOrange"]
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
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING;
    """,
        vals,
    )

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


def insert_players(db: sqlite3.Connection, game_data: Dict):
    game_id = game_data["gameMetadata"]["id"]

    for player in game_data["players"]:
        player_id = player["id"]["id"]
        player_name = player["name"]
        is_orange = player["isOrange"]

        db.execute(
            """
            INSERT INTO Player (ID, UserName) VALUES (?, ?)
            ON CONFLICT DO NOTHING;
        """,
            (player_id, player_name),
        )

        db.execute(
            """
            INSERT INTO PlayerToGame (GameID, PlayerID, IsOrange) VALUES (?, ? ,?)
        """,
            (game_id, player_id, is_orange),
        )

        insert_player_rumble_item(
            db, game_id, player_id, player["stats"]["rumbleStats"]["rumbleItems"]
        )


def insert_player_rumble_item(
    db: sqlite3.Connection, game_id: str, player_id: str, rumble_items: List[Dict]
):
    for item in rumble_items:
        db.execute(
            """
            INSERT INTO PlayerItemStat (GameID, PlayerID, Item, Used, Unused, AverageHold)
            VALUES (?, ?, ?, ?, ?, ?)
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
    db: sqlite3.Connection, game_id: str, is_orange: bool, rumble_items: List[Dict]
):
    for item in rumble_items:
        db.execute(
            """
            INSERT INTO TeamItemStat (GameID, IsOrange, Item, Used, Unused, AverageHold)
            VALUES (?, ?, ?, ?, ?, ?)
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


def insert_goals(db: sqlite3.Connection, game_id: str, goals: List[Dict]):
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
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING;
        """,
            (game_id, player_id, frame, pre_items, item_scored_with),
        )


def get_replay_data(file: str) -> Dict:
    analysis_manager = carball.analyze_replay_file(file, logging_level=logging.FATAL)
    return analysis_manager.get_json_data()


def done_replays(db: sqlite3.Connection) -> List[str]:
    db.execute("""SELECT ReplayFileName FROM Game;""").fetchall()


if __name__ == "__main__":
    parse_replays("replays")
