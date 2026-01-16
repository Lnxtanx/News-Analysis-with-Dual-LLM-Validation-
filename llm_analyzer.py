"""
LLM Analyzer Module
Uses OpenAI to analyze news articles for gist, sentiment, and tone.
"""

import os
import json
import time
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class AnalyzerError(Exception):
    """Custom exception for analyzer errors."""
    pass


def get_openai_client():
    """Initialize and return OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        raise AnalyzerError("OPENAI_API_KEY not configured in .env file")
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        raise AnalyzerError("openai package not installed. Run: pip install openai")


def analyze_article(article: Dict, max_retries: int = 3) -> Dict:
    """
    Analyze a single article using OpenAI.
    
    Args:
        article: Article dictionary with title, description, content
        max_retries: Number of retries for transient failures
        
    Returns:
        Analysis dictionary with gist, sentiment, tone
        
    Raises:
        AnalyzerError: If analysis fails after all retries
    """
    client = get_openai_client()
    
    # Build article text for analysis
    article_text = f"""
Title: {article.get('title', 'No title')}
Source: {article.get('source', 'Unknown')}
Description: {article.get('description', 'No description')}
Content: {article.get('content', 'No content')}
    """.strip()
    
    prompt = f"""Analyze the following news article and provide your analysis in JSON format.

Article:
{article_text}

Provide your analysis as a valid JSON object with exactly these fields:
- "gist": A 1-2 sentence summary of the main point of the news
- "sentiment": One of "positive", "negative", or "neutral"
- "tone": One of "urgent", "analytical", "satirical", "balanced", "critical", "optimistic", "pessimistic", or "informative"

Return ONLY the JSON object, no additional text or markdown formatting.

Example format:
{{"gist": "Summary here", "sentiment": "neutral", "tone": "analytical"}}
"""

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a news analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first and last lines (```json and ```)
                response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            # Parse JSON
            analysis = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["gist", "sentiment", "tone"]
            for field in required_fields:
                if field not in analysis:
                    raise AnalyzerError(f"Missing required field: {field}")
            
            # Normalize sentiment
            sentiment = analysis["sentiment"].lower().strip()
            if sentiment not in ["positive", "negative", "neutral"]:
                sentiment = "neutral"  # Default to neutral if unclear
            analysis["sentiment"] = sentiment
            
            # Normalize tone
            valid_tones = ["urgent", "analytical", "satirical", "balanced", 
                         "critical", "optimistic", "pessimistic", "informative"]
            tone = analysis["tone"].lower().strip()
            if tone not in valid_tones:
                tone = "informative"  # Default
            analysis["tone"] = tone
            
            return analysis
            
        except json.JSONDecodeError as e:
            last_error = AnalyzerError(f"Failed to parse OpenAI response as JSON: {e}")
        except Exception as e:
            last_error = AnalyzerError(f"OpenAI API error: {e}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    raise last_error or AnalyzerError("Analysis failed after all retries")


def analyze_articles(articles: list) -> list:
    """
    Analyze multiple articles.
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        List of analysis results with article info and analysis
    """
    results = []
    
    for i, article in enumerate(articles):
        print(f"Analyzing article {i + 1}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
        
        try:
            analysis = analyze_article(article)
            result = {
                "article_id": article.get("id", i + 1),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source": article.get("source", "Unknown"),
                "analysis": analysis,
                "status": "success"
            }
        except AnalyzerError as e:
            result = {
                "article_id": article.get("id", i + 1),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source": article.get("source", "Unknown"),
                "analysis": {
                    "gist": "Analysis failed",
                    "sentiment": "neutral",
                    "tone": "informative"
                },
                "status": "error",
                "error": str(e)
            }
        
        results.append(result)
        
        # Rate limiting - avoid hitting API limits
        time.sleep(1)
    
    return results


if __name__ == "__main__":
    # Test with a sample article
    test_article = {
        "id": 1,
        "title": "India announces new economic policy",
        "description": "The government unveiled a comprehensive economic reform package.",
        "content": "India's finance ministry today announced a sweeping economic reform package aimed at boosting growth and creating jobs. The policy includes tax incentives for businesses and infrastructure investments.",
        "source": "Test Source",
        "url": "https://example.com"
    }
    
    try:
        result = analyze_article(test_article)
        print("Analysis result:")
        print(json.dumps(result, indent=2))
    except AnalyzerError as e:
        print(f"Error: {e}")
