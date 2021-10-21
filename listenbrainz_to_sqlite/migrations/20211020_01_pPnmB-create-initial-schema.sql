-- create initial schema
-- depends:

CREATE TABLE IF NOT EXISTS artists (
    mbid CHAR(36) PRIMARY KEY,
    name TEXT,
    sort_name TEXT,
    country CHAR(2),
    disambiguation TEXT,
    gender VARCHAR(255),
    gender_id CHAR(36),
    type VARCHAR(255),
    type_id CHAR(36)
);
CREATE INDEX IF NOT EXISTS artists_name ON artists ( name );
CREATE INDEX IF NOT EXISTS artists_country ON artists ( country );
CREATE INDEX IF NOT EXISTS artists_gender ON artists ( gender );
CREATE INDEX IF NOT EXISTS artists_gender_id ON artists ( gender_id );
CREATE INDEX IF NOT EXISTS artists_type ON artists ( type );
CREATE INDEX IF NOT EXISTS artists_type_id ON artists ( type_id );


CREATE TABLE IF NOT EXISTS recordings (
    mbid CHAR(36) PRIMARY KEY,
    title TEXT,
    disambiguation TEXT,
    first_release_date TIMESTAMP,
    length INTEGER
);
CREATE INDEX IF NOT EXISTS recordings_title ON recordings ( title );
CREATE INDEX IF NOT EXISTS recordings_first_release_date ON recordings (
    first_release_date
);
CREATE INDEX IF NOT EXISTS recordings_length ON recordings ( length );


-- Use this to find out all of the artists performing in a recording
CREATE TABLE IF NOT EXISTS recording_artists (
    artist_mbid CHAR(36),
    recording_mbid CHAR(36),
    UNIQUE ( artist_mbid, recording_mbid ),
    FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid ),
    FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid )
);
CREATE INDEX IF NOT EXISTS recording_artists_by_artist ON recording_artists (
    artist_mbid
);
CREATE INDEX IF NOT EXISTS recording_artists_by_recording ON recording_artists (
    recording_mbid
);


CREATE TABLE IF NOT EXISTS releases (
    mbid CHAR(36) PRIMARY KEY,
    title TEXT,
    asin VARCHAR(255),
    barcode VARCHAR(255),
    country CHAR(2),
    date TIMESTAMP,
    disambiguation TEXT,
    quality VARCHAR(255),
    status VARCHAR(255),
    status_id CHAR(36)
);
CREATE INDEX IF NOT EXISTS releases_title ON releases ( title );
CREATE INDEX IF NOT EXISTS releases_asin ON releases ( asin );
CREATE INDEX IF NOT EXISTS releases_barcode ON releases ( barcode );
CREATE INDEX IF NOT EXISTS releases_country ON releases ( country );
CREATE INDEX IF NOT EXISTS releases_date ON releases ( date );
CREATE INDEX IF NOT EXISTS releases_quality ON releases ( quality );
CREATE INDEX IF NOT EXISTS releases_status ON releases ( status );
CREATE INDEX IF NOT EXISTS releases_status_id ON releases ( status_id );


CREATE TABLE IF NOT EXISTS release_artists (
    release_mbid CHAR(36),
    artist_mbid CHAR(36),
    joinphrase VARCHAR(255),
    name TEXT,
    UNIQUE ( release_mbid, artist_mbid ),
    FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid ),
    FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid )
);
CREATE INDEX IF NOT EXISTS release_artists_by_release ON release_artists (
    release_mbid
);
CREATE INDEX IF NOT EXISTS release_artists_by_artists ON release_artists (
    artist_mbid
);
CREATE INDEX IF NOT EXISTS release_artists_name ON release_artists ( name );

--- This returns a concatenated and formatted version of all artists for a
--- release, can be used for labelling releases
DROP VIEW IF EXISTS release_artists_label;
CREATE VIEW release_artists_label AS
SELECT
    release_mbid,
    group_concat(name || joinphrase, "") AS release_artists
FROM release_artists
GROUP BY release_mbid;


CREATE TABLE IF NOT EXISTS listens (
    id INTEGER PRIMARY KEY,
    listened_at TIMESTAMP,
    user_name VARCHAR(255),
    recording_mbid CHAR(36),
    release_mbid CHAR(36),
    UNIQUE ( listened_at, user_name ),
    FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid ),
    FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid )
);
CREATE INDEX IF NOT EXISTS listens_user_name ON listens ( user_name );
CREATE INDEX IF NOT EXISTS listens_track_recording_mbid ON listens (
    recording_mbid
);
CREATE INDEX IF NOT EXISTS listens_track_release_mbid ON listens (
    release_mbid
);

DROP VIEW IF EXISTS listens_as_sequence;
CREATE VIEW listens_as_sequence AS
SELECT
    *,
    lag(release_mbid) OVER (
        ORDER BY
            listened_at DESC
    ) AS following_release_mbid,
    lag(recording_mbid) OVER (
        ORDER BY
            listened_at DESC
    ) AS following_recording_mbid,
    lag(listened_at) OVER (
        ORDER BY
            listened_at DESC
    ) AS following_listened_at
FROM
    listens
ORDER BY listened_at DESC;


CREATE TABLE IF NOT EXISTS listen_artists (
    listen_id INTEGER,
    artist_mbid CHAR(36),
    FOREIGN KEY ( listen_id ) REFERENCES listens ( id ),
    FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid )
);
CREATE INDEX IF NOT EXISTS listen_artists_listen_id ON listen_artists (
    listen_id
);
CREATE INDEX IF NOT EXISTS listen_artists_artist_mbid ON listen_artists (
    artist_mbid
);


CREATE TABLE IF NOT EXISTS release_recordings (
    recording_mbid CHAR(36),
    release_mbid CHAR(36),
    UNIQUE ( recording_mbid, release_mbid ),
    FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid ),
    FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid )
);
CREATE INDEX IF NOT EXISTS release_recordings_by_recording ON release_recordings (
    recording_mbid
);
CREATE INDEX IF NOT EXISTS release_recordings_by_release ON release_recordings (
    release_mbid
);
