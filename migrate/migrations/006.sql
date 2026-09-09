-- finding color
UPDATE signage_type
   SET color = '#ff0000'
 WHERE uid = 3;

-- todo color
UPDATE signage_type
   SET color = '#0066ff'
 WHERE uid = 1;

-- Add background color column to signage table
ALTER TABLE signage ADD background TEXT;