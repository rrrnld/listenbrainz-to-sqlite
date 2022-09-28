-- save msids
-- depends: 20220927_01_0FE35-save-msids.sql
DROP INDEX listens_artist_msid;
DROP INDEX listens_recording_msid;
DROP INDEX listens_release_msid;

ALTER TABLE listens DROP COLUMN;
ALTER TABLE listens DROP COLUMN;
ALTER TABLE listens DROP COLUMN;
