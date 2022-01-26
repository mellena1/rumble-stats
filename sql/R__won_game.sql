CREATE OR REPLACE FUNCTION player_won_game(PlayerID TEXT, GameID TEXT)
RETURNS BOOLEAN AS $$
    SELECT CASE 
        WHEN pg.IsOrange AND g.OrangeScore > g.BlueScore THEN TRUE
        WHEN pg.IsOrange AND g.OrangeScore < g.BlueScore THEN FALSE
        WHEN (NOT pg.IsOrange) AND g.BlueScore > g.OrangeScore THEN TRUE
        WHEN (NOT pg.IsOrange) AND g.BlueScore < g.OrangeScore THEN FALSE
    END
    FROM PlayerToGame pg
    INNER JOIN Game g ON g.ID = pg.GameID
    WHERE pg.PlayerID = $1 AND pg.GameID = $2;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION team_won_game(IsOrange BOOLEAN, GameID TEXT)
RETURNS BOOLEAN AS $$
    SELECT CASE 
        WHEN $1 AND g.OrangeScore > g.BlueScore THEN TRUE
        WHEN $1 AND g.OrangeScore < g.BlueScore THEN FALSE
        WHEN (NOT $1) AND g.BlueScore > g.OrangeScore THEN TRUE
        WHEN (NOT $1) AND g.BlueScore < g.OrangeScore THEN FALSE
    END
    FROM Game g
    WHERE g.ID = $2;
$$ LANGUAGE SQL;
