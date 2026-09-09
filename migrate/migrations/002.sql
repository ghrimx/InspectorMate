-- Table: connectors
CREATE TABLE IF NOT EXISTS connectors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type         TEXT    NOT NULL,
    name         TEXT,
    value        TEXT    NOT NULL,
    workspace_id         REFERENCES workspace (workspace_id) ON DELETE CASCADE
                         NOT NULL,
    UNIQUE (
        type,
        value,
        workspace_id
    )
);

-- Remove onenote_section from workspace
ALTER TABLE workspace DROP COLUMN onenote_section;



