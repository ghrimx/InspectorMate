--
-- File generated with SQLiteStudio v3.4.4 on Wed Apr 16 14:47:04 2025
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: schema_migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT current_timestamp
);

-- Table: annotations
CREATE TABLE IF NOT EXISTS annotations (
    uid         INTEGER PRIMARY KEY
                        NOT NULL
                        UNIQUE,
    document_id INTEGER NOT NULL
                        REFERENCES document (id) ON DELETE CASCADE,
    text        TEXT,
    comment     TEXT,
    color       TEXT,
    position    TEXT,
    page_label  TEXT    DEFAULT (0),
    page_number INTEGER DEFAULT (0) 
);


-- Table: document
CREATE TABLE IF NOT EXISTS document (
    refkey                TEXT,
    title                 TEXT    DEFAULT untitled
                                  NOT NULL,
    subtitle              TEXT,
    reference             TEXT,
    status                INTEGER REFERENCES document_status (uid) ON DELETE SET NULL
                                                                   ON UPDATE CASCADE
                                  DEFAULT (0),
    type                  INTEGER REFERENCES document_type (type_id) 
                                  DEFAULT (1),
    note                  TEXT,
    filepath              TEXT    NOT NULL,
    creation_datetime     TEXT    NOT NULL,
    modification_datetime TEXT    NOT NULL,
    fileid                TEXT,
    id                    INTEGER PRIMARY KEY AUTOINCREMENT
                                  NOT NULL
                                  UNIQUE,
    signage_id            INTEGER REFERENCES signage (signage_id) ON DELETE SET NULL,
    workspace_id          INTEGER REFERENCES workspace (workspace_id) ON DELETE CASCADE,
    UNIQUE (
        filepath,
        workspace_id
    )
);


-- Table: document_has_tag
CREATE TABLE IF NOT EXISTS document_has_tag (
    doc_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY (
        tag_id
    )
    REFERENCES tags (tag_id) ON DELETE CASCADE,
    PRIMARY KEY (
        doc_id,
        tag_id
    )
);


-- Table: document_status
CREATE TABLE IF NOT EXISTS document_status (
    uid   INTEGER PRIMARY KEY AUTOINCREMENT
                  NOT NULL,
    name  TEXT    NOT NULL
                  UNIQUE,
    color TEXT,
    icon  TEXT,
    eol   INTEGER NOT NULL
                  DEFAULT (0) 
);


-- Table: connectors
CREATE TABLE IF NOT EXISTS connectors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type         TEXT    NOT NULL,
    value        TEXT    NOT NULL,
    workspace_id         REFERENCES workspace (workspace_id) ON DELETE CASCADE
                         NOT NULL,
    UNIQUE (
        type,
        value,
        workspace_id
    )
);


INSERT INTO document_status (
                                uid,
                                name,
                                color,
                                icon,
                                eol
                            )
                            VALUES (
                                0,
                                'To review',
                                '#000000',
                                NULL,
                                0
                            );

INSERT INTO document_status (
                                uid,
                                name,
                                color,
                                icon,
                                eol
                            )
                            VALUES (
                                1,
                                'In Progress',
                                '#32a852',
                                NULL,
                                0
                            );

INSERT INTO document_status (
                                uid,
                                name,
                                color,
                                icon,
                                eol
                            )
                            VALUES (
                                2,
                                'On Hold',
                                '#e28743',
                                NULL,
                                0
                            );

INSERT INTO document_status (
                                uid,
                                name,
                                color,
                                icon,
                                eol
                            )
                            VALUES (
                                3,
                                'Closed',
                                '#76b5c5',
                                NULL,
                                1
                            );

INSERT INTO document_status (
                                uid,
                                name,
                                color,
                                icon,
                                eol
                            )
                            VALUES (
                                4,
                                'Rejected',
                                '#FF0000',
                                NULL,
                                1
                            );


