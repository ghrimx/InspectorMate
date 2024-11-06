/* Clear table content and reset autoincrement */
delete from signage;    
delete from sqlite_sequence where name='signage';

delete from document;
delete from sqlite_sequence where name='document';

delete from workspace;
delete from sqlite_sequence where name='workspace';