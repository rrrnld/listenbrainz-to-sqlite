"""
Create initial schema
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        """
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
        )
        """,
        "DROP TABLE IF EXISTS artists",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS artists_name ON artists ( name )",
        "DROP INDEX IF EXISTS artists_name",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS artists_country ON artists ( country )",
        "DROP INDEX IF EXISTS artists_country",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS artists_gender ON artists ( gender )",
        "DROP INDEX IF EXISTS artists_gender",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS artists_gender_id ON artists ( gender_id )",
        "DROP INDEX IF EXISTS artists_gender_id",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS artists_type ON artits ( type )",
        "DROP INDEX IF EXISTS artists_type",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS artists_type_id ON artits ( type_id )",
        "DROP INDEX IF EXISTS artists_type_id",
    ),
    step(
        """
       CREATE TABLE IF NOT EXISTS recordings (
           mbid CHAR(36) PRIMARY KEY,
           title TEXT,
           disambiguation TEXT,
           first_release_date TIMESTAMP,
           length INTEGER
       )
       """,
        "DROP TABLE IF EXISTS recordings",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS recordings_title ON recrodings ( title )",
        "DROP INDEX IF EXISTS recordings_title",
    ),
    step(
        "CREATE INDEX IF NOT EXSITS recordings_first_release_date ON recordings ( first_release_date )",
        "DROP INDEX IF EXSITS recordings_first_release_date ",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS recordings_length ON recordings ( length )",
        "DROP INDEX IF EXISTS recordings_length",
    ),
    step(
        """
        -- Use this to find out all of the artists performing in a recording
        CREATE TABLE IF NOT EXISTS recording_artists (
            artist_mbid CHAR(36),
            recording_mbid CHAR(36),
            FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid ),
            FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid )
        )
        """,
        "DROP TABLE IF EXISTS recording_artits",
    ),
    step(
        "CREATE UNIQUE INDEX IF NOT EXISTS recording_artists_mapping ON recording_artists ( artist_mbid, recording_mbid )"
        "DROP INDEX IF EXISTS recording_artists_mapping",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS recording_artists_by_artist ON recording_artists ( artist_mbid )",
        "DROP INDEX IF EXISTS recording_artists_by_artist",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS recording_artists_by_recording ON recording_artists ( recording_mbid )"
        "DROP INDEX IF EXISTS recording_artists_by_recording"
    ),
    step(
        """
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
        )
        """,
        "DROP TABLE IF EXISTS releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_title ON releases ( title )",
        "DROP INDEX IF EXISTS releases_title ON releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_asin ON releases ( asin )",
        "DROP INDEX IF EXISTS releases_asin ON releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_barcode ON releases ( barcode )",
        "DROP INDEX IF EXISTS releases_barcode ON releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_country ON releases ( country )",
        "DROP INDEX IF EXISTS releases_country ON releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_date ON releases ( date )",
        "DROP INDEX IF EXISTS releases_date ON releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_quality ON releases ( quality )",
        "DROP INDEX IF EXISTS releases_quality ON releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_status ON releases ( status )",
        "DROP INDEX IF EXISTS releases_status ON releases",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS releases_status_id ON releases ( status_id )",
        "DROP INDEX IF EXISTS releases_status_id ON releases",
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS release_artists (
            release_mbid CHAR(36),
            artist_mbid CHAR(36),
            joinphrase VARCHAR(255),
            name TEXT,
            FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid ),
            FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid )
        )
        """,
        "DROP TABLE IF EXISTS release_artists",
    ),
    step(
        "CREATE UNIQUE INDEX IF NOT EXISTS release_artists_mapping ON release_artists ( release_mbid, artist_mbid )",
        "DROP INDEX IF EXISTS release_artists_mapping",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS release_artists_by_release ON release_artists ( release_mbid )",
        "DROP INDEX IF EXISTS release_artists_release_mbid",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS release_artists_by_artists ON release_artists ( artist_mbid )",
        "DROP INDEX IF EXISTS release_artists_artist_mbid",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS release_artists_name ON release_artists ( name )",
        "DROP INDEX IF EXISTS release_artists_name",
    ),
    step(
        """
        --- This returns a concatenated and formatted version of all artists for a
        --- release, can be used for labelling releases
        CREATE VIEW IF NOT EXISTS release_artists_label AS
           SELECT release_mbid, group_concat(name || joinphrase, "") release_artists
           FROM release_artists
           GROUP BY release_mbid
        """,
        "DROP VIEW IF EXISTS release_artists_label",
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS listens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listened_at TIMESTAMP,
            user_name VARCHAR(255),
            recording_mbid CHAR(36),
            release_mbid CHAR(36),
            FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid ),
            FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid )
        );
        """,
        "DROP TABLE IF EXISTS listens",
    ),
    step(
        "CREATE UNIQUE INDEX IF NOT EXISTS listens_listened_at ON listens ( listened_at )",
        "DROP INDEX IF EXISTS listens_listened_at",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS listens_user_name ON listens ( user_name )",
        "DROP INDEX IF EXISTS listens_user_name",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS listens_track_recording_mbid ON listens ( recording_mbid )",
        "DROP INDEX IF EXISTS listens_track_recording_mbid",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS listens_track_release_mbid ON listens ( release_mbid )",
        "DROP INDEX IF EXISTS listens_track_release_mbid",
    ),
    step(
        """
        CREATE VIEW IF NOT EXISTS listens_as_sequence AS
          SELECT
            *,
            LAG(release_mbid) OVER (
              ORDER BY
                listened_at DESC
            ) following_release_mbid,
            LAG(recording_mbid) OVER (
              ORDER BY
                listened_at DESC
            ) following_recording_mbid,
            LAG(listened_at) OVER (
              ORDER BY
                listened_at DESC
            ) following_listened_at
          FROM
            listens
          ORDER BY listened_at DESC
        """,
        "DROP VIEW IF EXISTS listens_as_sequence",
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS listen_artists (
            listen_id INTEGER,
            artist_mbid CHAR(36),
            FOREIGN KEY ( listen_id ) REFERENCES listens ( id ),
            FOREIGN KEY ( artist_mbid ) REFERENCES artists ( mbid )
        )
        """,
        "DROP TABLE IF EXISTS listen_artists",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS listen_artists_listen_id ON listen_artists ( listen_id )",
        "DROP INDEX IF EXISTS listen_artists_listen_id",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS listen_artists_artist_mbid ON listen_artists ( artist_mbid )",
        "DROP INDEX IF EXISTS listen_artists_artist_mbid",
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS release_recordings (
            recording_mbid CHAR(36),
            release_mbid CHAR(36),
            FOREIGN KEY ( recording_mbid ) REFERENCES recordings ( mbid ),
            FOREIGN KEY ( release_mbid ) REFERENCES releases ( mbid )
        );
        """,
        "DROP TABLE IF EXISTS release_recordings",
    ),
    step(
        "CREATE UNIQUE INDEX IF NOT EXISTS release_recordings_mapping ON release_recordings ( recording_mbid, release_mbid )",
        "DROP INDEX IF EXISTS release_recordings_mapping",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS release_recordings_by_recording ON release_recordings ( recording_mbid )",
        "DROP INDEX IF EXISTS release_recordings_by_recording",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS release_recordings_by_release ON release_recordings ( release_mbid )",
        "DROP INDEX IF EXISTS release_recordings_by_release",
    ),
]