-- Table: document_type
CREATE TABLE IF NOT EXISTS document_type (
    type_id   INTEGER PRIMARY KEY AUTOINCREMENT
                      NOT NULL,
    type      TEXT    NOT NULL,
    color     TEXT,
    extension TEXT,
    icon      BLOB
);

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              1,
                              'document',
                              NULL,
                              NULL,
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAV9JREFUeNqMkrFOwzAQhs9OAgzkAWBnad8izKzwCrxFq0qVeAAkOlfqhthRJV6hGdhg654IJRFVYzvcXWMrEDfipPNZ5/Pn+22LpmmA7HY6vcFwAcP2Zoz5NFrDy3zOidCu4MLlcjJZ7HGxJjcGNMLtAWmawnK9vsepQP+w+6QDaC0Mbapr9v1uB99VBWVZQlEUHJ9nswXWXWP5VQ+gEUBoiWMUBHAWRXAShhBKCQJzWZbB42oFyWj09L7Z3Nl9YacDSZslY4AhzpSCJElYThzH8JqmeQ+gqIMOwAdRKNHW9gBaKSeha38hdAjV+gAHCagZ2pN8kOAAkH0JmHQdDEACjOoIgO+A74Hfxw8JMK+8EuradWDs+3ogLAFr/RKoA3yqIYhoa/0SbAcDEMp7JeC35bm9g2MQ0an9BfjK81PXZvuh6OeJNjKUvjV6t9YBqrLcno/HD/APQ8jWzn8EGACxU8j1qPzZewAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              2,
                              'text',
                              NULL,
                              '.txt',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAfJJREFUeNqMUj1rG0EQnbtboYhESFfYJp8ESYFgo8qNazltuvyI/InYYFKkDoG4NqjLHwiGgCGFK3N9jCVIYYyRzrY+zljSKu+NtdIanJCFudnd2ffmzcwF77a2hCsIgrdwj+Xf64e19thOJjKdTvXCuA38k73t7d0bBEc0a2WCmIsnSSJ7+/vvmQv2yzGGZJtZYAkajdRurq8lGwyk3+9Lr9dT/21nZxfvNoF75QjMBODZCkgd4puLooXo8VjGIO52u/Kl2ZTG6urXz83mB0Q+KoFdEIQE/zw6UtnlclmGw6G8rtWUpNFo6H2xWJTvSZLOFYx9BSCoAcBS+DiOY3mQy91RoluUuygBAb+EVqul2TudjpKczBpZKpUkyzKp1+sCzL0EWkK1Wp1nd0qc8RzhDTDhogSPgLTtdnsOdEroeWZPnq6soJr7CbQHToHfB3+fC0MSeCVg5r4C1wOOjUA/ez6fl5dQAMxfSoCCSqWiB2Yj8BmaRyJLVbBAB+KVcHl6Kg+Xlu5Mwcll1hdQgPaKzEbIRrsSBufnYo4PDuT5xoYU4tjw8s36+m0P2Hmc6cPbGSkJkfjFTZam8vvwUGMFbJYv0zTvdRPvQ80WwdMMfm9jjETwfEsMscxagC1fnZ1dPFpb+yT/sWyWXRDDdvwRYAB4+UxUy0hc0wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              3,
                              'tabular',
                              NULL,
                              '.xls',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkJJREFUeNqMU11LVGEQfs7HVksttUSGYZBEGLvdFmGCtdKFRTddRS6RRFA/QJE2FSqobopCsLtgaTO66UYEkb7ACyGEsyC0YETQTYuwa8Z61PPVPK/nnBDaaGB2Zp9553ln5p2j3X99HfMLrdA07QKAVvxb3vm+/8X3PARBgMrsLEyiHe01VL6mDxRHR59tSNCh+j48OcSDFMuyUJyZuSGuJrpI7GhXFzSp4IP43c2u3Lv7EDqPXUW5XMbl3l5cLBRuCvxWiBWJ6XhO9/Cl501rvvuqn+2hVqthrFRCLpMZf1oqDUvoniJYc9ekVA8jpbxK6O+5hfcLb/Ct+hl3+l6AcVPXkcvlVDupVArTllWPLlAEbuCqg9fO3sb49IgKtO/PxPg2U0blunBlLhTX87SIQLcdWx3MnxnE2FRB7ACIncqcVzj9HYmEImElbMdzXU2UFvqquyoTdzA5XwT9J1NDuNIzpCxxYgnDiEmMTQI9IjCjCtr2HVFKeTw5sFlqWIEuSSShGGJdIdgyA83QcO5EXzz5yCfOOAkoJDGkDSGIZ8Bn/Jh/1Nl0D7Jtx2MCVQFbcJw/FciunV7/tRMrix2DnyYmHsqqgrvnh1tI64fTR7iGW1r4YekINg4TVvfwNiYpy//qreQ3JCEetdBYWoJpvazg4Mk9SKbT6rvgM+lhBX8jYabdaJh2vY7vc3MqlhSn5We9vj0ukySSQAIOjWrKAE0+o1ieZQ5zeWtStGWlWl3elc0+wH+Ib9vLzGHfvwUYAKq6LE11+rJNAAAAAElFTkSuQmCC'
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              4,
                              'image',
                              NULL,
                              '.jpg',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              5,
                              'presentation',
                              NULL,
                              '.ppt',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAlZJREFUeNqMU01oE0EU/mZ3YrPFCK3aqK2I6KHQ2oKIPxC15CAU9CKo4ElExIJH7aUtxR/8Qb148lyJ9eRZqQaFQAP1kPRk0eChvbTRbltMN5ud3fW9abIqGHHg5c1+b75v3nvzIpbvH8RV5zSEEGcA7MS/VzYIgi+B7yMMQ3zK5SAZvRHP45FzZNfE+PizGgU9tiCAT4f4IK9CoYCJqalrtBVknxnrTqUgKIP3tD/Z7Ep3xwF8P3UPxWIRFwcHcXZkZIjgdySsRUT5dl+4bazYNOdvd/qxdOU1stlshD3NZMbI3eW9VFUPYeBDLS9g7dUoRCwGmeyGdfgCZHsXOC4NA+l0WpeTSCTwplCwG2KGqtZIQMF+OQxnbhrxY5cQP34ZP3LPNc7xTVJqEWq0JinfF2TsIT3HRagU1ktFhK4Lo6sf1dIMnK+z2EI4xy3KaoOptIivlGhkINV6FYHvwWjfC7f0EfPX9+tAy75DGud4zDSj+s0NASMqwXOoBF8hcf4WzM4+ejqpPX8zznGDSCwSp0zYKxIgY89NrME0BFqTe9B688UfL8A4x4167Uw2qRfq9xJ8T32YPZdsOgdW74lIICrB86ISJL3NwJy5HY8TA8Mzk5MPaVTBsxfUp5A9Y40ldC9/9UBmVrfibWeKUX0P38Yk7flbd4p+6yKMN0qolMuQT6aXsPvoAqy2Nv2/4Gcy6hn8TYSZTqUiHdvGfD6vYxZtOlZtuyVKk0WIwALcNDZJDZQ0UCZ5Pssc5vKtFlnH2uLiyuaengf4jxU4zgpzuB0/BRgAO1gmOtGmT+8AAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              6,
                              'tabular',
                              NULL,
                              '.xlsx',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkJJREFUeNqMU11LVGEQfs7HVksttUSGYZBEGLvdFmGCtdKFRTddRS6RRFA/QJE2FSqobopCsLtgaTO66UYEkb7ACyGEsyC0YETQTYuwa8Z61PPVPK/nnBDaaGB2Zp9553ln5p2j3X99HfMLrdA07QKAVvxb3vm+/8X3PARBgMrsLEyiHe01VL6mDxRHR59tSNCh+j48OcSDFMuyUJyZuSGuJrpI7GhXFzSp4IP43c2u3Lv7EDqPXUW5XMbl3l5cLBRuCvxWiBWJ6XhO9/Cl501rvvuqn+2hVqthrFRCLpMZf1oqDUvoniJYc9ekVA8jpbxK6O+5hfcLb/Ct+hl3+l6AcVPXkcvlVDupVArTllWPLlAEbuCqg9fO3sb49IgKtO/PxPg2U0blunBlLhTX87SIQLcdWx3MnxnE2FRB7ACIncqcVzj9HYmEImElbMdzXU2UFvqquyoTdzA5XwT9J1NDuNIzpCxxYgnDiEmMTQI9IjCjCtr2HVFKeTw5sFlqWIEuSSShGGJdIdgyA83QcO5EXzz5yCfOOAkoJDGkDSGIZ8Bn/Jh/1Nl0D7Jtx2MCVQFbcJw/FciunV7/tRMrix2DnyYmHsqqgrvnh1tI64fTR7iGW1r4YekINg4TVvfwNiYpy//qreQ3JCEetdBYWoJpvazg4Mk9SKbT6rvgM+lhBX8jYabdaJh2vY7vc3MqlhSn5We9vj0ukySSQAIOjWrKAE0+o1ieZQ5zeWtStGWlWl3elc0+wH+Ib9vLzGHfvwUYAKq6LE11+rJNAAAAAElFTkSuQmCC'
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              7,
                              'image',
                              NULL,
                              '.png',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              8,
                              'image',
                              NULL,
                              '.jpeg',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              9,
                              'image',
                              NULL,
                              '.gif',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              10,
                              'msword',
                              NULL,
                              '.doc',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkdJREFUeNqMU01oE0EU/mZ30jZqwJRStYJURUlb0HoQAhYrQZAqBZGcevKoNz1YhCK9eKi9KCIqCAqFWLx58VCC0mrRgFA3ByFQb6JQq9laTLdmZye+N9ldPRhx4O23+36+ee/Li8iPF4GOVxBCjALYhX+fF1rrDzoI0Gg0UFlchGSv8A9By3LPzOTk/ToFfTatEVASJ/JxHAczxeIFTidbZl9maAgif6U4T67hVlf27t6C8/lelMtljI2M4NzExEVyPydiQyL9ejD89Naplj2fvTTH46FareJOoYBcf/+924XCNQpdNwSbnoJT+YarN0sYO3MAj58txzh1OQuOS8tCLpcz46RSKcw5jhtdYG3WFPr2plH3Aowe34OGasTIfo63SWlIuBM+KggEGSOkV/OhKNnSwLv3X7G/J4WlENnP8Y5EonmdUoYkUEpEHciNHwq+r5GwBOZff8KRTBcWCAcJ2c/xhG3HmthNAiseIeogISy8LH3G4UynwUHCqAOLipiEO2FUREDGSCJucFs2HkyfjG95cve0QfZz3Apn52KbtFB/juD/DBb6jj1quQfZoztigngE349HkPTLnGjb6mLnwaXxt7OzN2hVwbunwy1kZF90hNHytwZSiDfo2rfeFJhFoScXGeRvoxQ9QxL2RyPUVlchv1Qeon17Fsl0uvm/oAQr7OBvJFzp1WrSc118LJVMLEkv3d9dtz1uk0mogAlYNDZJAkpaKJuQc7mGa/nWJFn3+srK2raBgSn8x9Get8Y1LMcvAQYAwxgjb1L+BBMAAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              11,
                              'msword',
                              NULL,
                              '.docx',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkdJREFUeNqMU01oE0EU/mZ30jZqwJRStYJURUlb0HoQAhYrQZAqBZGcevKoNz1YhCK9eKi9KCIqCAqFWLx58VCC0mrRgFA3ByFQb6JQq9laTLdmZye+N9ldPRhx4O23+36+ee/Li8iPF4GOVxBCjALYhX+fF1rrDzoI0Gg0UFlchGSv8A9By3LPzOTk/ToFfTatEVASJ/JxHAczxeIFTidbZl9maAgif6U4T67hVlf27t6C8/lelMtljI2M4NzExEVyPydiQyL9ejD89Naplj2fvTTH46FareJOoYBcf/+924XCNQpdNwSbnoJT+YarN0sYO3MAj58txzh1OQuOS8tCLpcz46RSKcw5jhtdYG3WFPr2plH3Aowe34OGasTIfo63SWlIuBM+KggEGSOkV/OhKNnSwLv3X7G/J4WlENnP8Y5EonmdUoYkUEpEHciNHwq+r5GwBOZff8KRTBcWCAcJ2c/xhG3HmthNAiseIeogISy8LH3G4UynwUHCqAOLipiEO2FUREDGSCJucFs2HkyfjG95cve0QfZz3Apn52KbtFB/juD/DBb6jj1quQfZoztigngE349HkPTLnGjb6mLnwaXxt7OzN2hVwbunwy1kZF90hNHytwZSiDfo2rfeFJhFoScXGeRvoxQ9QxL2RyPUVlchv1Qeon17Fsl0uvm/oAQr7OBvJFzp1WrSc118LJVMLEkv3d9dtz1uk0mogAlYNDZJAkpaKJuQc7mGa/nWJFn3+srK2raBgSn8x9Get8Y1LMcvAQYAwxgjb1L+BBMAAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              12,
                              'text',
                              NULL,
                              '.md',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAfJJREFUeNqMUj1rG0EQnbtboYhESFfYJp8ESYFgo8qNazltuvyI/InYYFKkDoG4NqjLHwiGgCGFK3N9jCVIYYyRzrY+zljSKu+NtdIanJCFudnd2ffmzcwF77a2hCsIgrdwj+Xf64e19thOJjKdTvXCuA38k73t7d0bBEc0a2WCmIsnSSJ7+/vvmQv2yzGGZJtZYAkajdRurq8lGwyk3+9Lr9dT/21nZxfvNoF75QjMBODZCkgd4puLooXo8VjGIO52u/Kl2ZTG6urXz83mB0Q+KoFdEIQE/zw6UtnlclmGw6G8rtWUpNFo6H2xWJTvSZLOFYx9BSCoAcBS+DiOY3mQy91RoluUuygBAb+EVqul2TudjpKczBpZKpUkyzKp1+sCzL0EWkK1Wp1nd0qc8RzhDTDhogSPgLTtdnsOdEroeWZPnq6soJr7CbQHToHfB3+fC0MSeCVg5r4C1wOOjUA/ez6fl5dQAMxfSoCCSqWiB2Yj8BmaRyJLVbBAB+KVcHl6Kg+Xlu5Mwcll1hdQgPaKzEbIRrsSBufnYo4PDuT5xoYU4tjw8s36+m0P2Hmc6cPbGSkJkfjFTZam8vvwUGMFbJYv0zTvdRPvQ80WwdMMfm9jjETwfEsMscxagC1fnZ1dPFpb+yT/sWyWXRDDdvwRYAB4+UxUy0hc0wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              13,
                              'presentation',
                              NULL,
                              '.pptx',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAlZJREFUeNqMU01oE0EU/mZ3YrPFCK3aqK2I6KHQ2oKIPxC15CAU9CKo4ElExIJH7aUtxR/8Qb148lyJ9eRZqQaFQAP1kPRk0eChvbTRbltMN5ud3fW9abIqGHHg5c1+b75v3nvzIpbvH8RV5zSEEGcA7MS/VzYIgi+B7yMMQ3zK5SAZvRHP45FzZNfE+PizGgU9tiCAT4f4IK9CoYCJqalrtBVknxnrTqUgKIP3tD/Z7Ep3xwF8P3UPxWIRFwcHcXZkZIjgdySsRUT5dl+4bazYNOdvd/qxdOU1stlshD3NZMbI3eW9VFUPYeBDLS9g7dUoRCwGmeyGdfgCZHsXOC4NA+l0WpeTSCTwplCwG2KGqtZIQMF+OQxnbhrxY5cQP34ZP3LPNc7xTVJqEWq0JinfF2TsIT3HRagU1ktFhK4Lo6sf1dIMnK+z2EI4xy3KaoOptIivlGhkINV6FYHvwWjfC7f0EfPX9+tAy75DGud4zDSj+s0NASMqwXOoBF8hcf4WzM4+ejqpPX8zznGDSCwSp0zYKxIgY89NrME0BFqTe9B688UfL8A4x4167Uw2qRfq9xJ8T32YPZdsOgdW74lIICrB86ISJL3NwJy5HY8TA8Mzk5MPaVTBsxfUp5A9Y40ldC9/9UBmVrfibWeKUX0P38Yk7flbd4p+6yKMN0qolMuQT6aXsPvoAqy2Nv2/4Gcy6hn8TYSZTqUiHdvGfD6vYxZtOlZtuyVKk0WIwALcNDZJDZQ0UCZ5Pssc5vKtFlnH2uLiyuaengf4jxU4zgpzuB0/BRgAO1gmOtGmT+8AAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              14,
                              'pdf',
                              NULL,
                              '.pdf',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAjtJREFUeNqMU79PFEEU/nZ2jvPUM5JwFzUaEmww/AOGgsCGhsICSxIqCrQjQK4hQmOBhRdCZeslFyjFDghXk2gue8VVmkiUEM9LXNScy93tzvreOLtuYYyTfPsmb973vR8za70FsLm+DsuyHtD2Jv69akqp9yoMEUWRdkj+zFUqqM7P36psbLzo0WGfoRRCCooDXddF5fDwEW0twrtY0aoDzy8Dy7Y5CQkBoU/oEWyqLru4iEajgbmZGTxcW3tM7iMS1iJWE4iu0SZLEIZ4QfAJHcJPwtDZGWq1WtLHdrX6hMxT3UKQyioyGdzodvFxZATq5ATK+KUQcBxHt5PP57Hvul4sJgJTKmcNR0fRbzYxMD2dtMB2QEotQoPWpCAMLQJbiG6qZHt8HO1yGdcXFpCdnETXiFyiytIiYRBYBLYQF6bX3OwsCqUSrkxNAXQD93Z3cXt1VYtkbDsRsX8LiFhA+qbM+1tb+Ly3hy8HB/har+NHq6WvkxMIIrEIL5tsQALxDCRnYLweHtaOyAxVmX3PCMBUYlMbJGAlAhRQpkEuK0NSKTLj7tJSIqAr4Bb6/T8VUPDKh2Jx5ZXjlN7s7Dyjp6qJyrxCtuxLXh7fQrqF/UIB7sQEe3UezsYkbc3jApUNI8L+uIVOuw35kj53Tk+RGxzU/wVfkzAV/E2EmX6nI33Pw6fjY32Wo03xm+dlkzJZhAgswENjSBqg5Gsky7HMYS5nzRGK31ut86tjY5v4j6V8/5w5PI5fAgwAUXIN2+nu/TQAAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              15,
                              'email',
                              NULL,
                              '.msg',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA2lpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wUmlnaHRzPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvcmlnaHRzLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcFJpZ2h0czpNYXJrZWQ9IkZhbHNlIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOkE4NkNGMEIxRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOkE4NkNGMEIwRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDUzMgV2luZG93cyI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ1dWlkOkFDMUYyRTgzMzI0QURGMTFBQUI4QzUzOTBEODVCNUIzIiBzdFJlZjpkb2N1bWVudElEPSJ1dWlkOkM5RDM0OTY2NEEzQ0REMTFCMDhBQkJCQ0ZGMTcyMTU2Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+rI6PHAAAAkRJREFUeNqkU0tIG1EUPZlMPsR8bFoQk4D2gxprjWlqu+iqdJ2FIl1XCRUX0p2uBHHhvrgQa9CtFNFFIIuua7soEkRBbZtGSokloUmMTUxm3kx6bxokBVtKvXDnMe+dc+6Ze98YarUaLhMSLhnyk9nZMK2e/+SnZU3TvM/C4cXBnh64nc5/YuWKRbw/OMDLWGxC0oQwhIj8bm8PmUIBQtf/moxhLHOYKwkhJJfdjmB3N97u7CCTz/+ZTGeMYSxzmCsJVZU0moSTNu76/dhKJJDJ5SA07bfkPT5jDGOZw1yZH6yuEsjBIr29eLO9jQeBACxULb+0BHF8jHKlgjtuN2pWK05MJpi9XtxLpa7LKguQmiJEvUEmiwU+nw9bJOJfXEQnicrDw7ANDcHS1VXHKKkUfiws4NHu7n1JVRRJazgoUZVvZNXX1oZgXx9KR0eQQyFcmZ5Gdn0dybExfIhEoKkq7JOTsFUqrnMHTP5OHb7a2gqDJMHucEDQWLny1/l5GGUZN1dW6g4+jY/jFn0aajWJHRjPuHI2CxeRJKPxvOtWs7luW0km0T41hcToaF2gSg44dE0zyYVczvyZrHZ2dMBMhOY4YyC5k6lpp/E4gquryMdiuE1OihsbPAWbwTUwENF1/cZFN+7V4eHTh5ub7bLHg/zyMleEsZEt1OzX0egXmchR0bDUHIFyGc5qdbC0tmZvGRlxXJuZ+fX3kaPK3BxO0unTkqp+NDj6+3GRQHx/n5fHNNznlB5GKE1J72naf/FTgAEAy/9ZHAO9HmIAAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              16,
                              'email',
                              NULL,
                              '.eml',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA2lpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wUmlnaHRzPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvcmlnaHRzLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcFJpZ2h0czpNYXJrZWQ9IkZhbHNlIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOkE4NkNGMEIxRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOkE4NkNGMEIwRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDUzMgV2luZG93cyI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ1dWlkOkFDMUYyRTgzMzI0QURGMTFBQUI4QzUzOTBEODVCNUIzIiBzdFJlZjpkb2N1bWVudElEPSJ1dWlkOkM5RDM0OTY2NEEzQ0REMTFCMDhBQkJCQ0ZGMTcyMTU2Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+rI6PHAAAAkRJREFUeNqkU0tIG1EUPZlMPsR8bFoQk4D2gxprjWlqu+iqdJ2FIl1XCRUX0p2uBHHhvrgQa9CtFNFFIIuua7soEkRBbZtGSokloUmMTUxm3kx6bxokBVtKvXDnMe+dc+6Ze98YarUaLhMSLhnyk9nZMK2e/+SnZU3TvM/C4cXBnh64nc5/YuWKRbw/OMDLWGxC0oQwhIj8bm8PmUIBQtf/moxhLHOYKwkhJJfdjmB3N97u7CCTz/+ZTGeMYSxzmCsJVZU0moSTNu76/dhKJJDJ5SA07bfkPT5jDGOZw1yZH6yuEsjBIr29eLO9jQeBACxULb+0BHF8jHKlgjtuN2pWK05MJpi9XtxLpa7LKguQmiJEvUEmiwU+nw9bJOJfXEQnicrDw7ANDcHS1VXHKKkUfiws4NHu7n1JVRRJazgoUZVvZNXX1oZgXx9KR0eQQyFcmZ5Gdn0dybExfIhEoKkq7JOTsFUqrnMHTP5OHb7a2gqDJMHucEDQWLny1/l5GGUZN1dW6g4+jY/jFn0aajWJHRjPuHI2CxeRJKPxvOtWs7luW0km0T41hcToaF2gSg44dE0zyYVczvyZrHZ2dMBMhOY4YyC5k6lpp/E4gquryMdiuE1OihsbPAWbwTUwENF1/cZFN+7V4eHTh5ub7bLHg/zyMleEsZEt1OzX0egXmchR0bDUHIFyGc5qdbC0tmZvGRlxXJuZ+fX3kaPK3BxO0unTkqp+NDj6+3GRQHx/n5fHNNznlB5GKE1J72naf/FTgAEAy/9ZHAO9HmIAAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              17,
                              'email',
                              NULL,
                              '.email',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA2lpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wUmlnaHRzPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvcmlnaHRzLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcFJpZ2h0czpNYXJrZWQ9IkZhbHNlIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOkE4NkNGMEIxRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOkE4NkNGMEIwRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDUzMgV2luZG93cyI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ1dWlkOkFDMUYyRTgzMzI0QURGMTFBQUI4QzUzOTBEODVCNUIzIiBzdFJlZjpkb2N1bWVudElEPSJ1dWlkOkM5RDM0OTY2NEEzQ0REMTFCMDhBQkJCQ0ZGMTcyMTU2Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+rI6PHAAAAkRJREFUeNqkU0tIG1EUPZlMPsR8bFoQk4D2gxprjWlqu+iqdJ2FIl1XCRUX0p2uBHHhvrgQa9CtFNFFIIuua7soEkRBbZtGSokloUmMTUxm3kx6bxokBVtKvXDnMe+dc+6Ze98YarUaLhMSLhnyk9nZMK2e/+SnZU3TvM/C4cXBnh64nc5/YuWKRbw/OMDLWGxC0oQwhIj8bm8PmUIBQtf/moxhLHOYKwkhJJfdjmB3N97u7CCTz/+ZTGeMYSxzmCsJVZU0moSTNu76/dhKJJDJ5SA07bfkPT5jDGOZw1yZH6yuEsjBIr29eLO9jQeBACxULb+0BHF8jHKlgjtuN2pWK05MJpi9XtxLpa7LKguQmiJEvUEmiwU+nw9bJOJfXEQnicrDw7ANDcHS1VXHKKkUfiws4NHu7n1JVRRJazgoUZVvZNXX1oZgXx9KR0eQQyFcmZ5Gdn0dybExfIhEoKkq7JOTsFUqrnMHTP5OHb7a2gqDJMHucEDQWLny1/l5GGUZN1dW6g4+jY/jFn0aajWJHRjPuHI2CxeRJKPxvOtWs7luW0km0T41hcToaF2gSg44dE0zyYVczvyZrHZ2dMBMhOY4YyC5k6lpp/E4gquryMdiuE1OihsbPAWbwTUwENF1/cZFN+7V4eHTh5ub7bLHg/zyMleEsZEt1OzX0egXmchR0bDUHIFyGc5qdbC0tmZvGRlxXJuZ+fX3kaPK3BxO0unTkqp+NDj6+3GRQHx/n5fHNNznlB5GKE1J72naf/FTgAEAy/9ZHAO9HmIAAAAASUVORK5CYII='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              18,
                              'tabular',
                              NULL,
                              '.xlsm',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkJJREFUeNqMU11LVGEQfs7HVksttUSGYZBEGLvdFmGCtdKFRTddRS6RRFA/QJE2FSqobopCsLtgaTO66UYEkb7ACyGEsyC0YETQTYuwa8Z61PPVPK/nnBDaaGB2Zp9553ln5p2j3X99HfMLrdA07QKAVvxb3vm+/8X3PARBgMrsLEyiHe01VL6mDxRHR59tSNCh+j48OcSDFMuyUJyZuSGuJrpI7GhXFzSp4IP43c2u3Lv7EDqPXUW5XMbl3l5cLBRuCvxWiBWJ6XhO9/Cl501rvvuqn+2hVqthrFRCLpMZf1oqDUvoniJYc9ekVA8jpbxK6O+5hfcLb/Ct+hl3+l6AcVPXkcvlVDupVArTllWPLlAEbuCqg9fO3sb49IgKtO/PxPg2U0blunBlLhTX87SIQLcdWx3MnxnE2FRB7ACIncqcVzj9HYmEImElbMdzXU2UFvqquyoTdzA5XwT9J1NDuNIzpCxxYgnDiEmMTQI9IjCjCtr2HVFKeTw5sFlqWIEuSSShGGJdIdgyA83QcO5EXzz5yCfOOAkoJDGkDSGIZ8Bn/Jh/1Nl0D7Jtx2MCVQFbcJw/FciunV7/tRMrix2DnyYmHsqqgrvnh1tI64fTR7iGW1r4YekINg4TVvfwNiYpy//qreQ3JCEetdBYWoJpvazg4Mk9SKbT6rvgM+lhBX8jYabdaJh2vY7vc3MqlhSn5We9vj0ukySSQAIOjWrKAE0+o1ieZQ5zeWtStGWlWl3elc0+wH+Ib9vLzGHfvwUYAKq6LE11+rJNAAAAAElFTkSuQmCC'
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              19,
                              'image',
                              NULL,
                              '.jpg',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              20,
                              'archive',
                              NULL,
                              '.zip',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAh5JREFUeNp0UztoFFEUPTOzoxKDupINEgjoWAoWWaIIVrLYaiUKWqRJsAkKNilEVCQWgmIj2lhYGLMoWtiYtRNBVkH8gBIyLEYsNJFoNnF3531897757aIXDvfd++4977yfU78KNgcYM24nYnsToj1xB0u3xzFQDrAR3dbQwF0aFLS2GeN2jU4+OQ8pLcH9H5ibCxCGIconSlmr56F+88jlJEwJjLkQEXQUcRAEAYrFIhPozpa0yPF9mB43JZAqI1BmdR0rICMCMpXLOa4L05MRqEyBp/9DkM/BEJge758KqFBJkSaq1WqsQOT6uxW4RBDDUzKCFBa095P7FrgoyRE0FNeSKCF7CUxGCcGgQ7w047BPcp6/AV8/zVsCjTL1dRFoI1XF2D/8EZVKhZVQ7JrrW/w8z+NDF9WkqR+j8+tRECHBq8U9qNVqmDo1kOZWV1awY3gI652OVUEKRLwXA49kyhgjpdesYPreEsc8J+0WV1strqe+/C14Vr59SG9/HmAF545t5pySHoSw21trt1kB38L7L/kzkPxoCHu3vmAF12bXkDwwGfvxRinbwoVZs1oDaHWwSStbQHj36yArOHvUtzkz1zLSyS8vr3M99dGD6LvyCIO//6DfdVz4BZ8xsu0lK7j+OOKY5prNJvuJh/1Pn3/AA9PXZ34xthsMnT6MM8Egduf/7NRMoT59XIz2fGWE37Fw6xlumOG3vwIMAJg6gUpZKWmMAAAAAElFTkSuQmCC'
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              21,
                              'text',
                              NULL,
                              '.csv',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAfJJREFUeNqMUj1rG0EQnbtboYhESFfYJp8ESYFgo8qNazltuvyI/InYYFKkDoG4NqjLHwiGgCGFK3N9jCVIYYyRzrY+zljSKu+NtdIanJCFudnd2ffmzcwF77a2hCsIgrdwj+Xf64e19thOJjKdTvXCuA38k73t7d0bBEc0a2WCmIsnSSJ7+/vvmQv2yzGGZJtZYAkajdRurq8lGwyk3+9Lr9dT/21nZxfvNoF75QjMBODZCkgd4puLooXo8VjGIO52u/Kl2ZTG6urXz83mB0Q+KoFdEIQE/zw6UtnlclmGw6G8rtWUpNFo6H2xWJTvSZLOFYx9BSCoAcBS+DiOY3mQy91RoluUuygBAb+EVqul2TudjpKczBpZKpUkyzKp1+sCzL0EWkK1Wp1nd0qc8RzhDTDhogSPgLTtdnsOdEroeWZPnq6soJr7CbQHToHfB3+fC0MSeCVg5r4C1wOOjUA/ez6fl5dQAMxfSoCCSqWiB2Yj8BmaRyJLVbBAB+KVcHl6Kg+Xlu5Mwcll1hdQgPaKzEbIRrsSBufnYo4PDuT5xoYU4tjw8s36+m0P2Hmc6cPbGSkJkfjFTZam8vvwUGMFbJYv0zTvdRPvQ80WwdMMfm9jjETwfEsMscxagC1fnZ1dPFpb+yT/sWyWXRDDdvwRYAB4+UxUy0hc0wAAAABJRU5ErkJggg=='
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              22,
                              'web',
                              NULL,
                              '.html',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAmBJREFUeNqMU01rU0EUPZm8NIR8aFIbbfGjrS0tiSAY0S66imsR1K0rXXTlP7CF4EJcuFDBIm4shG78A1oQaoOgIAasGGyLFqoxpn1Jm7wmTV5mvHdsmocW8cJ9M2/uPWfOvTPjujo5CTaXy3WRhl78215KKZdlqwWlFHKZDAyesNHYNzM1Nd2gYJNdSrQo1o5ns1nMzM1N8F7kS7w2Oj4OwWy77pIMaja1N+p11CwL1WoVlUpFj89SqWnKu0DY4bYko0XgXXMxtaCvx+3uiLZt2ERsmiYeptNIxmKP7qfTtyhyWxPIDoFgsNA0+IskmUzqcoLBIJ5ns6U9BbZTgYNgPxJWoqdUbqcECvxZwudSC08X61gpUxNpbTAEXB5246hf7wLC7EugS1ha38G9hSLODocx1C3g8QgYboEnbwq4kfBjNKAJxB7IZmm/XTDt4xc5nO4PUdMs9IS8WF3dQHfYj8RQGLOvvuqyOLeNM2xnCaTgw8cVfMMh5ItFZJZMBH0+vJ19j5H4CD7lvsAjEgx0lEBn3lbDq7Jew7olYDYENjYbUD+3caJ/FAuvF3GAYm7uQbMpOqfg6AEriJ/swzvzO9xdQXi6uqBEE9ZWCX4PMDLQq6+h7ezBZj7f7oE+hZtXziOkttHj9WIgEsFgNApj20IAFiYuJfQpcS5jGCuW5+dhrq3xtTWY8dTxMB5cP4dYpA4zvwzzxwpiRxTuXjuD+LGDWgHnMoaxbD7y6OGxsZRymCRvSano8ih6XIoemarbttqhf85lDGONNsFWoVAOxON38B8ma7XyLoH9S4ABADQ1VpwuiBRTAAAAAElFTkSuQmCC'
                          );

