CREATE TABLE Player (
    ID TEXT NOT NULL PRIMARY KEY,
    UserName TEXT NOT NULL
);

CREATE TABLE Game (
    ID TEXT NOT NULL PRIMARY KEY,
    ReplayFileName TEXT NOT NULL,
    OrangeScore INT NOT NULL,
    BlueScore INT NOT NULL,
    MatchLengthSeconds REAL NOT NULL,
    MatchDate DATETIME NOT NULL
);

CREATE TABLE PlayerToGame (
    GameID TEXT NOT NULL REFERENCES Game(ID),
    PlayerID TEXT NOT NULL REFERENCES Player(ID),
    IsOrange BOOLEAN NOT NULL,
    PRIMARY KEY(GameID, PlayerID)
);

CREATE TABLE Goal (
    GameID TEXT NOT NULL REFERENCES Game(ID),
    PlayerID TEXT NOT NULL REFERENCES Player(ID),
    Frame INT NOT NULL,
    PreItems BOOLEAN NOT NULL,
    ItemScoredWith TEXT,
    PRIMARY KEY(GameID, PlayerID, Frame)
);

CREATE TABLE PlayerItemStat (
    GameID TEXT NOT NULL REFERENCES Game(ID),
    PlayerID TEXT NOT NULL REFERENCES Player(ID),
    Item TEXT NOT NULL,
    Used INT NOT NULL,
    Unused INT NOT NULL,
    AverageHold REAL NOT NULL,
    PRIMARY KEY(GameID, PlayerID, Item)
);

CREATE TABLE TeamItemStat (
    GameID TEXT NOT NULL REFERENCES Game(ID),
    IsOrange BOOLEAN NOT NULL,
    Item TEXT NOT NULL,
    Used INT NOT NULL,
    Unused INT NOT NULL,
    AverageHold REAL NOT NULL,
    PRIMARY KEY(GameID, IsOrange, Item)
);
