CREATE OR REPLACE VIEW win_percentage_by_item_players_v AS
    SELECT s.PlayerId, s.Item, s.Used+s.Unused as ItemCount, SUM(player_won_game(s.PlayerID, g.ID)::int) as num_wins, COUNT(g.ID) as num_games, SUM(player_won_game(s.PlayerID, g.ID)::int) / COUNT(g.ID)::real AS win_percentage
    FROM PlayerItemStat s
    INNER JOIN PlayerToGame pg ON pg.GameID = s.GameID AND pg.PlayerID = s.PlayerID
    INNER JOIN Game g ON g.ID = s.GameID
	INNER JOIN Player p ON p.ID = pg.PlayerID
    GROUP BY s.PlayerID, s.Item, ItemCount;