INSERT INTO document_type (
                              type_id,
                              type,
                              color,
                              extension,
                              icon
                          )
                          VALUES (
                              23,
                              'web',
                              NULL,
                              '.htm',
                              'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAmBJREFUeNqMU01rU0EUPZm8NIR8aFIbbfGjrS0tiSAY0S66imsR1K0rXXTlP7CF4EJcuFDBIm4shG78A1oQaoOgIAasGGyLFqoxpn1Jm7wmTV5mvHdsmocW8cJ9M2/uPWfOvTPjujo5CTaXy3WRhl78215KKZdlqwWlFHKZDAyesNHYNzM1Nd2gYJNdSrQo1o5ns1nMzM1N8F7kS7w2Oj4OwWy77pIMaja1N+p11CwL1WoVlUpFj89SqWnKu0DY4bYko0XgXXMxtaCvx+3uiLZt2ERsmiYeptNIxmKP7qfTtyhyWxPIDoFgsNA0+IskmUzqcoLBIJ5ns6U9BbZTgYNgPxJWoqdUbqcECvxZwudSC08X61gpUxNpbTAEXB5246hf7wLC7EugS1ha38G9hSLODocx1C3g8QgYboEnbwq4kfBjNKAJxB7IZmm/XTDt4xc5nO4PUdMs9IS8WF3dQHfYj8RQGLOvvuqyOLeNM2xnCaTgw8cVfMMh5ItFZJZMBH0+vJ19j5H4CD7lvsAjEgx0lEBn3lbDq7Jew7olYDYENjYbUD+3caJ/FAuvF3GAYm7uQbMpOqfg6AEriJ/swzvzO9xdQXi6uqBEE9ZWCX4PMDLQq6+h7ezBZj7f7oE+hZtXziOkttHj9WIgEsFgNApj20IAFiYuJfQpcS5jGCuW5+dhrq3xtTWY8dTxMB5cP4dYpA4zvwzzxwpiRxTuXjuD+LGDWgHnMoaxbD7y6OGxsZRymCRvSano8ih6XIoemarbttqhf85lDGONNsFWoVAOxON38B8ma7XyLoH9S4ABADQ1VpwuiBRTAAAAAElFTkSuQmCC'
                          );

