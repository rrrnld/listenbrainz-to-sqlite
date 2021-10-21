-- remove updated_at timestamps

ALTER TABLE artists DROP COLUMN updated_at;
ALTER TABLE listen_artists DROP COLUMN updated_at;
ALTER TABLE listens DROP COLUMN updated_at;
ALTER TABLE recording_artists DROP COLUMN updated_at;
ALTER TABLE recordings DROP COLUMN updated_at;
ALTER TABLE release_artists DROP COLUMN updated_at;
ALTER TABLE release_recordings DROP COLUMN updated_at;
ALTER TABLE releases DROP COLUMN updated_at;

DROP TRIGGER artists_update_ts_on_insert;
DROP TRIGGER artists_update_ts_on_update;
DROP TRIGGER listen_artists_update_ts_on_insert;
DROP TRIGGER listen_artists_update_ts_on_update;
DROP TRIGGER listens_update_ts_on_insert;
DROP TRIGGER listens_update_ts_on_update;
DROP TRIGGER recording_artists_update_ts_on_insert;
DROP TRIGGER recording_artists_update_ts_on_update;
DROP TRIGGER recordings_update_ts_on_insert;
DROP TRIGGER recordings_update_ts_on_update;
DROP TRIGGER release_artists_update_ts_on_insert;
DROP TRIGGER release_artists_update_ts_on_update;
DROP TRIGGER release_recordings_update_ts_on_insert;
DROP TRIGGER release_recordings_update_ts_on_update;
DROP TRIGGER releases_update_ts_on_insert;
DROP TRIGGER releases_update_ts_on_update;
