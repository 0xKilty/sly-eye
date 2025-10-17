import feedparser

def pypi_source():
    url = "https://pypi.org/rss/updates.xml"
    feed = feedparser.parse(url)
    return feed.entries