INSERT INTO document_type (
                            type_id,
                            type,
                            color,
                            extension,
                            icon
                          )
                          VALUES (
                                24,
                                'tabular',
                                NULL,
                                '.xlsb',
                                'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkJJREFUeNqMU11LVGEQfs7HVksttUSGYZBEGLvdFmGCtdKFRTddRS6RRFA/QJE2FSqobopCsLtgaTO66UYEkb7ACyGEsyC0YETQTYuwa8Z61PPVPK/nnBDaaGB2Zp9553ln5p2j3X99HfMLrdA07QKAVvxb3vm+/8X3PARBgMrsLEyiHe01VL6mDxRHR59tSNCh+j48OcSDFMuyUJyZuSGuJrpI7GhXFzSp4IP43c2u3Lv7EDqPXUW5XMbl3l5cLBRuCvxWiBWJ6XhO9/Cl501rvvuqn+2hVqthrFRCLpMZf1oqDUvoniJYc9ekVA8jpbxK6O+5hfcLb/Ct+hl3+l6AcVPXkcvlVDupVArTllWPLlAEbuCqg9fO3sb49IgKtO/PxPg2U0blunBlLhTX87SIQLcdWx3MnxnE2FRB7ACIncqcVzj9HYmEImElbMdzXU2UFvqquyoTdzA5XwT9J1NDuNIzpCxxYgnDiEmMTQI9IjCjCtr2HVFKeTw5sFlqWIEuSSShGGJdIdgyA83QcO5EXzz5yCfOOAkoJDGkDSGIZ8Bn/Jh/1Nl0D7Jtx2MCVQFbcJw/FciunV7/tRMrix2DnyYmHsqqgrvnh1tI64fTR7iGW1r4YekINg4TVvfwNiYpy//qreQ3JCEetdBYWoJpvazg4Mk9SKbT6rvgM+lhBX8jYabdaJh2vY7vc3MqlhSn5We9vj0ukySSQAIOjWrKAE0+o1ieZQ5zeWtStGWlWl3elc0+wH+Ib9vLzGHfvwUYAKq6LE11+rJNAAAAAElFTkSuQmCC'
);

