from dataclasses import dataclass
import sys
from typing import Dict, List, Tuple, Optional
import psycopg
import matplotlib.pyplot as plt


@dataclass
class PlayerStat:
    item: str
    item_count: int
    num_wins: int
    num_games: int
    win_percentage: float


def main():
    with psycopg.connect(
        host="localhost", dbname="rumble", user="rumble", password="rumble"
    ) as conn:
        if len(sys.argv) < 2:
            print("error: must supply a player name")
            exit(1)

        player_name = sys.argv[1]

        player_data = get_data(conn, player_name)
        plot_data = format_data(player_data)

        image_loc = None
        if len(sys.argv) > 2:
            image_loc = sys.argv[2]
        plot(plot_data, player_name, image_loc)


def get_data(db: psycopg.Connection, player: str) -> List[PlayerStat]:
    rows = db.execute(
        """
        SELECT v.item, v.itemcount, SUM(v.num_wins), SUM(v.num_games), SUM(v.num_wins) / SUM(v.num_games) * 100 as win_percentage
        FROM win_percentage_by_item_players_v v
        INNER JOIN Player p ON v.playerID = p.ID
        WHERE p.UserName like %s
        GROUP BY v.item, v.itemcount
        ORDER BY v.Item, v.ItemCount;
    """,
        (player,),
    ).fetchall()

    result = []

    for r in rows:
        result.append(PlayerStat(r[0], int(r[1]), int(r[2]), int(r[3]), float(r[4])))

    return result


def plot(
    data: Dict[str, Tuple[List[int], List[float]]],
    title: str,
    image_loc: Optional[str] = None
):
    fig, ax = plt.subplots()
    ax.set(xlabel="Item Count", ylabel="Win Percentage", title=title)

    max_x = 0
    for item, d in data.items():
        ax.plot(d[0], d[1], label=item)
        max_item_x = max(d[0])
        if max_item_x > max_x:
            max_x = max_item_x

    ax.legend()
    ax.get_xaxis().set_ticks(range(0, max_x + 1))
    if image_loc:
        fig.savefig(image_loc)
    else:
        plt.show()


def format_data(data: List[PlayerStat]) -> Dict[str, Tuple[List[int], List[float]]]:
    result = {}

    for d in data:
        if d.item not in result:
            result[d.item] = ([], [])
        result[d.item][0].append(d.item_count)
        result[d.item][1].append(d.win_percentage)

    return result


if __name__ == "__main__":
    main()
