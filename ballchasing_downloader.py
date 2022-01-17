import os
import sys

import ballchasing

client = ballchasing.Api(sys.argv[1])

replays = client.get_replays(player_name='lunaoso', playlist='ranked-rumble')

os.makedirs('./replays', exist_ok=True)

for r in replays:
    client.download_replay(r['id'], 'replays')