-- Table: metadata
CREATE TABLE IF NOT EXISTS metadata (
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT INTO metadata (
                         key,
                         value
                     )
                     VALUES (
                         'version',
                         '1.0.0'
                     );


-- Table: signage
CREATE TABLE IF NOT EXISTS signage (
    refkey                TEXT,
    title                 TEXT,
    owner                 TEXT,
    type                  INTEGER NOT NULL
                                  REFERENCES signage_type (uid) ON DELETE SET NULL
                                                                ON UPDATE CASCADE
                                  DEFAULT (0),
    status                INTEGER REFERENCES signage_status (uid) ON DELETE SET NULL
                                                                  ON UPDATE CASCADE
                                  DEFAULT (0),
    source                TEXT,
    note                  TEXT,
    public_note           TEXT,
    evidence              INTEGER DEFAULT (0) 
                                  NOT NULL,
    evidence_eol          INTEGER DEFAULT (0) 
                                  NOT NULL,
    creation_datetime     TEXT,
    modification_datetime TEXT,
    signage_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    parentID              INTEGER REFERENCES signage (signage_id) ON DELETE CASCADE,
    workspace_id          INTEGER REFERENCES workspace (workspace_id) ON DELETE CASCADE
                                  NOT NULL
);


-- Table: signage_has_tag
CREATE TABLE IF NOT EXISTS signage_has_tag (
    tag_id     INTEGER NOT NULL
                       REFERENCES tags (tag_id) ON DELETE NO ACTION,
    signage_id INTEGER NOT NULL,
    PRIMARY KEY (
        tag_id,
        signage_id
    ),
    FOREIGN KEY (
        tag_id
    )
    REFERENCES tags (tag_id) ON DELETE CASCADE
);


-- Table: signage_status
CREATE TABLE IF NOT EXISTS signage_status (
    uid   INTEGER PRIMARY KEY
                  NOT NULL,
    name  TEXT    NOT NULL UNIQUE,
    color TEXT,
    icon  BLOB
);

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           VALUES (
                               0,
                               'Open',
                               '#000000',
                               NULL
                           );

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           VALUES (
                               1,
                               'Planned',
                               '#0000FF',
                               NULL
                           );

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           VALUES (
                               2,
                               'On Hold',
                               '#e28743',
                               NULL
                           );

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           VALUES (
                               3,
                               'Closed',
                               '#76b5c5',
                               NULL
                           );

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           VALUES (
                               4,
                               'Rejected',
                               '#FF0000',
                               NULL
                           );

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           VALUES (
                               5,
                               'Canceled',
                               '#eeeee4',
                               NULL
                           );

INSERT INTO signage_status (
                               uid,
                               name,
                               color,
                               icon
                           )
                           VALUES (
                               6,
                               'Clarification needed',
                               '#42c5f5',
                               NULL
                           );


-- Table: signage_type
CREATE TABLE IF NOT EXISTS signage_type (
    uid   INTEGER PRIMARY KEY
                  NOT NULL,
    name  TEXT    NOT NULL
                  UNIQUE,
    color TEXT,
    icon  BLOB
);

INSERT INTO signage_type (
                             uid,
                             name,
                             color,
                             icon
                         )
                         VALUES (
                             0,
                             'Request',
                             NULL,
                             'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgdmlld0JveD0iMCAwIDI0IDI0IgogICBmaWxsPSJjdXJyZW50Q29sb3IiCiAgIHZlcnNpb249IjEuMSIKICAgaWQ9InN2ZzEiCiAgIHNvZGlwb2RpOmRvY25hbWU9ImhhbmQtZG9jLWZpbGwtZ3JleS5zdmciCiAgIHhtbDpzcGFjZT0icHJlc2VydmUiCiAgIGlua3NjYXBlOnZlcnNpb249IjEuMyAoMGUxNTBlZDZjNCwgMjAyMy0wNy0yMSkiCiAgIHhtbG5zOmlua3NjYXBlPSJodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIgogICB4bWxuczpzb2RpcG9kaT0iaHR0cDovL3NvZGlwb2RpLnNvdXJjZWZvcmdlLm5ldC9EVEQvc29kaXBvZGktMC5kdGQiCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnMKICAgICBpZD0iZGVmczEiIC8+PHNvZGlwb2RpOm5hbWVkdmlldwogICAgIGlkPSJuYW1lZHZpZXcxIgogICAgIHBhZ2Vjb2xvcj0iI2ZmZmZmZiIKICAgICBib3JkZXJjb2xvcj0iIzAwMDAwMCIKICAgICBib3JkZXJvcGFjaXR5PSIwLjI1IgogICAgIGlua3NjYXBlOnNob3dwYWdlc2hhZG93PSIyIgogICAgIGlua3NjYXBlOnBhZ2VvcGFjaXR5PSIwLjAiCiAgICAgaW5rc2NhcGU6cGFnZWNoZWNrZXJib2FyZD0iMCIKICAgICBpbmtzY2FwZTpkZXNrY29sb3I9IiNkMWQxZDEiCiAgICAgc2hvd2d1aWRlcz0idHJ1ZSIKICAgICBpbmtzY2FwZTp6b29tPSI4LjM5NTgzMzMiCiAgICAgaW5rc2NhcGU6Y3g9IjEwLjEyNDA2OSIKICAgICBpbmtzY2FwZTpjeT0iMzEuNjIyODI5IgogICAgIGlua3NjYXBlOndpbmRvdy13aWR0aD0iMTkyMCIKICAgICBpbmtzY2FwZTp3aW5kb3ctaGVpZ2h0PSIxMDE3IgogICAgIGlua3NjYXBlOndpbmRvdy14PSItOCIKICAgICBpbmtzY2FwZTp3aW5kb3cteT0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LW1heGltaXplZD0iMSIKICAgICBpbmtzY2FwZTpjdXJyZW50LWxheWVyPSJzdmcxIiAvPjxwYXRoCiAgICAgZD0ibSA5LjMxNzYxMzEsMTEuNDUyMzQ0IDIuMTY5OTk5OSw1ZS00IGMgMS4zMzIwNTcsMCAyLjUyODkyNSwwLjU3ODc2IDMuMzUyODYyLDEuNDk4NTM2IDAuNzEzMzMzLDAuNzk2MzA3IDEuMTQ3MTM4LDEuODQ4MjIxIDEuMTQ3MTM4LDMuMDAxNDY0IEggOC45ODY1OTMxIGwgMTBlLTQsMSA4LjAwMDAxOTksLThlLTQgdiAtMC45OTkyIGMgMCwtMS4wODI0IC0wLjMxODIsLTIuMTAzMSAtMC44ODYxLC0zLjAwMDggbCAyLjg4NjEsOGUtNCBjIDEuOTkyMywwIDMuNzEyNCwxLjE2NTMgNC41MTYxLDIuODUxNCAtMi4zNjQ4LDMuMTIwNiAtNi4xOTQyLDUuMTQ4NiAtMTAuNTE2MSw1LjE0ODYgLTIuNzYxMywwIC01LjEwMDQ0OTksLTAuNTkwNiAtNy4wMDAzMzk5LC0xLjYyNDggbCAwLjAwMTM2LC05LjMwNDIgYyAxLjI0NTU1LDAuMTc4NCAyLjM4NTMsMC42ODQ3IDMuMzI4OTgsMS40Mjg1IHogbSAtNC4zMzAwMiw3LjUwMDUgYyAwLDAuNTUyMyAtMC40NDc3MSwxIC0xLDEgaCAtMiBjIC0wLjU1MjI4LDAgLTEuMDAwMDAwMDUsLTAuNDQ3NyAtMS4wMDAwMDAwNSwtMSBWIDkuOTUyODQzNiBjIDAsLTAuNTUyMjggMC40NDc3MjAwNSwtMC45OTk5OSAxLjAwMDAwMDA1LC0wLjk5OTk5IGggMiBjIDAuNTUyMjksMCAxLDAuNDQ3NzEgMSwwLjk5OTk5IHoiCiAgICAgaWQ9InBhdGgxIgogICAgIHNvZGlwb2RpOm5vZGV0eXBlcz0iY2NzY2NjY3NjY2NzY2Njc3Nzc3Nzc3NzIgogICAgIHN0eWxlPSJmaWxsOiM5OTk5OTk7ZmlsbC1vcGFjaXR5OjEiIC8+PHBhdGgKICAgICBkPSJtIDkuMjE5NzA5NiwxLjA3NDQ5MDIgYyAtMC4wNDc3MTYsMCAtMC4wOTM2NzcsMC4wMDYwOSAtMC4xMzg2NzE5LDAuMDE0ODE0IC0wLjA0NDk5NCwwLjAwODczIC0wLjA4OTUxMywwLjAyMDQ1NCAtMC4xMzA4NTk0LDAuMDM3MDM1IC0wLjA0MTM0NiwwLjAxNjU4IC0wLjA4MDQxNiwwLjAzNzU1NSAtMC4xMTcxODc1LDAuMDYxMTA3IC0wLjAzNjc3MiwwLjAyMzU1MiAtMC4wNzAyOTIsMC4wNDk5NzcgLTAuMTAxNTYyNSwwLjA3OTYyNCAtMC4wMzEyNywwLjAyOTY0NyAtMC4wNjEwOTUsMC4wNjE0MjcgLTAuMDg1OTM3LDAuMDk2MjkgLTAuMDI0ODQyLDAuMDM0ODYyIC0wLjA0NTAxMiwwLjA3Mzc1NSAtMC4wNjI1LDAuMTEyOTU1MSAtMC4wMTc0ODgsMC4wMzkxOTkgLTAuMDMxODA4LDAuMDc5NTU1IC0wLjA0MTAxNiwwLjEyMjIxMzcgLTAuMDA5MjEsMC4wNDI2NTggLTAuMDEzNjcyLDAuMDg2MjM0IC0wLjAxMzY3MiwwLjEzMTQ3MjQgViA5LjUwNzI0IGMgMC4wNDA2OSwwLjAyMjAyNCAwLjA4Mjg3MywwLjA0MjAzOCAwLjEyMzA0NjksMC4wNjQ4MTEgMC4xMjk1MDksMC4wNzM0MSAwLjI1Njk0ODYsMC4xNTA1MjIzIDAuMzgwODU5NCwwLjIzMTQ2NTggMC4xMjM5MTA3LDAuMDgwOTQ3IDAuMjQzMzY4MiwwLjE2NTUzOCAwLjM2MTMyODEsMC4yNTM2ODYyIGggMi4xNzE4NzQzIGMgMC4xNjY1MDcsMCAwLjMzMDM3LDAuMDA5MiAwLjQ5MjE4OCwwLjAyNTkyIDAuMTYxODE4LDAuMDE2NyAwLjMyMDM2MiwwLjA0MTU0IDAuNDc2NTYyLDAuMDc0MDcgMC4xNTYyMDEsMC4wMzI1MyAwLjMwOTMzMSwwLjA3Mjg4IDAuNDU4OTg1LDAuMTIwMzYyIDAuMTQ5NjU0LDAuMDQ3NDggMC4yOTUzMjEsMC4xMDE0MDcgMC40Mzc1LDAuMTYyOTUxIDAuMTQyMTc5LDAuMDYxNTQgMC4yODAyODcsMC4xMzA4MTEgMC40MTQwNjIsMC4yMDU1NDIgMC4xMzM3NzUsMC4wNzQ3MyAwLjI2NDIyOSwwLjE1NTU0IDAuMzg4NjcyLDAuMjQyNTc1IDAuMTI0NDQzLDAuMDg3MDMgMC4yNDMyNCwwLjE4MTE1MSAwLjM1NzQyMiwwLjI3OTYxMSAwLjExNDE4MiwwLjA5ODQ2IDAuMjIzMTgsMC4yMDIwODYgMC4zMjYxNzIsMC4zMTEwODkgaCAxLjI2MTcxOSAyLjg4NjcxOCBjIDAuMTI0NTE5LDAgMC4yNDY5MDYsMC4wMDQ1IDAuMzY5MTQxLDAuMDEyOTYgMC4xMjIyMzUsMC4wMDg0IDAuMjQzNjQ1LDAuMDIyMjIgMC4zNjMyODEsMC4wMzg4OSAwLjExOTYzNywwLjAxNjY3IDAuMjM2NzkyLDAuMDM2NTYgMC4zNTM1MTYsMC4wNjExIDAuMTE2NzIzLDAuMDI0NTUgMC4yMzIyMDcsMC4wNTMwNSAwLjM0NTcwMywwLjA4NTE3IDAuMTEzNDk2LDAuMDMyMTQgMC4yMjU5ODQsMC4wNjc5OCAwLjMzNTkzNywwLjEwNzQgMC4wNDY0OCwwLjAxNjY3IDAuMDkwOTEsMC4wMzc2MiAwLjEzNjcxOSwwLjA1NTU1IFYgMS43MzAwMDAzIGMgMCwtMC4wNDUyMzkgLTAuMDA0NSwtMC4wODg4MTQgLTAuMDEzNjcsLTAuMTMxNDcyNCAtMC4wMDkyLC0wLjA0MjY1OSAtMC4wMjM1MywtMC4wODMwMTQgLTAuMDQxMDIsLTAuMTIyMjEzNyAtMC4wMTc0OSwtMC4wMzkxOTkgLTAuMDM3NjYsLTAuMDc4MDkzIC0wLjA2MjUsLTAuMTEyOTU1MSAtMC4wMjQ4NCwtMC4wMzQ4NjIgLTAuMDU0NjcsLTAuMDY2NjQzIC0wLjA4NTk0LC0wLjA5NjI5IC0wLjAzMTI3LC0wLjAyOTY0NiAtMC4wNjQ3OSwtMC4wNTYwNzEgLTAuMTAxNTYyLC0wLjA3OTYyNCAtMC4wMzY3NywtMC4wMjM1NTIgLTAuMDc1ODQsLTAuMDQ0NTI3IC0wLjExNzE4OCwtMC4wNjExMDcgLTAuMDQxMzUsLTAuMDE2NTggLTAuMDg1ODYsLTAuMDI4MzA1IC0wLjEzMDg1OSwtMC4wMzcwMzUgLTAuMDQ1LC0wLjAwODczIC0wLjA5MDk1LC0wLjAxNDgxNCAtMC4xMzg2NzIsLTAuMDE0ODE0IHogTSAxMS4yOTI1MiwyLjYxNTMzMzggaCA0LjIzNzU0MiBWIDMuOTI2MzU0IEggMTEuMjkyNTIgWiBtIDAuMDAxNCwzLjI3NTY5ODggaCA2LjkxMDE1NiBWIDcuMjAyMDUzMiBIIDExLjI5MzkyIFoiCiAgICAgc3R5bGU9ImZpbGw6Izk5OTk5OTtzdHJva2Utd2lkdGg6MS40OTc0NztmaWxsLW9wYWNpdHk6MSIKICAgICBpZD0icGF0aDE0IgogICAgIHNvZGlwb2RpOm5vZGV0eXBlcz0ic2Nzc3Nzc2NzY2NjY3NjY3Njc3NzY2NzY3NjY3Njc2Nzc3Nzc3Nzc2NjY2NjY2NjY2MiIC8+PC9zdmc+Cg=='
                         );

INSERT INTO signage_type (
                             uid,
                             name,
                             color,
                             icon
                         )
                         VALUES (
                             1,
                             'Question',
                             NULL,
                             'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgdmlld0JveD0iMCAwIDI0IDI0IgogICBmaWxsPSJjdXJyZW50Q29sb3IiCiAgIHZlcnNpb249IjEuMSIKICAgaWQ9InN2ZzEiCiAgIHNvZGlwb2RpOmRvY25hbWU9InF1ZXN0aW9ubmFpcmUtZmlsbCgxKS5zdmciCiAgIGlua3NjYXBlOnZlcnNpb249IjEuMyAoMGUxNTBlZDZjNCwgMjAyMy0wNy0yMSkiCiAgIHhtbG5zOmlua3NjYXBlPSJodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIgogICB4bWxuczpzb2RpcG9kaT0iaHR0cDovL3NvZGlwb2RpLnNvdXJjZWZvcmdlLm5ldC9EVEQvc29kaXBvZGktMC5kdGQiCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPGRlZnMKICAgICBpZD0iZGVmczEiIC8+CiAgPHNvZGlwb2RpOm5hbWVkdmlldwogICAgIGlkPSJuYW1lZHZpZXcxIgogICAgIHBhZ2Vjb2xvcj0iI2ZmZmZmZiIKICAgICBib3JkZXJjb2xvcj0iIzAwMDAwMCIKICAgICBib3JkZXJvcGFjaXR5PSIwLjI1IgogICAgIGlua3NjYXBlOnNob3dwYWdlc2hhZG93PSIyIgogICAgIGlua3NjYXBlOnBhZ2VvcGFjaXR5PSIwLjAiCiAgICAgaW5rc2NhcGU6cGFnZWNoZWNrZXJib2FyZD0iMCIKICAgICBpbmtzY2FwZTpkZXNrY29sb3I9IiNkMWQxZDEiCiAgICAgaW5rc2NhcGU6em9vbT0iMzQuOTU4MzMzIgogICAgIGlua3NjYXBlOmN4PSIxMiIKICAgICBpbmtzY2FwZTpjeT0iMTEuOTcxMzk1IgogICAgIGlua3NjYXBlOndpbmRvdy13aWR0aD0iMTkyMCIKICAgICBpbmtzY2FwZTp3aW5kb3ctaGVpZ2h0PSIxMDE3IgogICAgIGlua3NjYXBlOndpbmRvdy14PSItOCIKICAgICBpbmtzY2FwZTp3aW5kb3cteT0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LW1heGltaXplZD0iMSIKICAgICBpbmtzY2FwZTpjdXJyZW50LWxheWVyPSJzdmcxIiAvPgogIDxwYXRoCiAgICAgZD0iTTYuNDU0NTUgMTlMMiAyMi41VjRDMiAzLjQ0NzcyIDIuNDQ3NzIgMyAzIDNIMjFDMjEuNTUyMyAzIDIyIDMuNDQ3NzIgMjIgNFYxOEMyMiAxOC41NTIzIDIxLjU1MjMgMTkgMjEgMTlINi40NTQ1NVpNMTEgMTRWMTZIMTNWMTRIMTFaTTguNTY3MzEgOC44MTM0NkwxMC41Mjg4IDkuMjA1NzdDMTAuNjY1NiA4LjUxODIzIDExLjI3MjMgOCAxMiA4QzEyLjgyODQgOCAxMy41IDguNjcxNTcgMTMuNSA5LjVDMTMuNSAxMC4zMjg0IDEyLjgyODQgMTEgMTIgMTFIMTFWMTNIMTJDMTMuOTMzIDEzIDE1LjUgMTEuNDMzIDE1LjUgOS41QzE1LjUgNy41NjcgMTMuOTMzIDYgMTIgNkMxMC4zMDIgNiA4Ljg4NjM3IDcuMjA5MTkgOC41NjczMSA4LjgxMzQ2WiIKICAgICBpZD0icGF0aDEiCiAgICAgc3R5bGU9ImZpbGw6IzQ2OTJkZDtmaWxsLW9wYWNpdHk6MSIgLz4KPC9zdmc+Cg=='
                         );

INSERT INTO signage_type (
                             uid,
                             name,
                             color,
                             icon
                         )
                         VALUES (
                             2,
                             'Todo',
                             NULL,
                             'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmls
        bD0iY3VycmVudENvbG9yIj48cGF0aCBkPSJNMTkgNEg1VjIwSDE5VjRaTTMgMi45OTE4QzMgMi40NDQwNSAzLjQ0NzQ5IDIg
        My45OTg1IDJIMTkuOTk5N0MyMC41NTE5IDIgMjAuOTk5NiAyLjQ0NzcyIDIwLjk5OTcgM0wyMSAyMC45OTI1QzIxIDIxLjU0O
        DkgMjAuNTU1MSAyMiAyMC4wMDY2IDIySDMuOTkzNEMzLjQ0NDc2IDIyIDMgMjEuNTQ0NyAzIDIxLjAwODJWMi45OTE4Wk0xMS
        4yOTI5IDEzLjEyMTNMMTUuNTM1NSA4Ljg3ODY4TDE2Ljk0OTcgMTAuMjkyOUwxMS4yOTI5IDE1Ljk0OTdMNy40MDM4MSAxMi4w
        NjA3TDguODE4MDIgMTAuNjQ2NEwxMS4yOTI5IDEzLjEyMTNaIj48L3BhdGg+PC9zdmc+'
                         );

INSERT INTO signage_type (
                             uid,
                             name,
                             color,
                             icon
                         )
                         VALUES (
                             3,
                             'Finding',
                             NULL,
                             'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgdmlld0JveD0iMCAwIDI0IDI0IgogICBmaWxsPSJjdXJyZW50Q29sb3IiCiAgIHZlcnNpb249IjEuMSIKICAgaWQ9InN2ZzEiCiAgIHNvZGlwb2RpOmRvY25hbWU9ImFsZXJ0LWZpbGwuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIxLjMgKDBlMTUwZWQ2YzQsIDIwMjMtMDctMjEpIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMxIiAvPgogIDxzb2RpcG9kaTpuYW1lZHZpZXcKICAgICBpZD0ibmFtZWR2aWV3MSIKICAgICBwYWdlY29sb3I9IiNmZmZmZmYiCiAgICAgYm9yZGVyY29sb3I9IiMwMDAwMDAiCiAgICAgYm9yZGVyb3BhY2l0eT0iMC4yNSIKICAgICBpbmtzY2FwZTpzaG93cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTpwYWdlb3BhY2l0eT0iMC4wIgogICAgIGlua3NjYXBlOnBhZ2VjaGVja2VyYm9hcmQ9IjAiCiAgICAgaW5rc2NhcGU6ZGVza2NvbG9yPSIjZDFkMWQxIgogICAgIGlua3NjYXBlOnpvb209IjExLjg3MzUwMSIKICAgICBpbmtzY2FwZTpjeD0iMTMuMzkxMTY0IgogICAgIGlua3NjYXBlOmN5PSI4LjYzMjY2ODQiCiAgICAgaW5rc2NhcGU6d2luZG93LXdpZHRoPSIxOTIwIgogICAgIGlua3NjYXBlOndpbmRvdy1oZWlnaHQ9IjEwMTciCiAgICAgaW5rc2NhcGU6d2luZG93LXg9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy15PSItOCIKICAgICBpbmtzY2FwZTp3aW5kb3ctbWF4aW1pemVkPSIxIgogICAgIGlua3NjYXBlOmN1cnJlbnQtbGF5ZXI9InN2ZzEiIC8+CiAgPHBhdGgKICAgICBkPSJNMTIuODY1OSAzLjAwMDE3TDIyLjM5MjIgMTkuNTAwMkMyMi42Njg0IDE5Ljk3ODUgMjIuNTA0NSAyMC41OTAxIDIyLjAyNjIgMjAuODY2MkMyMS44NzQyIDIwLjk1NCAyMS43MDE3IDIxLjAwMDIgMjEuNTI2MiAyMS4wMDAySDIuNDczNjNDMS45MjEzNSAyMS4wMDAyIDEuNDczNjMgMjAuNTUyNSAxLjQ3MzYzIDIwLjAwMDJDMS40NzM2MyAxOS44MjQ2IDEuNTE5ODQgMTkuNjUyMiAxLjYwNzYxIDE5LjUwMDJMMTEuMTMzOSAzLjAwMDE3QzExLjQxIDIuNTIxODcgMTIuMDIxNiAyLjM1OCAxMi40OTk5IDIuNjM0MTRDMTIuNjUxOSAyLjcyMTkxIDEyLjc3ODIgMi44NDgxNSAxMi44NjU5IDMuMDAwMTdaTTEwLjk5OTkgMTYuMDAwMlYxOC4wMDAySDEyLjk5OTlWMTYuMDAwMkgxMC45OTk5Wk0xMC45OTk5IDkuMDAwMTdWMTQuMDAwMkgxMi45OTk5VjkuMDAwMTdIMTAuOTk5OVoiCiAgICAgaWQ9InBhdGgxIgogICAgIHN0eWxlPSJmaWxsOiNmZjAwMDA7ZmlsbC1vcGFjaXR5OjEiIC8+Cjwvc3ZnPgo='
                         );


-- Table: tags
CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT
                   NOT NULL,
    name   TEXT    NOT NULL
                   UNIQUE,
    color  TEXT,
    icon   TEXT
);

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     1,
                     'PSMF',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     3,
                     'Signal',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     4,
                     'Safety variation',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     5,
                     'PASS',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     6,
                     'Audit',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     7,
                     'LCP',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     8,
                     'QPPV',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     9,
                     'Risk minimization',
                     NULL,
                     NULL
                 );

