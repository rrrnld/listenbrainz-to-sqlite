import click
import requests
from tqdm import tqdm
import time
import datetime
import sqlite3
from .db import setup_database

# TODO: Use REPLACE statement where applicable
def upsert_artist(db, mbid, name):
    artist = db.execute("SELECT * FROM artists WHERE mbid = ?", [mbid])
    if artist.fetchone():
        query = """
           UPDATE artists
           SET name = :name
           WHERE mbid= :mbid;
        """
    else:
        query = """
           INSERT INTO artists VALUES ( :mbid, :name );
        """
    db.execute(query, {"mbid": mbid, "name": name})


def upsert_recording(db, mbid, name):
    recording = db.execute("SELECT * FROM recordings WHERE mbid = ?", [mbid])
    if recording.fetchone():
        query = """
           UPDATE recordings
           SET name = :name
           WHERE mbid= :mbid;
        """
    else:
        query = """
           INSERT INTO recordings VALUES ( :mbid, :name )
        """
    db.execute(query, {"mbid": mbid, "name": name})


def upsert_artists_for_recording(db, artist_mbids, recording_mbid):
    for artist_mbid in artist_mbids:
        artist_on_recording = db.execute(
            """
            SELECT * FROM artists_for_recordings
            WHERE artist_mbid = ? AND recording_mbid = ?;
        """,
            [artist_mbid, recording_mbid],
        )
        if not artist_on_recording.fetchone():
            db.execute(
                "INSERT INTO artists_for_recordings VALUES ( ?, ? )",
                [artist_mbid, recording_mbid],
            )


def upsert_release_with_recording(db, release_mbid, name, recording_mbid):
    release = db.execute("SELECT * FROM releases WHERE mbid = ?;", [release_mbid])
    if not release.fetchone():
        db.execute("INSERT INTO releases VALUES ( ?, ? )", [release_mbid, name])

    recording_on_release = db.execute(
        """
        SELECT * FROM recordings_on_releases WHERE recording_mbid = ? AND release_mbid = ?;
    """,
        [recording_mbid, release_mbid],
    )
    if not recording_on_release.fetchone():
        db.execute(
            """
            INSERT INTO recordings_on_releases VALUES ( ?, ? );
        """,
            [recording_mbid, release_mbid],
        )


def upsert_listen(db, listen):
    imported_listen = db.execute(
        "SELECT * FROM listens WHERE listened_at = ?", [listen["listened_at"]]
    )
    if not imported_listen.fetchone():
        mbids = listen["track_metadata"]["mbid_mapping"]
        cur = db.execute(
            """
            INSERT INTO listens VALUES ( ?, ?, ?, ? )
        """,
            [
                listen["listened_at"],
                listen["user_name"],
                mbids["recording_mbid"],
                mbids["release_mbid"],
            ],
        )

        db.executemany(
            """
            INSERT INTO listen_artists VALUES ( ?, ? )
        """,
            [(cur.lastrowid, artist_mbid) for artist_mbid in mbids["artist_mbids"]],
        )


@click.command(
    help="Imports listenbrainz history of a single user with associated artists, releases, and recordings."
)
@click.option(
    "--user",
    required=True,
    help="The Listenbrainz username form which to import listens",
    type=str,
)
@click.option(
    "--max-results", help="Limit the maximum amount of fetched results.", type=int
)
@click.option(
    "--since",
    default=datetime.datetime(1970, 1, 1),
    help="Consider only listens more recent than this argument",
    type=click.DateTime(),
)
@click.option(
    "--until",
    default=datetime.datetime.now(),
    help="Consider only listens older than this argument",
    type=click.DateTime(),
)
def import_listens(user, max_results, since, until):
    setup_database("listenbrainz.db")
    with sqlite3.connect("listenbrainz.db") as con, tqdm(
        desc=f'Starting to fetch {max_results or "all"} listens from the listenbrainz API',
        unit=" listens",
    ) as pbar:
        con.isolation_level = None
        cur = con.cursor()

        num_results = 0

        min_ts = int(time.mktime(since.timetuple()))
        max_ts = int(time.mktime(until.timetuple()))

        while True:
            req = requests.get(
                f"https://api.listenbrainz.org/1/user/{user}/listens",
                {"min_ts": min_ts, "max_ts": max_ts},
            )
            if not req.ok:
                print("Something is wrong! aborting")
                print(f'{req.status_code}: {req.json()["error"]}')
                break

            body = req.json()["payload"]

            # insert all listens, artists, recordings, etc.
            for listen in body["listens"]:
                if not listen["track_metadata"].get("mbid_mapping"):
                    print(
                        "Skipping listen without mbid info:",
                        listen["track_metadata"].get("artist_name", ""),
                        listen["track_metadata"].get("track_name", ""),
                    )
                    continue

                # start with artists
                meta = listen["track_metadata"]
                for mbid in meta["mbid_mapping"]["artist_mbids"]:
                    # FIXME: Handle multiple artists correctly, possibly just fetch the name by mbid
                    upsert_artist(cur, mbid, meta["artist_name"])

                upsert_recording(
                    cur, meta["mbid_mapping"]["recording_mbid"], meta["track_name"]
                )
                upsert_artists_for_recording(
                    cur,
                    meta["mbid_mapping"]["artist_mbids"],
                    meta["mbid_mapping"]["recording_mbid"],
                )
                upsert_release_with_recording(
                    cur,
                    meta["mbid_mapping"]["release_mbid"],
                    meta["track_name"],
                    meta["mbid_mapping"]["recording_mbid"],
                )

                # FIXME: It would be nice to be more consistent here and not just pass the entire listen :)
                upsert_listen(cur, listen)

            num_results += body["count"]
            pbar.update(body["count"])

            min_ts = body["latest_listen_ts"]
            if (max_results and num_results >= max_results) or not body["listens"]:
                break

            con.commit()
            time.sleep(0.5)


if __name__ == "__main__":
    import_listens(auto_envar_prefix="LISTENBRAINZ_IMPORT")
