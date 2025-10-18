import feedparser
import requests
import tempfile

def pypi_source():
    url = "https://pypi.org/rss/updates.xml"
    feed = feedparser.parse(url)
    return feed.entries

def download_pypi_package(package):
    info = package.split("/")[-3:-1]
    package, version = info[0], info[1]

    meta = requests.get(f"https://pypi.org/pypi/{package}/{version}/json").json()

    wheel = next(
        (url for url in meta["urls"] if url["packagetype"] == "bdist_wheel"),
        None
    )

    if not wheel:
        raise RuntimeError(f"No wheel (.whl) found for {package}=={version}")

    url = wheel["url"]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".whl")
    tmp.write(requests.get(url).content)
    tmp.close()

    return tmp.name

