-- Add constraint on signage_status
PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM signage_status;

DROP TABLE signage_status;

CREATE TABLE signage_status (
    uid   INTEGER PRIMARY KEY
                  NOT NULL,
    name  TEXT    NOT NULL
                  UNIQUE,
    color TEXT,
    icon  BLOB
);

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           SELECT uid,
                                  name,
                                  color,
                                  icon
                             FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;

-- Add Signage Status
INSERT INTO signage_status (
                            name,
                            color
                        )
                        VALUES (
                            'Pending',
                            '#FF0000'
                        );
