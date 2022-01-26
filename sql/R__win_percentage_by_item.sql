CREATE OR REPLACE VIEW win_percentage_by_item_players_v AS
    SELECT s.PlayerId, s.Item, s.Used+s.Unused as ItemCount, SUM(player_won_game(s.PlayerID, g.ID)::int) as num_wins, COUNT(g.ID) as num_games, SUM(player_won_game(s.PlayerID, g.ID)::int) / COUNT(g.ID)::real AS win_percentage
    FROM PlayerItemStat s
    INNER JOIN PlayerToGame pg ON pg.GameID = s.GameID AND pg.PlayerID = s.PlayerID
    INNER JOIN Game g ON g.ID = s.GameID
    GROUP BY s.PlayerID, s.Item, ItemCount;

CREATE OR REPLACE VIEW game_result_by_item_teams_v AS
    SELECT s.GameID, s.IsOrange, s.Item, s.Used+s.Unused as ItemCount, team_won_game(s.IsOrange, s.GameID)::int as won
    FROM TeamItemStat s
    GROUP BY s.GameID, s.IsOrange, s.Item, ItemCount;
