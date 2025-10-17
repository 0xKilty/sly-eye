import feedparser

url = "https://pypi.org/rss/updates.xml"
feed = feedparser.parse(url)
for entry in feed.entries:
    # each entry has fields like title, link, updated, etc.
    print(entry.updated, entry.title, entry.link)
