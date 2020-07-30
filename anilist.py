from anime import Anime


q = "query($userId:Int,$userName:String,$type:MediaType=ANIME){MediaListCollection(userId:$userId,userName:$userName,type:$type){lists{name entries{media{title{romaji english}startDate{year}}}}}}"

async def anime_list(session, username):
    async with session.post("https://graphql.anilist.co", json={"query": q, "variables": {"userName": username}}) as resp:
        d = await resp.json()
    o = []
    for l in d["data"]["MediaListCollection"]["lists"]:
        if l["name"] == "Completed":
            for entry in l["entries"]:
                o.append(Anime(entry["media"]["title"]["romaji"], entry["media"]["startDate"]["year"], entry["media"]["title"]["english"]))
    return o