INSERT INTO tags (
                     tag_id,
                     name,
                     color,
                     icon
                 )
                 VALUES (
                     10,
                     'QMS',
                     NULL,
                     NULL
                 );


-- Table: version
CREATE TABLE IF NOT EXISTS version (
    name TEXT    NOT NULL,
    note TEXT,
    id   INTEGER PRIMARY KEY AUTOINCREMENT
                 NOT NULL
);

INSERT INTO version (
                        name,
                        note,
                        id
                    )
                    VALUES (
                        '0.0.1-alpha',
                        NULL,
                        1
                    );


-- Table: workspace
CREATE TABLE IF NOT EXISTS workspace (
    workspace_id      INTEGER PRIMARY KEY AUTOINCREMENT
                              NOT NULL,
    state             INTEGER NOT NULL
                              DEFAULT (1),
    name              TEXT    NOT NULL
                              UNIQUE,
    reference         TEXT,
    root              TEXT    NOT NULL,
    attachments_path  TEXT,
    notebook_path     TEXT,
    onenote_section   TEXT,
    creation_date     TEXT,
    modification_date TEXT
);


-- Index: idx_document_type
CREATE INDEX IF NOT EXISTS idx_document_type ON document_type (
    type,
    extension
);


-- Trigger: afterEvidenceDelete
CREATE TRIGGER IF NOT EXISTS afterEvidenceDelete
                       AFTER DELETE
                          ON document
