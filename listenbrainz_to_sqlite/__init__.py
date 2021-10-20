import click
import requests
from tqdm import tqdm
import time
import datetime
import sqlite3
from yoyo import read_migrations, get_backend


def datestr_to_timestamp(datestr: str):
    try:
        return datetime.datetime(*map(int, datestr.split("-")))  # type: ignore
    except:
        return None


def snake_case(d: dict):
    return {k.replace("-", "_"): v for (k, v) in d.items()}


def ensure_keys(d: dict, ks):
    return {k: d.get(k) for k in ks}


def get_manual_or_mapped(listen, mbid_type: str):
    meta = listen["track_metadata"]
    manually_submitted = meta.get("additional_info", {}).get(mbid_type)
    if manually_submitted:
        return manually_submitted
    else:
        return meta.get("mbid_mapping", {}).get(mbid_type)


def upsert_recording(db, mbid):
    recording = db.execute("SELECT * FROM recordings WHERE mbid = ?", [mbid])
    if not recording.fetchone():
        time.sleep(1)
        mb_recording = requests.get(
            f"https://musicbrainz.org/ws/2/recording/{mbid}?fmt=json"
        ).json()
        mb_recording["first-release-date"] = datestr_to_timestamp(
            mb_recording.get("first-release-date")
        )

        # sometimes mbids change and musicbrainz silently redirects; we need to
        # make sure we can still detect existing entries
        mb_recording["id"] = mbid
        db.execute(
            "INSERT INTO recordings VALUES ( :id, :title, :disambiguation, :first_release_date, :length )",
            ensure_keys(
                snake_case(mb_recording),
                ["id", "title", "disambiguation", "first_release_date", "length"],
            ),
        )


def upsert_artist(db, artist_mbid):
    artist = db.execute("SELECT * FROM artists WHERE mbid = ?", [artist_mbid])
    if not artist.fetchone():
        time.sleep(1)  # be nice
        mb_artist = requests.get(
            f"https://musicbrainz.org/ws/2/artist/{artist_mbid}?fmt=json"
        ).json()
        mb_artist["id"] = artist_mbid
        try:
            db.execute(
                """
                INSERT INTO artists VALUES (
                :id, :name, :sort_name, :country,
                :disambiguation, :gender, :gender_id,
                :type, :type_id
                )
                """,
                ensure_keys(
                    snake_case(mb_artist),
                    [
                        "id",
                        "name",
                        "sort_name",
                        "country",
                        "disambiguation",
                        "gender",
                        "gender_id",
                        "type",
                        "type_id",
                    ],
                ),
            )
        except InterruptedError:
            pass
        except:
            tqdm.wrte(f"artist response: {mb_artist}")
            raise


def upsert_recording_artists(db, artist_mbids, recording_mbid):
    for artist_mbid in artist_mbids:
        upsert_artist(db, artist_mbid)

        artist_on_recording = db.execute(
            """
            SELECT * FROM recording_artists
            WHERE artist_mbid = ? AND recording_mbid = ?;
            """,
            [artist_mbid, recording_mbid],
        )
        if not artist_on_recording.fetchone():
            db.execute(
                "INSERT INTO recording_artists VALUES ( ?, ? )",
                [artist_mbid, recording_mbid],
            )


def upsert_release_with_recording(db, release_mbid, recording_mbid):
    release = db.execute("SELECT * FROM releases WHERE mbid = ?;", [release_mbid])
    if not release.fetchone():
        time.sleep(1)
        mb_release = requests.get(
            f"https://musicbrainz.org/ws/2/release/{release_mbid}?fmt=json&inc=artists"
        ).json()
        mb_release["id"] = release_mbid
        mb_release["date"] = datestr_to_timestamp(mb_release.get("date"))
        try:
            db.execute(
                """
                INSERT INTO releases VALUES (
                :id, :title, :asin, :barcode, :country, :date,
                :disambiguation, :quality, :status, :status_id
                )
                """,
                ensure_keys(
                    snake_case(mb_release),
                    [
                        "id",
                        "title",
                        "asin",
                        "barcode",
                        "country",
                        "date",
                        "disambiguation",
                        "quality",
                        "status",
                        "status_id",
                    ],
                ),
            )
        except InterruptedError:
            pass
        except:
            tqdm.write(f"release response: {mb_release}")
            raise

        try:
            for artist_credit in mb_release["artist-credit"]:
                # TODO: This is not ideal becaue
                # a) we're using musicbrainz mbids and might have the previous problem of mbid drift
                # b) we're refetching information we already have due to how upsert_artist is written
                upsert_artist(db, artist_credit["artist"]["id"])
                release_artist = db.execute(
                    "SELECT * FROM release_artists WHERE release_mbid = ? AND artist_mbid = ?",
                    [mb_release["id"], artist_credit["artist"]["id"]],
                )
                if not release_artist.fetchone():
                    db.execute(
                        "INSERT INTO release_artists VALUES ( :release_mbid, :artist_mbid, :joinphrase, :name )",
                        {
                            "release_mbid": mb_release["id"],
                            "artist_mbid": artist_credit["artist"]["id"],
                            "joinphrase": artist_credit["joinphrase"],
                            "name": artist_credit["name"],
                        },
                    )
        except:
            tqdm.write(f"response: {mb_release}")
            raise

    release_recording = db.execute(
        """
        SELECT * FROM release_recordings WHERE recording_mbid = ? AND release_mbid = ?;
        """,
        [recording_mbid, release_mbid],
    )
    if not release_recording.fetchone():
        db.execute(
            """
            INSERT INTO release_recordings VALUES ( ?, ? );
            """,
            [recording_mbid, release_mbid],
        )


