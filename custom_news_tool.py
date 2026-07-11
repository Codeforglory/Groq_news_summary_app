from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
from typing import Type

import requests

class NewsToolInput(BaseModel):
    """Input schema for the FetchNewsTool."""

    query: str = Field(..., description="The topic or keywords to search for in the news articles.")

class FetchNewsTool(BaseTool):
    name : str = "Fetch Latest News"
    description : str = "Mandatory tool for fetching real-time, recent news articles or updates on a specific topic using the Currents API."
    args_schema: Type[NewsToolInput] = NewsToolInput

    def _run(self, query: str = "Latest news on AI and technologies") -> str:
        """Fetch the latest news articles based on the provided query."""
        api_key = os.getenv("NEWS_API_KEY")
        url = "https://api.currentsapi.services/v1/search"
        search_params = {
            "keywords": query,
            "language": "en",
            "page_number": 1,
            "page_size": 5,
            
        }

        try:

            response = requests.get(url, headers = {"Authorization": api_key},params=search_params,timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("news", [])
                
                formatted_news = ""
                for idx, art in enumerate(articles[:5]):
                    formatted_news += f"Title: {art.get('title')}\nSummary: {art.get('description')}\nPublish Date: {art.get('published')}\n\n"
                return formatted_news if formatted_news else "No articles found."
            return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Error executing tool: {str(e)}"