BEGIN
    UPDATE signage
       SET evidence = (
               SELECT Count(1) 
                 FROM document
                WHERE refkey = old.refkey AND 
                      refkey IS NOT "" AND 
                      workspace_id = old.workspace_id
           ),
           evidence_eol = (
               SELECT count(1) 
                 FROM document
                WHERE refkey = old.refkey AND 
                      refkey IS NOT "" AND 
                      status IN (
                          SELECT uid
                            FROM document_status
                           WHERE eol = 1
                      )
AND 
                      workspace_id = old.workspace_id
           )
     WHERE signage.refkey = old.refkey AND 
           signage.type = 0 AND 
           signage.workspace_id = old.workspace_id;
END;


-- Trigger: afterEvidenceInsert
CREATE TRIGGER IF NOT EXISTS afterEvidenceInsert
                       AFTER INSERT
                          ON document
BEGIN
    UPDATE signage
       SET evidence = (
               SELECT Count(1) 
                 FROM document
                WHERE refkey = new.refkey AND 
                      refkey IS NOT "" AND 
                      workspace_id = new.workspace_id
           ),
           evidence_eol = (
               SELECT count(1) 
                 FROM document
                WHERE refkey = new.refkey AND 
                      refkey IS NOT "" AND 
                      status IN (
                          SELECT uid
                            FROM document_status
                           WHERE eol = 1
                      )
AND 
                      workspace_id = new.workspace_id
           )
     WHERE signage.refkey = new.refkey AND 
           signage.type = 0 AND 
           signage.workspace_id = new.workspace_id;
