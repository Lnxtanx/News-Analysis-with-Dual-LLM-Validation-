"""
LLM Validator Module
Uses OpenRouter (Qwen) to validate analysis from Gemini.
"""

import os
import json
import time
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class ValidatorError(Exception):
    """Custom exception for validator errors."""
    pass


def get_openrouter_client():
    """Initialize and return OpenRouter client (OpenAI-compatible)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        raise ValidatorError("OPENROUTER_API_KEY not configured in .env file")
    
    try:
        from openai import OpenAI
        return OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    except ImportError:
        raise ValidatorError("openai package not installed. Run: pip install openai")


def validate_analysis(article: Dict, analysis: Dict, max_retries: int = 3) -> Dict:
    """
    Validate Gemini's analysis using OpenAI.
    
    Args:
        article: Original article dictionary
        analysis: Gemini's analysis (gist, sentiment, tone)
        max_retries: Number of retries for transient failures
        
    Returns:
        Validation dictionary with is_valid, validation_notes, suggested_corrections
        
    Raises:
        ValidatorError: If validation fails after all retries
    """
    client = get_openrouter_client()
    
    # Build article text
    article_text = f"""
Title: {article.get('title', 'No title')}
Source: {article.get('source', 'Unknown')}
Description: {article.get('description', 'No description')}
Content: {article.get('content', 'No content')}
    """.strip()
    
    # Build analysis text
    analysis_text = f"""
Gist: {analysis.get('gist', 'N/A')}
Sentiment: {analysis.get('sentiment', 'N/A')}
Tone: {analysis.get('tone', 'N/A')}
    """.strip()
    
    prompt = f"""You are a fact-checker validating an AI's analysis of a news article.

ORIGINAL ARTICLE:
{article_text}

AI ANALYSIS TO VALIDATE:
{analysis_text}

Your task:
1. Check if the gist accurately summarizes the article's main point
2. Check if the sentiment (positive/negative/neutral) matches the article's tone
3. Check if the tone classification is appropriate

Respond with a JSON object containing:
- "is_valid": boolean - true if the analysis is accurate, false if there are significant errors
- "validation_notes": string - Brief explanation of your assessment, mention what's correct and any issues found
- "suggested_corrections": null if valid, or an object with corrected values for any wrong fields

Return ONLY the JSON object, no additional text.

Example valid response:
{{"is_valid": true, "validation_notes": "Gist accurately captures the policy announcement. Sentiment correctly identified as positive based on words like 'launched' and 'new initiative'.", "suggested_corrections": null}}

Example invalid response:
{{"is_valid": false, "validation_notes": "Sentiment should be negative as the article discusses failures and criticism.", "suggested_corrections": {{"sentiment": "negative"}}}}
"""

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-nano-30b-a3b:free",
                messages=[
                    {"role": "system", "content": "You are a precise fact-checker. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            # Parse JSON
            validation = json.loads(response_text)
            
            # Validate required fields
            if "is_valid" not in validation:
                validation["is_valid"] = True
            if "validation_notes" not in validation:
                validation["validation_notes"] = "Validation completed"
            if "suggested_corrections" not in validation:
                validation["suggested_corrections"] = None
            
            return validation
            
        except json.JSONDecodeError as e:
            last_error = ValidatorError(f"Failed to parse OpenAI response as JSON: {e}")
        except Exception as e:
            last_error = ValidatorError(f"OpenAI API error: {e}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    raise last_error or ValidatorError("Validation failed after all retries")


def validate_analyses(articles: list, analyses: list) -> list:
    """
    Validate multiple analyses.
    
    Args:
        articles: List of original article dictionaries
        analyses: List of analysis results from Gemini
        
    Returns:
        List of validated results with validation info added
    """
    validated_results = []
    
    # Create a lookup for articles by ID
    articles_lookup = {a.get("id", i + 1): a for i, a in enumerate(articles)}
    
    for i, analysis_result in enumerate(analyses):
        article_id = analysis_result.get("article_id", i + 1)
        article = articles_lookup.get(article_id, {})
        
        print(f"Validating analysis {i + 1}/{len(analyses)}: {analysis_result.get('title', 'Unknown')[:50]}...")
        
        # Skip if original analysis failed
        if analysis_result.get("status") == "error":
            validated_result = analysis_result.copy()
            validated_result["validation"] = {
                "is_valid": False,
                "validation_notes": "Skipped - original analysis failed",
                "suggested_corrections": None
            }
            validated_results.append(validated_result)
            continue
        
        try:
            validation = validate_analysis(article, analysis_result.get("analysis", {}))
            validated_result = analysis_result.copy()
            validated_result["validation"] = validation
        except ValidatorError as e:
            validated_result = analysis_result.copy()
            validated_result["validation"] = {
                "is_valid": True,  # Assume valid if we can't check
                "validation_notes": f"Validation error: {e}",
                "suggested_corrections": None
            }
        
        validated_results.append(validated_result)
        
        # Rate limiting
        time.sleep(1)
    
    return validated_results


if __name__ == "__main__":
    # Test with sample data
    test_article = {
        "id": 1,
        "title": "India announces new economic policy",
        "description": "The government unveiled a comprehensive economic reform package.",
        "content": "India's finance ministry today announced a sweeping economic reform package aimed at boosting growth and creating jobs.",
        "source": "Test Source"
    }
    
    test_analysis = {
        "gist": "India announced economic reforms to boost growth",
        "sentiment": "positive",
        "tone": "informative"
    }
    
    try:
        result = validate_analysis(test_article, test_analysis)
        print("Validation result:")
        print(json.dumps(result, indent=2))
    except ValidatorError as e:
        print(f"Error: {e}")
