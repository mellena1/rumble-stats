from dataclasses import dataclass
import sys
from typing import Dict, List, Tuple, Optional
import psycopg
import matplotlib.pyplot as plt


@dataclass
class TeamStat:
    item: str
    item_count: int
    num_wins: int
    num_games: int
    win_percentage: float


def main():
    with psycopg.connect(
        host="localhost", dbname="rumble", user="rumble", password="rumble"
    ) as conn:
        player_data = get_data(conn)
        plot_data = format_data(player_data)

        image_loc = None
        if len(sys.argv) > 1:
            image_loc = sys.argv[1]
        plot(plot_data, 'team win percentage by item count', image_loc)


def get_data(db: psycopg.Connection) -> List[TeamStat]:
    rows = db.execute(
        """
        SELECT Item, ItemCount, SUM(won) as won, COUNT(*) as games, SUM(won)*1.0/COUNT(*)*1.0 as win_p FROM game_result_by_item_teams_v
        GROUP BY Item, ItemCount
        ORDER BY Item, ItemCount;
    """).fetchall()

    result = []

    for r in rows:
        result.append(TeamStat(r[0], int(r[1]), int(r[2]), int(r[3]), float(r[4])))

    return result


def plot(
    data: Dict[str, Tuple[List[int], List[float]]],
    title: str,
    image_loc: Optional[str] = None,
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


def format_data(data: List[TeamStat]) -> Dict[str, Tuple[List[int], List[float]]]:
    result = {}

    for d in data:
        if d.item not in result:
            result[d.item] = ([], [])
        result[d.item][0].append(d.item_count)
        result[d.item][1].append(d.win_percentage)

    return result


if __name__ == "__main__":
    main()