END;


-- Trigger: afterEvidenceUpdate
CREATE TRIGGER IF NOT EXISTS afterEvidenceUpdate
                       AFTER UPDATE OF refkey,
                                       status,
                                       signage_id
                          ON document
BEGIN
    UPDATE signage
       SET evidence = (
               SELECT Count(1) 
                 FROM document
                WHERE refkey = new.refkey AND 
                      refkey IS NOT "" AND 
                      workspace_id = new.workspace_id
           ),
           evidence_eol = (
               SELECT count(1) 
                 FROM document
                WHERE refkey = new.refkey AND 
                      refkey IS NOT "" AND 
                      status IN (
                          SELECT uid
                            FROM document_status
                           WHERE eol = 1
                      )
AND 
                      workspace_id = new.workspace_id
           )
     WHERE signage.refkey = new.refkey AND 
           signage.type = 0 AND 
           signage.workspace_id = new.workspace_id;
END;


-- Trigger: afterRefkeyUpdate
CREATE TRIGGER IF NOT EXISTS afterRefkeyUpdate
                       AFTER UPDATE OF refkey
                          ON document
BEGIN
    UPDATE document
       SET signage_id = (
               SELECT signage.signage_id
                 FROM signage
                WHERE signage.refkey = new.refkey AND 
                      signage.workspace_id = new.workspace_id AND 
                      signage.type = 0
                LIMIT 1
           )
     WHERE id = new.id;
END;


-- Trigger: updateEvidenceAfterInsert
CREATE TRIGGER IF NOT EXISTS updateEvidenceAfterInsert
                       AFTER INSERT
                          ON signage
                    FOR EACH ROW
                        WHEN new.type = 0
BEGIN
    UPDATE document
       SET signage_id = NEW.signage_id
     WHERE document.refkey = NEW.refkey AND 
           document.workspace_id = NEW.workspace_id;
END;


-- Trigger: updateEvidenceAfterUpdate
CREATE TRIGGER IF NOT EXISTS updateEvidenceAfterUpdate
                       AFTER UPDATE OF refkey
                          ON signage
                        WHEN new.type = 0
BEGIN
    UPDATE document
       SET signage_id = new.signage_id
     WHERE document.refkey = new.refkey AND 
           document.workspace_id = new.workspace_id;
END;


-- Trigger: updateSignageIdAfterInsert
CREATE TRIGGER IF NOT EXISTS updateSignageIdAfterInsert
                       AFTER INSERT
                          ON document
BEGIN
    UPDATE document
       SET signage_id = (
               SELECT signage.signage_id
                 FROM signage
                WHERE signage.refkey = new.refkey AND 
                      signage.workspace_id = new.workspace_id AND 
                      signage.type = 0
                LIMIT 1
           )
     WHERE id = new.id;
END;


-- Trigger: UpdateStateBeforeInsert
CREATE TRIGGER IF NOT EXISTS UpdateStateBeforeInsert
                      BEFORE INSERT
                          ON workspace
                    FOR EACH ROW
                        WHEN NEW.state = 1
BEGIN
    UPDATE workspace
       SET state = 0
     WHERE state = 1;
END;


-- Trigger: UpdateWorkspaceState
CREATE TRIGGER IF NOT EXISTS UpdateWorkspaceState
                       AFTER UPDATE OF state
                          ON workspace
                        WHEN NEW.state = 1
BEGIN
    UPDATE workspace
       SET state = 0
     WHERE state = 1 AND 
           workspace_id <> OLD.workspace_id;
END;


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
