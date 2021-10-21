-- add updated_at timestamps
-- depends: 20211020_01_pPnmB-create-initial-schema

ALTER TABLE artists ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE listen_artists ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE listens ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE recording_artists ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE recordings ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE release_artists ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE release_recordings ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE releases ADD COLUMN updated_at TIMESTAMP;

UPDATE artists SET updated_at = datetime("now", "-1 second");
UPDATE listen_artists SET updated_at = datetime("now", "-1 second");
UPDATE listens SET updated_at = datetime("now", "-1 second");
UPDATE recording_artists SET updated_at = datetime("now", "-1 second");
UPDATE recordings SET updated_at = datetime("now", "-1 second");
UPDATE release_artists SET updated_at = datetime("now", "-1 second");
UPDATE release_recordings SET updated_at = datetime("now", "-1 second");
UPDATE releases SET updated_at = datetime("now", "-1 second");

CREATE TRIGGER artists_update_ts_on_insert
AFTER INSERT ON artists
BEGIN
  UPDATE artists SET updated_at = datetime("now") WHERE artists.mbid = NEW.mbid;
END;
CREATE TRIGGER artists_update_ts_on_update
AFTER UPDATE ON artists
BEGIN
  UPDATE artists SET updated_at = datetime("now") WHERE artists.mbid = NEW.mbid;
END;

CREATE TRIGGER listen_artists_update_ts_on_insert
AFTER INSERT ON listen_artists
BEGIN
  UPDATE listen_artists SET updated_at = datetime("now") WHERE listen_artists.rowid = NEW.rowid;
END;
CREATE TRIGGER listen_artists_update_ts_on_update
AFTER UPDATE ON listen_artists
BEGIN
  UPDATE listen_artists SET updated_at = datetime("now") WHERE listen_artists.rowid = NEW.rowid;
END;

CREATE TRIGGER listens_update_ts_on_insert
AFTER INSERT ON listens
BEGIN
  UPDATE listens SET updated_at = datetime("now") WHERE listens.id = NEW.id;
END;
CREATE TRIGGER listens_update_ts_on_update
AFTER UPDATE ON listens
BEGIN
  UPDATE listens SET updated_at = datetime("now") WHERE listens.id = NEW.id;
END;

CREATE TRIGGER recording_artists_update_ts_on_insert
AFTER INSERT ON recording_artists
BEGIN
  UPDATE recording_artists SET updated_at = datetime("now") WHERE recording_artists.rowid = NEW.rowid;
END;
CREATE TRIGGER recording_artists_update_ts_on_update
AFTER UPDATE ON recording_artists
BEGIN
  UPDATE recording_artists SET updated_at = datetime("now") WHERE recording_artists.rowid = NEW.rowid;
END;

CREATE TRIGGER recordings_update_ts_on_insert
AFTER INSERT ON recordings
BEGIN
  UPDATE recordings SET updated_at = datetime("now") WHERE recordings.mbid = NEW.mbid;
END;
CREATE TRIGGER recordings_update_ts_on_update
AFTER UPDATE ON recordings
BEGIN
  UPDATE recordings SET updated_at = datetime("now") WHERE recordings.mbid = NEW.mbid;
END;

CREATE TRIGGER release_artists_update_ts_on_insert
AFTER INSERT ON release_artists
BEGIN
  UPDATE release_artists SET updated_at = datetime("now") WHERE release_artists.rowid = NEW.rowid;
END;
CREATE TRIGGER release_artists_update_ts_on_update
AFTER UPDATE ON release_artists
BEGIN
  UPDATE release_artists SET updated_at = datetime("now") WHERE release_artists.rowid = NEW.rowid;
END;

CREATE TRIGGER release_recordings_update_ts_on_insert
AFTER INSERT ON release_recordings
BEGIN
  UPDATE release_recordings SET updated_at = datetime("now") WHERE release_recordings.rowid = NEW.rowid;
END;
CREATE TRIGGER release_recordings_update_ts_on_update
AFTER UPDATE ON release_recordings
BEGIN
  UPDATE release_recordings SET updated_at = datetime("now") WHERE release_recordings.rowid = NEW.rowid;
END;

CREATE TRIGGER releases_update_ts_on_insert
AFTER INSERT ON releases
BEGIN
  UPDATE releases SET updated_at = datetime("now") WHERE releases.mbid = NEW.mbid;
END;
CREATE TRIGGER releases_update_ts_on_update
AFTER UPDATE ON releases
BEGIN
  UPDATE releases SET updated_at = datetime("now") WHERE releases.mbid = NEW.mbid;
END;
