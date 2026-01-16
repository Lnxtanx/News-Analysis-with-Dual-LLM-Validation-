"""
News Fetcher Module
Fetches news articles from NewsAPI about Indian politics.
"""

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class NewsFetcherError(Exception):
    """Custom exception for news fetching errors."""
    pass


def fetch_news(
    query: str = "India politics OR India government",
    num_articles: int = 15,
    language: str = "en"
) -> List[Dict]:
    """
    Fetch news articles from NewsAPI.
    
    Args:
        query: Search query for news articles
        num_articles: Number of articles to fetch (10-15 recommended)
        language: Language code for articles
        
    Returns:
        List of article dictionaries with title, description, content, url, source
        
    Raises:
        NewsFetcherError: If API call fails or returns no articles
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key or api_key == "your_newsapi_key_here":
        raise NewsFetcherError("NEWSAPI_KEY not configured in .env file")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "pageSize": num_articles,
        "sortBy": "publishedAt",
        "apiKey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise NewsFetcherError("NewsAPI request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise NewsFetcherError("Failed to connect to NewsAPI. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise NewsFetcherError("Invalid NewsAPI key. Please check your API key.")
        elif response.status_code == 429:
            raise NewsFetcherError("NewsAPI rate limit exceeded. Please wait and try again.")
        else:
            raise NewsFetcherError(f"NewsAPI HTTP error: {e}")
    
    data = response.json()
    
    if data.get("status") != "ok":
        error_msg = data.get("message", "Unknown error from NewsAPI")
        raise NewsFetcherError(f"NewsAPI error: {error_msg}")
    
    articles = data.get("articles", [])
    
    if not articles:
        raise NewsFetcherError("No articles found for the given query.")
    
    # Clean and structure the articles
    cleaned_articles = []
    for i, article in enumerate(articles):
        # Skip articles with missing essential content
        title = article.get("title", "").strip()
        if not title or title == "[Removed]":
            continue
            
        content = article.get("content") or article.get("description") or ""
        content = content.strip()
        
        # Skip if no meaningful content
        if not content or len(content) < 50:
            continue
        
        cleaned_article = {
            "id": i + 1,
            "title": title,
            "description": (article.get("description") or "").strip(),
            "content": content,
            "url": article.get("url", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "author": article.get("author") or "Unknown"
        }
        cleaned_articles.append(cleaned_article)
    
    if not cleaned_articles:
        raise NewsFetcherError("All fetched articles had invalid or missing content.")
    
    return cleaned_articles


def get_article_text(article: Dict) -> str:
    """
    Get the full text content of an article for analysis.
    
    Args:
        article: Article dictionary
        
    Returns:
        Combined title, description, and content as a single string
    """
    parts = []
    if article.get("title"):
        parts.append(f"Title: {article['title']}")
    if article.get("description"):
        parts.append(f"Description: {article['description']}")
    if article.get("content"):
        parts.append(f"Content: {article['content']}")
    
    return "\n".join(parts)


if __name__ == "__main__":
    # Test the fetcher
    try:
        articles = fetch_news(num_articles=5)
        print(f"Fetched {len(articles)} articles:")
        for article in articles:
            print(f"  - {article['title'][:60]}...")
    except NewsFetcherError as e:
        print(f"Error: {e}")
