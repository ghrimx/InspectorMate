-- Trigger: DROP
DROP TRIGGER IF EXISTS afterEvidenceUpdate;

DROP TRIGGER IF EXISTS afterEvidenceInsert;

DROP TRIGGER IF EXISTS afterEvidenceDelete;

DROP TRIGGER IF EXISTS updateSignageIdAfterInsert;

DROP TRIGGER IF EXISTS afterRefkeyUpdate;

DROP TRIGGER IF EXISTS updateEvidenceAfterUpdate;


-- Remove columns from signage
ALTER TABLE signage DROP COLUMN evidence;

ALTER TABLE signage DROP COLUMN evidence_eol;







