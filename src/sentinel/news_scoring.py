import json
import os
import sqlite3 as sql
from enum import IntEnum

import groq
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
system_prompt = open("prompts/system_prompt.md", "r").read()


class RelevanceScore(IntEnum):
    NOISE = 0
    LOW = 20
    MEDIUM = 50
    HIGH = 80
    CRITICAL = 100


# 2. Define the exact structure you want
class NewsAnalysis(BaseModel):
    reasoning: str = Field(
        ...,
        description="Concise analysis of why this news impacts the physical supply chain.",
    )
    entities: list[str] = Field(
        ..., description="List of key companies, materials, or locations involved."
    )
    score: RelevanceScore = Field(..., description="The operational risk score.")


def get_unscored_news(db_directory):
    with sql.connect(db_directory) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM news WHERE relevance IS NULL")
        result = cur.fetchall()
        return result


def get_all_news(db_directory):
    with sql.connect(db_directory) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM news")
        result = cur.fetchall()
        return result


def score_news(news_title: str, news_content: str, model: str, system_message: str):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_message,
                },
                {
                    "role": "user",
                    "content": f"Title: {news_title}, Content: {news_content}",
                },
            ],
            temperature=0.1,
            max_completion_tokens=2000,
            top_p=0.1,
            reasoning_effort="medium",
            stream=False,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "NewsAnalysis",
                    "schema": NewsAnalysis.model_json_schema(),
                },
            },
            stop=None,
        )
        response_json = NewsAnalysis.model_validate(
            json.loads(response.choices[0].message.content)
        )
        print(f"Title: {news_title}")
        print(f"Reasoning: {response_json.reasoning}")
        print(f"Entities: {response_json.entities}")
        print(f"Score: {response_json.score}")

        return int(response_json.score)
    except ValueError as e:
        print("Error:", e)
        return 0


def update_news_score(db_directory, news_title: str, news_score: int):
    with sql.connect(db_directory) as con:
        cur = con.cursor()
        cur.execute(
            "UPDATE news SET relevance = ? WHERE title = ?", (news_score, news_title)
        )
        con.commit()
        print(f"Title: {news_title}, updated to DB with score: {news_score}")


if __name__ == "__main__":
    db_directory = "data/database.db"
    news = get_unscored_news(db_directory)
    for row in news:
        news_title = row[1]
        news_content = row[2]
        print(news_title)
        news_score = score_news(
            news_title,
            news_content,
            "openai/gpt-oss-120b",
            system_message=system_prompt,
        )
        update_news_score(db_directory, news_title, news_score)
