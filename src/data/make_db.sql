--
-- File generated with SQLiteStudio v3.4.4 on Thu Jun 20 22:51:24 2024
--
-- Text encoding used: Shift_JIS
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: annotation
DROP TABLE IF EXISTS annotation;

CREATE TABLE IF NOT EXISTS annotation (
    annotation_id INTEGER PRIMARY KEY AUTOINCREMENT
                          NOT NULL
                          UNIQUE,
    document_id   INTEGER REFERENCES document (doc_id) 
                          NOT NULL,
    text          TEXT,
    comment       TEXT,
    color         TEXT,
    position      TEXT,
    page_label    TEXT,
    type          INTEGER NOT NULL
                          DEFAULT (1) 
                          REFERENCES annotation_type (type_id) 
);


-- Table: annotation_type
DROP TABLE IF EXISTS annotation_type;

CREATE TABLE IF NOT EXISTS annotation_type (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT
                    NOT NULL,
    type    TEXT
);

INSERT INTO annotation_type (type_id, type) VALUES (1, 'area');
INSERT INTO annotation_type (type_id, type) VALUES (2, 'highlighted text');
INSERT INTO annotation_type (type_id, type) VALUES (3, 'sticky note');

-- Table: document
DROP TABLE IF EXISTS document;

CREATE TABLE IF NOT EXISTS document (
    exist             INTEGER NOT NULL
                              DEFAULT (1),
    status_id         INTEGER REFERENCES document_status (status_id) 
                              DEFAULT (1),
    refKey            TEXT,
    title             TEXT    DEFAULT untitled
                              NOT NULL,
    subtitle          TEXT,
    reference         TEXT,
    type_id           INTEGER REFERENCES document_type (type_ID) 
                              DEFAULT (1),
    doc_id            INTEGER PRIMARY KEY AUTOINCREMENT
                              NOT NULL
                              UNIQUE,
    filename          TEXT    NOT NULL,
    filepath          TEXT    NOT NULL
                              UNIQUE,
    modification_date TEXT    NOT NULL,
    creation_date     TEXT    NOT NULL,
    note              TEXT,
    workspace_id      INTEGER REFERENCES workspace (workspace_id),
    dirpath           TEXT    NOT NULL,
    citation_key      TEXT,
    display           INTEGER DEFAULT (1) 
                              NOT NULL
);


-- Table: document_has_tag
DROP TABLE IF EXISTS document_has_tag;

