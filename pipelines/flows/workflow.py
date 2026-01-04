import time

from prefect import task, flow
from sentinel.news_ingestion import (
    init_db,
    get_random_query,
    fetch_rss_feed,
    scrape_article,
    save_article,
)
from sentinel.news_scoring import (
    get_unscored_news,
    score_news,
    update_news_score,
)

system_prompt = open("prompts/system_prompt.md", "r").read()
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


@task
def ingest_news(search_query: str, num_articles: int = 3):
    init_db(directory="data/database.db")
    refined_query = search_query.replace(" ", "+")
    search_url = f"https://www.bing.com/news/search?q={refined_query}&format=rss"
    feed = fetch_rss_feed(search_url)
    valid_articles = 0
    for entry in feed.entries:
        content = scrape_article(entry.link, HEADERS)
        print(entry.title)
        if content:
            print(f"Title: {entry.title}")
            print(f"Link: {entry.link}")
            print(f"Published: {entry.published}")
            print(f"Text: {content}")
            print("-" * 50)
            time.sleep(0.5)
            article_saved = save_article(db_directory="data/database.db", entry=entry, text=content)
            if not article_saved:
                continue
            valid_articles += 1
            if valid_articles == num_articles:
                print(len(feed.entries), "articles fetched.")
                print(num_articles, "articles ingested.")
                break
    
    if valid_articles < num_articles:
        print("Not enough articles found. Try a different search query.")
        return None
    return True

@task
def analyze_news():
    news = get_unscored_news(db_directory="data/database.db")
    for row in news:
        news_title = row[1]
        news_content = row[2]
        news_score = score_news(news_title, news_content, "openai/gpt-oss-120b", system_message=system_prompt)
        update_news_score(db_directory="data/database.db", news_title=news_title, news_score=news_score)

@flow
def news_pipeline():
    try:
        retries = 0
        max_retries = 3
        while retries < max_retries:
            query = get_random_query()
            print(f"Search Query: {query}")
            articles_ingested = ingest_news(search_query=query, num_articles=5)
            if articles_ingested:
                print("Scoring News...")
                analyze_news()
                break
            retries += 1
        print("")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    news_pipeline()