def upsert_listen(db, listen):
    listened_at = datetime.datetime.fromtimestamp(listen["listened_at"])
    imported_listen = db.execute(
        "SELECT * FROM listens WHERE listened_at = ?", [listened_at]
    )
    if not imported_listen.fetchone():
        meta = listen["track_metadata"]
        cur = db.execute(
            "INSERT INTO listens VALUES ( NULL, ?, ?, ?, ? )",
            [
                listened_at,
                listen["user_name"],
                get_manual_or_mapped(listen, "recording_mbid"),
                get_manual_or_mapped(listen, "release_mbid"),
            ],
        )

        db.executemany(
            "INSERT INTO listen_artists VALUES ( ?, ? )",
            [
                (cur.lastrowid, artist_mbid)
                for artist_mbid in get_manual_or_mapped(listen, "artist_mbids")
            ],
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
    default=datetime.datetime(1970, 1, 1, 1, 0),
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
    backend = get_backend("sqlite:///listenbrainz.db")
    migrations = read_migrations("./migrations")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    with sqlite3.connect("listenbrainz.db") as con, tqdm(
        desc=f"Importing listens from the listenbrainz API", unit="listen(s)"
    ) as pbar:
        con.isolation_level = None
        cur = con.cursor()

        num_results = 0

        min_ts = int(time.mktime(since.timetuple()))
        max_ts = int(time.mktime(until.timetuple()))

        while True:
            max_dt = datetime.datetime.fromtimestamp(max_ts)
            pbar.set_description_str(
                f'Importing @ {max_dt.strftime("%Y-%m-%d %H:%M:%S")}'
            )
            req = requests.get(
                f"https://api.listenbrainz.org/1/user/{user}/listens",
                {"max_ts": max_ts, "count": 100},
            )
            if not req.ok:
                tqdm.write(f"Something went wrong while requesting {req.url}, aborting")
                tqdm.write(f'{req.status_code}: {req.json()["error"]}')
                break

            body = req.json()["payload"]

            # insert all listens, artists, recordings, etc.
            for listen in body["listens"]:
                pbar.update()

                artist_mbids = get_manual_or_mapped(listen, "artist_mbids")
                recording_mbid = get_manual_or_mapped(listen, "recording_mbid")
                release_mbid = get_manual_or_mapped(listen, "release_mbid")

                if not (artist_mbids and recording_mbid and release_mbid):
                    meta = listen["track_metadata"]
                    artist_name = meta.get("artist_name", "")
                    track_name = meta.get("track_name", "")
                    tqdm.write(
                        f"Skipping listen without mbid info: {artist_name} - {track_name}",
                    )
                    continue

                try:
                    upsert_recording(cur, recording_mbid)
                    upsert_recording_artists(
                        cur,
                        artist_mbids,
                        recording_mbid,
                    )
                    upsert_release_with_recording(
                        cur,
                        release_mbid,
                        recording_mbid,
                    )
                    upsert_listen(cur, listen)
                except:
                    tqdm.write(
                        f"Something went wrong while requesting {req.url}, aborting"
                    )
                    tqdm.write(f"listen: {listen}")
                    raise

            try:
                max_ts = min([l["listened_at"] for l in body.get("listens", [])])
            except ValueError:
                # empty list for listens
                break

            num_results += body["count"]
            if (max_results and num_results >= max_results) or max_ts <= min_ts:
                break

            time.sleep(1)


if __name__ == "__main__":
    import_listens(auto_envar_prefix="LISTENBRAINZ_IMPORT")
