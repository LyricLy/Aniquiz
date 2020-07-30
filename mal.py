from jikanpy import AioJikan

from anime import Anime


jikan = None

async def anime_list(session, username):
    global jikan
    if jikan is None:
        jikan = AioJikan(session=session)
    d = await jikan.user(username, "animelist", "completed")
    return [Anime(x["title"], int(x["start_date"].split("-")[0])) for x in d["anime"]]
