import sqlite3 as sql
import time
import random
import feedparser
import requests
import trafilatura

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
SEARCH_QUERIES = [
    "semiconductor supply chain",
    "TSMC manufacturing delays",
    "Nvidia GPU shortage",
    "Silicon wafer prices",
    "ASML lithography export controls",
    "Micron Technology logistics",
    "Rare earth metal exports China",
    "Samsung Electronics foundry",
    "Intel fabrication plant news",
    "Automotive chip shortage updates"
]


def init_db(directory="database.db"):
    with sql.connect(directory) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                title TEXT, 
                link TEXT, 
                published TEXT, 
                text TEXT, 
                relevance INTEGER
            )
        """)


def get_random_query():
    return random.choice(SEARCH_QUERIES)


def fetch_rss_feed(feed_url):
    news_feed = feedparser.parse(feed_url)
    return news_feed


def scrape_article(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    content = response.text
    return trafilatura.extract(content)


def save_article(db_directory, entry, text):
    with sql.connect(db_directory) as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO news (title, link, published, text)
            VALUES (?, ?, ?, ?)
            """,
            (entry.title, entry.link, entry.published, text),
        )
        con.commit()
        return cur.rowcount == 1


if __name__ == "__main__":
    init_db("data/database.db")
    query = get_random_query()
    print(f"Query: {query}")
    feed = fetch_rss_feed(
        feed_url=f"https://www.bing.com/news/search?q={query}&format=rss"
    )

    for entry in feed.entries[:3]:
        print(f"Title: {entry.title}")
        print(f"Link: {entry.link}")
        print(f"Published: {entry.published}")
        text = scrape_article(entry.link, HEADERS)
        if text:
            print(f"Text: {text}")
            save_article(db_directory="data/database.db", entry=entry, text=text)
        print("-" * 50)
        time.sleep(0.5)