CREATE TABLE IF NOT EXISTS document_has_tag (
    doc_id INTEGER NOT NULL
                   REFERENCES document (doc_id) ON DELETE CASCADE,
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


-- Table: document_relation
DROP TABLE IF EXISTS document_relation;

CREATE TABLE IF NOT EXISTS document_relation (
    doc_id     INTEGER REFERENCES document (doc_id) ON DELETE CASCADE,
    related_id INTEGER REFERENCES document (doc_id) ON DELETE CASCADE
);


-- Table: document_status
DROP TABLE IF EXISTS document_status;

CREATE TABLE IF NOT EXISTS document_status (
    status_id INTEGER PRIMARY KEY AUTOINCREMENT
                      NOT NULL,
    status    TEXT    NOT NULL
                      UNIQUE,
    color     TEXT,
    icon      TEXT
);

INSERT INTO document_status (status_id, status, color, icon) VALUES (1, 'To review', '#0000FF', NULL);
INSERT INTO document_status (status_id, status, color, icon) VALUES (2, 'In Progress', '#32a852', NULL);
INSERT INTO document_status (status_id, status, color, icon) VALUES (3, 'On Hold', '#e28743', NULL);
INSERT INTO document_status (status_id, status, color, icon) VALUES (4, 'Closed', '#76b5c5', NULL);
INSERT INTO document_status (status_id, status, color, icon) VALUES (5, 'Rejected', '#FF0000', NULL);

-- Table: document_type
DROP TABLE IF EXISTS document_type;

CREATE TABLE IF NOT EXISTS document_type (
    type_id   INTEGER PRIMARY KEY AUTOINCREMENT
                      NOT NULL,
    type      TEXT    NOT NULL,
    color     TEXT,
    extension TEXT,
    icon      BLOB
);

INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (1, 'document', NULL, NULL, 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAV9JREFUeNqMkrFOwzAQhs9OAgzkAWBnad8izKzwCrxFq0qVeAAkOlfqhthRJV6hGdhg654IJRFVYzvcXWMrEDfipPNZ5/Pn+22LpmmA7HY6vcFwAcP2Zoz5NFrDy3zOidCu4MLlcjJZ7HGxJjcGNMLtAWmawnK9vsepQP+w+6QDaC0Mbapr9v1uB99VBWVZQlEUHJ9nswXWXWP5VQ+gEUBoiWMUBHAWRXAShhBKCQJzWZbB42oFyWj09L7Z3Nl9YacDSZslY4AhzpSCJElYThzH8JqmeQ+gqIMOwAdRKNHW9gBaKSeha38hdAjV+gAHCagZ2pN8kOAAkH0JmHQdDEACjOoIgO+A74Hfxw8JMK+8EuradWDs+3ogLAFr/RKoA3yqIYhoa/0SbAcDEMp7JeC35bm9g2MQ0an9BfjK81PXZvuh6OeJNjKUvjV6t9YBqrLcno/HD/APQ8jWzn8EGACxU8j1qPzZewAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (2, 'text', NULL, '.txt', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAfJJREFUeNqMUj1rG0EQnbtboYhESFfYJp8ESYFgo8qNazltuvyI/InYYFKkDoG4NqjLHwiGgCGFK3N9jCVIYYyRzrY+zljSKu+NtdIanJCFudnd2ffmzcwF77a2hCsIgrdwj+Xf64e19thOJjKdTvXCuA38k73t7d0bBEc0a2WCmIsnSSJ7+/vvmQv2yzGGZJtZYAkajdRurq8lGwyk3+9Lr9dT/21nZxfvNoF75QjMBODZCkgd4puLooXo8VjGIO52u/Kl2ZTG6urXz83mB0Q+KoFdEIQE/zw6UtnlclmGw6G8rtWUpNFo6H2xWJTvSZLOFYx9BSCoAcBS+DiOY3mQy91RoluUuygBAb+EVqul2TudjpKczBpZKpUkyzKp1+sCzL0EWkK1Wp1nd0qc8RzhDTDhogSPgLTtdnsOdEroeWZPnq6soJr7CbQHToHfB3+fC0MSeCVg5r4C1wOOjUA/ez6fl5dQAMxfSoCCSqWiB2Yj8BmaRyJLVbBAB+KVcHl6Kg+Xlu5Mwcll1hdQgPaKzEbIRrsSBufnYo4PDuT5xoYU4tjw8s36+m0P2Hmc6cPbGSkJkfjFTZam8vvwUGMFbJYv0zTvdRPvQ80WwdMMfm9jjETwfEsMscxagC1fnZ1dPFpb+yT/sWyWXRDDdvwRYAB4+UxUy0hc0wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (3, 'tabular', NULL, '.xls', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkJJREFUeNqMU11LVGEQfs7HVksttUSGYZBEGLvdFmGCtdKFRTddRS6RRFA/QJE2FSqobopCsLtgaTO66UYEkb7ACyGEsyC0YETQTYuwa8Z61PPVPK/nnBDaaGB2Zp9553ln5p2j3X99HfMLrdA07QKAVvxb3vm+/8X3PARBgMrsLEyiHe01VL6mDxRHR59tSNCh+j48OcSDFMuyUJyZuSGuJrpI7GhXFzSp4IP43c2u3Lv7EDqPXUW5XMbl3l5cLBRuCvxWiBWJ6XhO9/Cl501rvvuqn+2hVqthrFRCLpMZf1oqDUvoniJYc9ekVA8jpbxK6O+5hfcLb/Ct+hl3+l6AcVPXkcvlVDupVArTllWPLlAEbuCqg9fO3sb49IgKtO/PxPg2U0blunBlLhTX87SIQLcdWx3MnxnE2FRB7ACIncqcVzj9HYmEImElbMdzXU2UFvqquyoTdzA5XwT9J1NDuNIzpCxxYgnDiEmMTQI9IjCjCtr2HVFKeTw5sFlqWIEuSSShGGJdIdgyA83QcO5EXzz5yCfOOAkoJDGkDSGIZ8Bn/Jh/1Nl0D7Jtx2MCVQFbcJw/FciunV7/tRMrix2DnyYmHsqqgrvnh1tI64fTR7iGW1r4YekINg4TVvfwNiYpy//qreQ3JCEetdBYWoJpvazg4Mk9SKbT6rvgM+lhBX8jYabdaJh2vY7vc3MqlhSn5We9vj0ukySSQAIOjWrKAE0+o1ieZQ5zeWtStGWlWl3elc0+wH+Ib9vLzGHfvwUYAKq6LE11+rJNAAAAAElFTkSuQmCC');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (4, 'image', NULL, '.jpg', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (5, 'presentation', NULL, '.ppt', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAlZJREFUeNqMU01oE0EU/mZ3YrPFCK3aqK2I6KHQ2oKIPxC15CAU9CKo4ElExIJH7aUtxR/8Qb148lyJ9eRZqQaFQAP1kPRk0eChvbTRbltMN5ud3fW9abIqGHHg5c1+b75v3nvzIpbvH8RV5zSEEGcA7MS/VzYIgi+B7yMMQ3zK5SAZvRHP45FzZNfE+PizGgU9tiCAT4f4IK9CoYCJqalrtBVknxnrTqUgKIP3tD/Z7Ep3xwF8P3UPxWIRFwcHcXZkZIjgdySsRUT5dl+4bazYNOdvd/qxdOU1stlshD3NZMbI3eW9VFUPYeBDLS9g7dUoRCwGmeyGdfgCZHsXOC4NA+l0WpeTSCTwplCwG2KGqtZIQMF+OQxnbhrxY5cQP34ZP3LPNc7xTVJqEWq0JinfF2TsIT3HRagU1ktFhK4Lo6sf1dIMnK+z2EI4xy3KaoOptIivlGhkINV6FYHvwWjfC7f0EfPX9+tAy75DGud4zDSj+s0NASMqwXOoBF8hcf4WzM4+ejqpPX8zznGDSCwSp0zYKxIgY89NrME0BFqTe9B688UfL8A4x4167Uw2qRfq9xJ8T32YPZdsOgdW74lIICrB86ISJL3NwJy5HY8TA8Mzk5MPaVTBsxfUp5A9Y40ldC9/9UBmVrfibWeKUX0P38Yk7flbd4p+6yKMN0qolMuQT6aXsPvoAqy2Nv2/4Gcy6hn8TYSZTqUiHdvGfD6vYxZtOlZtuyVKk0WIwALcNDZJDZQ0UCZ5Pssc5vKtFlnH2uLiyuaengf4jxU4zgpzuB0/BRgAO1gmOtGmT+8AAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (6, 'tabular', NULL, '.xlsx', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkJJREFUeNqMU11LVGEQfs7HVksttUSGYZBEGLvdFmGCtdKFRTddRS6RRFA/QJE2FSqobopCsLtgaTO66UYEkb7ACyGEsyC0YETQTYuwa8Z61PPVPK/nnBDaaGB2Zp9553ln5p2j3X99HfMLrdA07QKAVvxb3vm+/8X3PARBgMrsLEyiHe01VL6mDxRHR59tSNCh+j48OcSDFMuyUJyZuSGuJrpI7GhXFzSp4IP43c2u3Lv7EDqPXUW5XMbl3l5cLBRuCvxWiBWJ6XhO9/Cl501rvvuqn+2hVqthrFRCLpMZf1oqDUvoniJYc9ekVA8jpbxK6O+5hfcLb/Ct+hl3+l6AcVPXkcvlVDupVArTllWPLlAEbuCqg9fO3sb49IgKtO/PxPg2U0blunBlLhTX87SIQLcdWx3MnxnE2FRB7ACIncqcVzj9HYmEImElbMdzXU2UFvqquyoTdzA5XwT9J1NDuNIzpCxxYgnDiEmMTQI9IjCjCtr2HVFKeTw5sFlqWIEuSSShGGJdIdgyA83QcO5EXzz5yCfOOAkoJDGkDSGIZ8Bn/Jh/1Nl0D7Jtx2MCVQFbcJw/FciunV7/tRMrix2DnyYmHsqqgrvnh1tI64fTR7iGW1r4YekINg4TVvfwNiYpy//qreQ3JCEetdBYWoJpvazg4Mk9SKbT6rvgM+lhBX8jYabdaJh2vY7vc3MqlhSn5We9vj0ukySSQAIOjWrKAE0+o1ieZQ5zeWtStGWlWl3elc0+wH+Ib9vLzGHfvwUYAKq6LE11+rJNAAAAAElFTkSuQmCC');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (7, 'image', NULL, '.png', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (8, 'image', NULL, '.jpeg', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (9, 'image', NULL, '.gif', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (10, 'msword', NULL, '.doc', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkdJREFUeNqMU01oE0EU/mZ30jZqwJRStYJURUlb0HoQAhYrQZAqBZGcevKoNz1YhCK9eKi9KCIqCAqFWLx58VCC0mrRgFA3ByFQb6JQq9laTLdmZye+N9ldPRhx4O23+36+ee/Li8iPF4GOVxBCjALYhX+fF1rrDzoI0Gg0UFlchGSv8A9By3LPzOTk/ToFfTatEVASJ/JxHAczxeIFTidbZl9maAgif6U4T67hVlf27t6C8/lelMtljI2M4NzExEVyPydiQyL9ejD89Naplj2fvTTH46FareJOoYBcf/+924XCNQpdNwSbnoJT+YarN0sYO3MAj58txzh1OQuOS8tCLpcz46RSKcw5jhtdYG3WFPr2plH3Aowe34OGasTIfo63SWlIuBM+KggEGSOkV/OhKNnSwLv3X7G/J4WlENnP8Y5EonmdUoYkUEpEHciNHwq+r5GwBOZff8KRTBcWCAcJ2c/xhG3HmthNAiseIeogISy8LH3G4UynwUHCqAOLipiEO2FUREDGSCJucFs2HkyfjG95cve0QfZz3Apn52KbtFB/juD/DBb6jj1quQfZoztigngE349HkPTLnGjb6mLnwaXxt7OzN2hVwbunwy1kZF90hNHytwZSiDfo2rfeFJhFoScXGeRvoxQ9QxL2RyPUVlchv1Qeon17Fsl0uvm/oAQr7OBvJFzp1WrSc118LJVMLEkv3d9dtz1uk0mogAlYNDZJAkpaKJuQc7mGa/nWJFn3+srK2raBgSn8x9Get8Y1LMcvAQYAwxgjb1L+BBMAAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (11, 'msword', NULL, '.docx', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkdJREFUeNqMU01oE0EU/mZ30jZqwJRStYJURUlb0HoQAhYrQZAqBZGcevKoNz1YhCK9eKi9KCIqCAqFWLx58VCC0mrRgFA3ByFQb6JQq9laTLdmZye+N9ldPRhx4O23+36+ee/Li8iPF4GOVxBCjALYhX+fF1rrDzoI0Gg0UFlchGSv8A9By3LPzOTk/ToFfTatEVASJ/JxHAczxeIFTidbZl9maAgif6U4T67hVlf27t6C8/lelMtljI2M4NzExEVyPydiQyL9ejD89Naplj2fvTTH46FareJOoYBcf/+924XCNQpdNwSbnoJT+YarN0sYO3MAj58txzh1OQuOS8tCLpcz46RSKcw5jhtdYG3WFPr2plH3Aowe34OGasTIfo63SWlIuBM+KggEGSOkV/OhKNnSwLv3X7G/J4WlENnP8Y5EonmdUoYkUEpEHciNHwq+r5GwBOZff8KRTBcWCAcJ2c/xhG3HmthNAiseIeogISy8LH3G4UynwUHCqAOLipiEO2FUREDGSCJucFs2HkyfjG95cve0QfZz3Apn52KbtFB/juD/DBb6jj1quQfZoztigngE349HkPTLnGjb6mLnwaXxt7OzN2hVwbunwy1kZF90hNHytwZSiDfo2rfeFJhFoScXGeRvoxQ9QxL2RyPUVlchv1Qeon17Fsl0uvm/oAQr7OBvJFzp1WrSc118LJVMLEkv3d9dtz1uk0mogAlYNDZJAkpaKJuQc7mGa/nWJFn3+srK2raBgSn8x9Get8Y1LMcvAQYAwxgjb1L+BBMAAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (12, 'text', NULL, '.md', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAfJJREFUeNqMUj1rG0EQnbtboYhESFfYJp8ESYFgo8qNazltuvyI/InYYFKkDoG4NqjLHwiGgCGFK3N9jCVIYYyRzrY+zljSKu+NtdIanJCFudnd2ffmzcwF77a2hCsIgrdwj+Xf64e19thOJjKdTvXCuA38k73t7d0bBEc0a2WCmIsnSSJ7+/vvmQv2yzGGZJtZYAkajdRurq8lGwyk3+9Lr9dT/21nZxfvNoF75QjMBODZCkgd4puLooXo8VjGIO52u/Kl2ZTG6urXz83mB0Q+KoFdEIQE/zw6UtnlclmGw6G8rtWUpNFo6H2xWJTvSZLOFYx9BSCoAcBS+DiOY3mQy91RoluUuygBAb+EVqul2TudjpKczBpZKpUkyzKp1+sCzL0EWkK1Wp1nd0qc8RzhDTDhogSPgLTtdnsOdEroeWZPnq6soJr7CbQHToHfB3+fC0MSeCVg5r4C1wOOjUA/ez6fl5dQAMxfSoCCSqWiB2Yj8BmaRyJLVbBAB+KVcHl6Kg+Xlu5Mwcll1hdQgPaKzEbIRrsSBufnYo4PDuT5xoYU4tjw8s36+m0P2Hmc6cPbGSkJkfjFTZam8vvwUGMFbJYv0zTvdRPvQ80WwdMMfm9jjETwfEsMscxagC1fnZ1dPFpb+yT/sWyWXRDDdvwRYAB4+UxUy0hc0wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (13, 'presentation', NULL, '.pptx', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAlZJREFUeNqMU01oE0EU/mZ3YrPFCK3aqK2I6KHQ2oKIPxC15CAU9CKo4ElExIJH7aUtxR/8Qb148lyJ9eRZqQaFQAP1kPRk0eChvbTRbltMN5ud3fW9abIqGHHg5c1+b75v3nvzIpbvH8RV5zSEEGcA7MS/VzYIgi+B7yMMQ3zK5SAZvRHP45FzZNfE+PizGgU9tiCAT4f4IK9CoYCJqalrtBVknxnrTqUgKIP3tD/Z7Ep3xwF8P3UPxWIRFwcHcXZkZIjgdySsRUT5dl+4bazYNOdvd/qxdOU1stlshD3NZMbI3eW9VFUPYeBDLS9g7dUoRCwGmeyGdfgCZHsXOC4NA+l0WpeTSCTwplCwG2KGqtZIQMF+OQxnbhrxY5cQP34ZP3LPNc7xTVJqEWq0JinfF2TsIT3HRagU1ktFhK4Lo6sf1dIMnK+z2EI4xy3KaoOptIivlGhkINV6FYHvwWjfC7f0EfPX9+tAy75DGud4zDSj+s0NASMqwXOoBF8hcf4WzM4+ejqpPX8zznGDSCwSp0zYKxIgY89NrME0BFqTe9B688UfL8A4x4167Uw2qRfq9xJ8T32YPZdsOgdW74lIICrB86ISJL3NwJy5HY8TA8Mzk5MPaVTBsxfUp5A9Y40ldC9/9UBmVrfibWeKUX0P38Yk7flbd4p+6yKMN0qolMuQT6aXsPvoAqy2Nv2/4Gcy6hn8TYSZTqUiHdvGfD6vYxZtOlZtuyVKk0WIwALcNDZJDZQ0UCZ5Pssc5vKtFlnH2uLiyuaengf4jxU4zgpzuB0/BRgAO1gmOtGmT+8AAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (14, 'pdf', NULL, '.pdf', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAjtJREFUeNqMU79PFEEU/nZ2jvPUM5JwFzUaEmww/AOGgsCGhsICSxIqCrQjQK4hQmOBhRdCZeslFyjFDghXk2gue8VVmkiUEM9LXNScy93tzvreOLtuYYyTfPsmb973vR8za70FsLm+DsuyHtD2Jv69akqp9yoMEUWRdkj+zFUqqM7P36psbLzo0WGfoRRCCooDXddF5fDwEW0twrtY0aoDzy8Dy7Y5CQkBoU/oEWyqLru4iEajgbmZGTxcW3tM7iMS1iJWE4iu0SZLEIZ4QfAJHcJPwtDZGWq1WtLHdrX6hMxT3UKQyioyGdzodvFxZATq5ATK+KUQcBxHt5PP57Hvul4sJgJTKmcNR0fRbzYxMD2dtMB2QEotQoPWpCAMLQJbiG6qZHt8HO1yGdcXFpCdnETXiFyiytIiYRBYBLYQF6bX3OwsCqUSrkxNAXQD93Z3cXt1VYtkbDsRsX8LiFhA+qbM+1tb+Ly3hy8HB/har+NHq6WvkxMIIrEIL5tsQALxDCRnYLweHtaOyAxVmX3PCMBUYlMbJGAlAhRQpkEuK0NSKTLj7tJSIqAr4Bb6/T8VUPDKh2Jx5ZXjlN7s7Dyjp6qJyrxCtuxLXh7fQrqF/UIB7sQEe3UezsYkbc3jApUNI8L+uIVOuw35kj53Tk+RGxzU/wVfkzAV/E2EmX6nI33Pw6fjY32Wo03xm+dlkzJZhAgswENjSBqg5Gsky7HMYS5nzRGK31ut86tjY5v4j6V8/5w5PI5fAgwAUXIN2+nu/TQAAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (15, 'email', NULL, '.msg', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA2lpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wUmlnaHRzPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvcmlnaHRzLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcFJpZ2h0czpNYXJrZWQ9IkZhbHNlIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOkE4NkNGMEIxRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOkE4NkNGMEIwRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDUzMgV2luZG93cyI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ1dWlkOkFDMUYyRTgzMzI0QURGMTFBQUI4QzUzOTBEODVCNUIzIiBzdFJlZjpkb2N1bWVudElEPSJ1dWlkOkM5RDM0OTY2NEEzQ0REMTFCMDhBQkJCQ0ZGMTcyMTU2Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+rI6PHAAAAkRJREFUeNqkU0tIG1EUPZlMPsR8bFoQk4D2gxprjWlqu+iqdJ2FIl1XCRUX0p2uBHHhvrgQa9CtFNFFIIuua7soEkRBbZtGSokloUmMTUxm3kx6bxokBVtKvXDnMe+dc+6Ze98YarUaLhMSLhnyk9nZMK2e/+SnZU3TvM/C4cXBnh64nc5/YuWKRbw/OMDLWGxC0oQwhIj8bm8PmUIBQtf/moxhLHOYKwkhJJfdjmB3N97u7CCTz/+ZTGeMYSxzmCsJVZU0moSTNu76/dhKJJDJ5SA07bfkPT5jDGOZw1yZH6yuEsjBIr29eLO9jQeBACxULb+0BHF8jHKlgjtuN2pWK05MJpi9XtxLpa7LKguQmiJEvUEmiwU+nw9bJOJfXEQnicrDw7ANDcHS1VXHKKkUfiws4NHu7n1JVRRJazgoUZVvZNXX1oZgXx9KR0eQQyFcmZ5Gdn0dybExfIhEoKkq7JOTsFUqrnMHTP5OHb7a2gqDJMHucEDQWLny1/l5GGUZN1dW6g4+jY/jFn0aajWJHRjPuHI2CxeRJKPxvOtWs7luW0km0T41hcToaF2gSg44dE0zyYVczvyZrHZ2dMBMhOY4YyC5k6lpp/E4gquryMdiuE1OihsbPAWbwTUwENF1/cZFN+7V4eHTh5ub7bLHg/zyMleEsZEt1OzX0egXmchR0bDUHIFyGc5qdbC0tmZvGRlxXJuZ+fX3kaPK3BxO0unTkqp+NDj6+3GRQHx/n5fHNNznlB5GKE1J72naf/FTgAEAy/9ZHAO9HmIAAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (16, 'email', NULL, '.eml', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA2lpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wUmlnaHRzPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvcmlnaHRzLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcFJpZ2h0czpNYXJrZWQ9IkZhbHNlIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOkE4NkNGMEIxRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOkE4NkNGMEIwRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDUzMgV2luZG93cyI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ1dWlkOkFDMUYyRTgzMzI0QURGMTFBQUI4QzUzOTBEODVCNUIzIiBzdFJlZjpkb2N1bWVudElEPSJ1dWlkOkM5RDM0OTY2NEEzQ0REMTFCMDhBQkJCQ0ZGMTcyMTU2Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+rI6PHAAAAkRJREFUeNqkU0tIG1EUPZlMPsR8bFoQk4D2gxprjWlqu+iqdJ2FIl1XCRUX0p2uBHHhvrgQa9CtFNFFIIuua7soEkRBbZtGSokloUmMTUxm3kx6bxokBVtKvXDnMe+dc+6Ze98YarUaLhMSLhnyk9nZMK2e/+SnZU3TvM/C4cXBnh64nc5/YuWKRbw/OMDLWGxC0oQwhIj8bm8PmUIBQtf/moxhLHOYKwkhJJfdjmB3N97u7CCTz/+ZTGeMYSxzmCsJVZU0moSTNu76/dhKJJDJ5SA07bfkPT5jDGOZw1yZH6yuEsjBIr29eLO9jQeBACxULb+0BHF8jHKlgjtuN2pWK05MJpi9XtxLpa7LKguQmiJEvUEmiwU+nw9bJOJfXEQnicrDw7ANDcHS1VXHKKkUfiws4NHu7n1JVRRJazgoUZVvZNXX1oZgXx9KR0eQQyFcmZ5Gdn0dybExfIhEoKkq7JOTsFUqrnMHTP5OHb7a2gqDJMHucEDQWLny1/l5GGUZN1dW6g4+jY/jFn0aajWJHRjPuHI2CxeRJKPxvOtWs7luW0km0T41hcToaF2gSg44dE0zyYVczvyZrHZ2dMBMhOY4YyC5k6lpp/E4gquryMdiuE1OihsbPAWbwTUwENF1/cZFN+7V4eHTh5ub7bLHg/zyMleEsZEt1OzX0egXmchR0bDUHIFyGc5qdbC0tmZvGRlxXJuZ+fX3kaPK3BxO0unTkqp+NDj6+3GRQHx/n5fHNNznlB5GKE1J72naf/FTgAEAy/9ZHAO9HmIAAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (17, 'email', NULL, '.email', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA2lpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wUmlnaHRzPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvcmlnaHRzLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcFJpZ2h0czpNYXJrZWQ9IkZhbHNlIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOkE4NkNGMEIxRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOkE4NkNGMEIwRjE1MzExRTA5MjM3OUJERjBCOTQ1QkZGIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDUzMgV2luZG93cyI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ1dWlkOkFDMUYyRTgzMzI0QURGMTFBQUI4QzUzOTBEODVCNUIzIiBzdFJlZjpkb2N1bWVudElEPSJ1dWlkOkM5RDM0OTY2NEEzQ0REMTFCMDhBQkJCQ0ZGMTcyMTU2Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+rI6PHAAAAkRJREFUeNqkU0tIG1EUPZlMPsR8bFoQk4D2gxprjWlqu+iqdJ2FIl1XCRUX0p2uBHHhvrgQa9CtFNFFIIuua7soEkRBbZtGSokloUmMTUxm3kx6bxokBVtKvXDnMe+dc+6Ze98YarUaLhMSLhnyk9nZMK2e/+SnZU3TvM/C4cXBnh64nc5/YuWKRbw/OMDLWGxC0oQwhIj8bm8PmUIBQtf/moxhLHOYKwkhJJfdjmB3N97u7CCTz/+ZTGeMYSxzmCsJVZU0moSTNu76/dhKJJDJ5SA07bfkPT5jDGOZw1yZH6yuEsjBIr29eLO9jQeBACxULb+0BHF8jHKlgjtuN2pWK05MJpi9XtxLpa7LKguQmiJEvUEmiwU+nw9bJOJfXEQnicrDw7ANDcHS1VXHKKkUfiws4NHu7n1JVRRJazgoUZVvZNXX1oZgXx9KR0eQQyFcmZ5Gdn0dybExfIhEoKkq7JOTsFUqrnMHTP5OHb7a2gqDJMHucEDQWLny1/l5GGUZN1dW6g4+jY/jFn0aajWJHRjPuHI2CxeRJKPxvOtWs7luW0km0T41hcToaF2gSg44dE0zyYVczvyZrHZ2dMBMhOY4YyC5k6lpp/E4gquryMdiuE1OihsbPAWbwTUwENF1/cZFN+7V4eHTh5ub7bLHg/zyMleEsZEt1OzX0egXmchR0bDUHIFyGc5qdbC0tmZvGRlxXJuZ+fX3kaPK3BxO0unTkqp+NDj6+3GRQHx/n5fHNNznlB5GKE1J72naf/FTgAEAy/9ZHAO9HmIAAAAASUVORK5CYII=');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (18, 'tabular', NULL, '.xlsm', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAkJJREFUeNqMU11LVGEQfs7HVksttUSGYZBEGLvdFmGCtdKFRTddRS6RRFA/QJE2FSqobopCsLtgaTO66UYEkb7ACyGEsyC0YETQTYuwa8Z61PPVPK/nnBDaaGB2Zp9553ln5p2j3X99HfMLrdA07QKAVvxb3vm+/8X3PARBgMrsLEyiHe01VL6mDxRHR59tSNCh+j48OcSDFMuyUJyZuSGuJrpI7GhXFzSp4IP43c2u3Lv7EDqPXUW5XMbl3l5cLBRuCvxWiBWJ6XhO9/Cl501rvvuqn+2hVqthrFRCLpMZf1oqDUvoniJYc9ekVA8jpbxK6O+5hfcLb/Ct+hl3+l6AcVPXkcvlVDupVArTllWPLlAEbuCqg9fO3sb49IgKtO/PxPg2U0blunBlLhTX87SIQLcdWx3MnxnE2FRB7ACIncqcVzj9HYmEImElbMdzXU2UFvqquyoTdzA5XwT9J1NDuNIzpCxxYgnDiEmMTQI9IjCjCtr2HVFKeTw5sFlqWIEuSSShGGJdIdgyA83QcO5EXzz5yCfOOAkoJDGkDSGIZ8Bn/Jh/1Nl0D7Jtx2MCVQFbcJw/FciunV7/tRMrix2DnyYmHsqqgrvnh1tI64fTR7iGW1r4YekINg4TVvfwNiYpy//qreQ3JCEetdBYWoJpvazg4Mk9SKbT6rvgM+lhBX8jYabdaJh2vY7vc3MqlhSn5We9vj0ukySSQAIOjWrKAE0+o1ieZQ5zeWtStGWlWl3elc0+wH+Ib9vLzGHfvwUYAKq6LE11+rJNAAAAAElFTkSuQmCC');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (19, 'image', NULL, '.jpg', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAdRJREFUeNqkkz1rFFEUhp+587nzsbMbE8PumkiWoMWKQQs7QdDCxkKEgP9Af0QgkFZsrQRbC/UP2GppYxdSCYqNm41xd8zOnRnPnYFgqbsXLjNzmec973k516qqimWWYsnl7O7vP5Bnf0H+m1MUxeDNwcGLRehHe3tPnUJrq5Qcbj+3UBa4ttiSPddg4mm3ZAdyJs0OV2HUA13C7s0Kwzpaa1XInzuXLDwHUgFWI/j+E1pu821inszgmjS6M4DZHAxjWEfneS3Qjz5wpbdFN+rXla+uw3rSCGUCDC80Ts50I1oLCFsL6LLk/aeXfAxC7t94yJ3R3dqycWRsZzmshJAXzVnomjbKRiA3AqJ2eHRIJ+3w+vQVJ6df2VjbpLeywcV2l5Ynpa2wgb2mtd9lRV4LzOeqELWzkwE/fjlMxx5vJ59pBUdEYUQcxcRxTBInpElbhPtsrQ24ddnHsOcOhr17eJ6H7/uEYUiSxKRpQrfbli1wGtGWEKLIRfkKXWXnDuxSHPy9qjrhgkzSUyqTd8V0WnF8XBAEQV3k+qg0DmxnMh57tuvy7tnjfxwfUyzDdj0Ma0Xb209UGG4uMonlbPZFZg/JlY65F//JazNf1rLX+Y8AAwAgusJW985f5wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (20, 'archive', NULL, '.zip', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAh5JREFUeNp0UztoFFEUPTOzoxKDupINEgjoWAoWWaIIVrLYaiUKWqRJsAkKNilEVCQWgmIj2lhYGLMoWtiYtRNBVkH8gBIyLEYsNJFoNnF3531897757aIXDvfd++4977yfU78KNgcYM24nYnsToj1xB0u3xzFQDrAR3dbQwF0aFLS2GeN2jU4+OQ8pLcH9H5ibCxCGIconSlmr56F+88jlJEwJjLkQEXQUcRAEAYrFIhPozpa0yPF9mB43JZAqI1BmdR0rICMCMpXLOa4L05MRqEyBp/9DkM/BEJge758KqFBJkSaq1WqsQOT6uxW4RBDDUzKCFBa095P7FrgoyRE0FNeSKCF7CUxGCcGgQ7w047BPcp6/AV8/zVsCjTL1dRFoI1XF2D/8EZVKhZVQ7JrrW/w8z+NDF9WkqR+j8+tRECHBq8U9qNVqmDo1kOZWV1awY3gI652OVUEKRLwXA49kyhgjpdesYPreEsc8J+0WV1strqe+/C14Vr59SG9/HmAF545t5pySHoSw21trt1kB38L7L/kzkPxoCHu3vmAF12bXkDwwGfvxRinbwoVZs1oDaHWwSStbQHj36yArOHvUtzkz1zLSyS8vr3M99dGD6LvyCIO//6DfdVz4BZ8xsu0lK7j+OOKY5prNJvuJh/1Pn3/AA9PXZ34xthsMnT6MM8Egduf/7NRMoT59XIz2fGWE37Fw6xlumOG3vwIMAJg6gUpZKWmMAAAAAElFTkSuQmCC');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (21, 'text', NULL, '.csv', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAfJJREFUeNqMUj1rG0EQnbtboYhESFfYJp8ESYFgo8qNazltuvyI/InYYFKkDoG4NqjLHwiGgCGFK3N9jCVIYYyRzrY+zljSKu+NtdIanJCFudnd2ffmzcwF77a2hCsIgrdwj+Xf64e19thOJjKdTvXCuA38k73t7d0bBEc0a2WCmIsnSSJ7+/vvmQv2yzGGZJtZYAkajdRurq8lGwyk3+9Lr9dT/21nZxfvNoF75QjMBODZCkgd4puLooXo8VjGIO52u/Kl2ZTG6urXz83mB0Q+KoFdEIQE/zw6UtnlclmGw6G8rtWUpNFo6H2xWJTvSZLOFYx9BSCoAcBS+DiOY3mQy91RoluUuygBAb+EVqul2TudjpKczBpZKpUkyzKp1+sCzL0EWkK1Wp1nd0qc8RzhDTDhogSPgLTtdnsOdEroeWZPnq6soJr7CbQHToHfB3+fC0MSeCVg5r4C1wOOjUA/ez6fl5dQAMxfSoCCSqWiB2Yj8BmaRyJLVbBAB+KVcHl6Kg+Xlu5Mwcll1hdQgPaKzEbIRrsSBufnYo4PDuT5xoYU4tjw8s36+m0P2Hmc6cPbGSkJkfjFTZam8vvwUGMFbJYv0zTvdRPvQ80WwdMMfm9jjETwfEsMscxagC1fnZ1dPFpb+yT/sWyWXRDDdvwRYAB4+UxUy0hc0wAAAABJRU5ErkJggg==');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (22, 'web', NULL, '.html', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAmBJREFUeNqMU01rU0EUPZm8NIR8aFIbbfGjrS0tiSAY0S66imsR1K0rXXTlP7CF4EJcuFDBIm4shG78A1oQaoOgIAasGGyLFqoxpn1Jm7wmTV5mvHdsmocW8cJ9M2/uPWfOvTPjujo5CTaXy3WRhl78215KKZdlqwWlFHKZDAyesNHYNzM1Nd2gYJNdSrQo1o5ns1nMzM1N8F7kS7w2Oj4OwWy77pIMaja1N+p11CwL1WoVlUpFj89SqWnKu0DY4bYko0XgXXMxtaCvx+3uiLZt2ERsmiYeptNIxmKP7qfTtyhyWxPIDoFgsNA0+IskmUzqcoLBIJ5ns6U9BbZTgYNgPxJWoqdUbqcECvxZwudSC08X61gpUxNpbTAEXB5246hf7wLC7EugS1ha38G9hSLODocx1C3g8QgYboEnbwq4kfBjNKAJxB7IZmm/XTDt4xc5nO4PUdMs9IS8WF3dQHfYj8RQGLOvvuqyOLeNM2xnCaTgw8cVfMMh5ItFZJZMBH0+vJ19j5H4CD7lvsAjEgx0lEBn3lbDq7Jew7olYDYENjYbUD+3caJ/FAuvF3GAYm7uQbMpOqfg6AEriJ/swzvzO9xdQXi6uqBEE9ZWCX4PMDLQq6+h7ezBZj7f7oE+hZtXziOkttHj9WIgEsFgNApj20IAFiYuJfQpcS5jGCuW5+dhrq3xtTWY8dTxMB5cP4dYpA4zvwzzxwpiRxTuXjuD+LGDWgHnMoaxbD7y6OGxsZRymCRvSano8ih6XIoemarbttqhf85lDGONNsFWoVAOxON38B8ma7XyLoH9S4ABADQ1VpwuiBRTAAAAAElFTkSuQmCC');
INSERT INTO document_type (type_id, type, color, extension, icon) VALUES (23, 'web', NULL, '.htm', 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAmBJREFUeNqMU01rU0EUPZm8NIR8aFIbbfGjrS0tiSAY0S66imsR1K0rXXTlP7CF4EJcuFDBIm4shG78A1oQaoOgIAasGGyLFqoxpn1Jm7wmTV5mvHdsmocW8cJ9M2/uPWfOvTPjujo5CTaXy3WRhl78215KKZdlqwWlFHKZDAyesNHYNzM1Nd2gYJNdSrQo1o5ns1nMzM1N8F7kS7w2Oj4OwWy77pIMaja1N+p11CwL1WoVlUpFj89SqWnKu0DY4bYko0XgXXMxtaCvx+3uiLZt2ERsmiYeptNIxmKP7qfTtyhyWxPIDoFgsNA0+IskmUzqcoLBIJ5ns6U9BbZTgYNgPxJWoqdUbqcECvxZwudSC08X61gpUxNpbTAEXB5246hf7wLC7EugS1ha38G9hSLODocx1C3g8QgYboEnbwq4kfBjNKAJxB7IZmm/XTDt4xc5nO4PUdMs9IS8WF3dQHfYj8RQGLOvvuqyOLeNM2xnCaTgw8cVfMMh5ItFZJZMBH0+vJ19j5H4CD7lvsAjEgx0lEBn3lbDq7Jew7olYDYENjYbUD+3caJ/FAuvF3GAYm7uQbMpOqfg6AEriJ/swzvzO9xdQXi6uqBEE9ZWCX4PMDLQq6+h7ezBZj7f7oE+hZtXziOkttHj9WIgEsFgNApj20IAFiYuJfQpcS5jGCuW5+dhrq3xtTWY8dTxMB5cP4dYpA4zvwzzxwpiRxTuXjuD+LGDWgHnMoaxbD7y6OGxsZRymCRvSano8ih6XIoemarbttqhf85lDGONNsFWoVAOxON38B8ma7XyLoH9S4ABADQ1VpwuiBRTAAAAAElFTkSuQmCC');

-- Table: note
DROP TABLE IF EXISTS note;

CREATE TABLE IF NOT EXISTS note (
    note_id           INTEGER PRIMARY KEY AUTOINCREMENT
                              NOT NULL,
    title             TEXT    NOT NULL
                              DEFAULT Untitled,
    text              TEXT,
    creation_date     TEXT,
    modification_date TEXT,
    workspace_id      INTEGER REFERENCES workspace (workspace_id) 
                              NOT NULL
);


-- Table: note_has_tag
DROP TABLE IF EXISTS note_has_tag;

CREATE TABLE IF NOT EXISTS note_has_tag (
    tag_id  INTEGER NOT NULL,
    note_id INTEGER NOT NULL,
    PRIMARY KEY (
        tag_id,
        note_id
    ),
    FOREIGN KEY (
        tag_id
    )
    REFERENCES tags (tag_id) ON DELETE CASCADE,
    FOREIGN KEY (
        note_id
    )
    REFERENCES note (note_id) ON DELETE CASCADE
);


-- Table: signage
DROP TABLE IF EXISTS signage;

CREATE TABLE IF NOT EXISTS signage (
    refKey            TEXT,
    title             TEXT,
    status_id         INTEGER REFERENCES signage_status (status_id) 
                              DEFAULT (1),
    type_id           INTEGER NOT NULL
                              REFERENCES signage_type (type_id) 
                              DEFAULT (1),
    note              TEXT,
    creation_date     TEXT,
    modification_date TEXT,
    source_link       TEXT,
    source_type       TEXT,
    position          TEXT,
    signage_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id      INTEGER REFERENCES workspace (workspace_id) 
                              NOT NULL,
    uid               TEXT    UNIQUE
);


-- Table: signage_docs
DROP TABLE IF EXISTS signage_docs;

CREATE TABLE IF NOT EXISTS signage_docs (
    signage_id  REFERENCES signage (signage_id) 
                NOT NULL,
    doc_id      REFERENCES document (doc_id) 
                NOT NULL
);


-- Table: signage_has_tag
DROP TABLE IF EXISTS signage_has_tag;

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


-- Table: signage_relation
DROP TABLE IF EXISTS signage_relation;

CREATE TABLE IF NOT EXISTS signage_relation (
    signage_id INTEGER REFERENCES signage (signage_id) ON DELETE CASCADE,
    related_id INTEGER REFERENCES signage (signage_id) 
);


-- Table: signage_status
DROP TABLE IF EXISTS signage_status;

CREATE TABLE IF NOT EXISTS signage_status (
    status_id INTEGER PRIMARY KEY
                      NOT NULL,
    status    TEXT    NOT NULL,
    color     TEXT,
    icon      TEXT,
    icon_obj  BLOB,
    type_id           REFERENCES signage_type (type_id) 
                      NOT NULL
);

INSERT INTO signage_status (status_id, status, color, icon, icon_obj, type_id) VALUES (1, 'Open', '#32a852', NULL, NULL, 1);
INSERT INTO signage_status (status_id, status, color, icon, icon_obj, type_id) VALUES (2, 'Planned', '#0000FF', NULL, NULL, 1);
INSERT INTO signage_status (status_id, status, color, icon, icon_obj, type_id) VALUES (3, 'On Hold', '#e28743', NULL, NULL, 1);
INSERT INTO signage_status (status_id, status, color, icon, icon_obj, type_id) VALUES (4, 'Closed', '#76b5c5', NULL, NULL, 1);
INSERT INTO signage_status (status_id, status, color, icon, icon_obj, type_id) VALUES (5, 'Rejected', '#FF0000', NULL, NULL, 1);
INSERT INTO signage_status (status_id, status, color, icon, icon_obj, type_id) VALUES (6, 'Canceled', '#eeeee4', NULL, NULL, 1);

-- Table: signage_type
DROP TABLE IF EXISTS signage_type;

CREATE TABLE IF NOT EXISTS signage_type (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT
                    NOT NULL,
    type    TEXT    NOT NULL,
    color   TEXT,
    icon    BLOB
);

INSERT INTO signage_type (type_id, type, color, icon) VALUES (1, 'Request', NULL, NULL);
INSERT INTO signage_type (type_id, type, color, icon) VALUES (2, 'Question', NULL, NULL);
INSERT INTO signage_type (type_id, type, color, icon) VALUES (3, 'Todo', NULL, NULL);
INSERT INTO signage_type (type_id, type, color, icon) VALUES (4, 'Finding', NULL, NULL);

-- Table: tags
DROP TABLE IF EXISTS tags;

CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT
                   NOT NULL,
    name   TEXT    NOT NULL
                   UNIQUE,
    color  TEXT,
    icon   TEXT
);

INSERT INTO tags (tag_id, name, color, icon) VALUES (1, 'PSMF', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (3, 'Signal', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (4, 'Safety variation', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (5, 'PASS', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (6, 'Audit', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (7, 'LCP', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (8, 'QPPV', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (9, 'Risk minimization', NULL, NULL);
INSERT INTO tags (tag_id, name, color, icon) VALUES (10, 'QMS', NULL, NULL);

-- Table: workspace
DROP TABLE IF EXISTS workspace;

CREATE TABLE IF NOT EXISTS workspace (
    workspace_id      INTEGER PRIMARY KEY AUTOINCREMENT
                              NOT NULL,
    name              TEXT    NOT NULL
                              UNIQUE,
    root              TEXT    NOT NULL,
    state             INTEGER NOT NULL
                              DEFAULT (1),
    attachments_path  TEXT,
    notebook_path     TEXT,
    onenote_section   TEXT,
    creation_date     TEXT,
    modification_date TEXT
);


-- Index: idx_document_dirpath
DROP INDEX IF EXISTS idx_document_dirpath;

CREATE INDEX IF NOT EXISTS idx_document_dirpath ON document (
    dirpath COLLATE BINARY
);


-- Index: idx_document_filepath
DROP INDEX IF EXISTS idx_document_filepath;

CREATE UNIQUE INDEX IF NOT EXISTS idx_document_filepath ON document (
    filepath COLLATE BINARY
);


-- Index: idx_document_type
DROP INDEX IF EXISTS idx_document_type;

CREATE INDEX IF NOT EXISTS idx_document_type ON document_type (
    type,
    extension
);


-- Trigger: CheckDocSourceID
DROP TRIGGER IF EXISTS CheckDocSourceID;
CREATE TRIGGER IF NOT EXISTS CheckDocSourceID
                      BEFORE INSERT
                          ON signage
                    FOR EACH ROW
                        WHEN NEW.source_type = 'document'
BEGIN
    SELECT RAISE(ROLLBACK, "Invalid source_id for document") 
     WHERE (
               SELECT 1
                 FROM document
                WHERE doc_id = NEW.source_link
           )
           IS NULL;
END;


-- Trigger: CheckNoteSourceID
DROP TRIGGER IF EXISTS CheckNoteSourceID;
CREATE TRIGGER IF NOT EXISTS CheckNoteSourceID
                      BEFORE INSERT
                          ON signage
                    FOR EACH ROW
                        WHEN NEW.source_type = 'note'
BEGIN
    SELECT RAISE(ROLLBACK, "Invalid source_id for note") 
     WHERE (
               SELECT 1
                 FROM note
                WHERE note_id = NEW.source_link
           )
           IS NULL;
END;


-- Trigger: UpdateStateAfterInsert
DROP TRIGGER IF EXISTS UpdateStateAfterInsert;
CREATE TRIGGER IF NOT EXISTS UpdateStateAfterInsert
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
DROP TRIGGER IF EXISTS UpdateWorkspaceState;
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
