-- save msids
-- depends: 20211020_02_Zp8BO-add-updated-at-timestamps
ALTER TABLE listens ADD COLUMN artist_msid CHAR(36);
ALTER TABLE listens ADD COLUMN recording_msid CHAR(36);
ALTER TABLE listens ADD COLUMN release_msid CHAR(36);

CREATE INDEX listens_artist_msid ON listens ( artist_msid );
CREATE INDEX listens_recording_msid ON listens ( recording_msid );
CREATE INDEX listens_release_msid ON listens ( release_msid );
