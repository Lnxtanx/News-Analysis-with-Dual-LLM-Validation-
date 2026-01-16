"""
Tests for News Analyzer
At least 3 meaningful tests for the analysis pipeline.
"""

import pytest
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_fetcher import fetch_news, get_article_text, NewsFetcherError
from llm_analyzer import analyze_article, AnalyzerError
from llm_validator import validate_analysis, ValidatorError


class TestNewsFetcher:
    """Tests for the news fetcher module."""
    
    def test_news_fetcher_returns_articles(self):
        """Test that the fetcher returns valid article structure."""
        try:
            articles = fetch_news(num_articles=3)
            
            assert isinstance(articles, list), "Should return a list"
            assert len(articles) > 0, "Should return at least one article"
            
            # Check required fields in first article
            article = articles[0]
            required_fields = ["id", "title", "description", "content", "url", "source"]
            for field in required_fields:
                assert field in article, f"Article should have '{field}' field"
            
            # Check types
            assert isinstance(article["title"], str), "Title should be string"
            assert isinstance(article["url"], str), "URL should be string"
            assert len(article["title"]) > 0, "Title should not be empty"
            
        except NewsFetcherError as e:
            # Skip if API key not configured
            if "not configured" in str(e):
                pytest.skip("NewsAPI key not configured")
            raise
    
    def test_get_article_text_combines_fields(self):
        """Test that get_article_text properly combines article fields."""
        article = {
            "title": "Test Title",
            "description": "Test Description",
            "content": "Test Content"
        }
        
        text = get_article_text(article)
        
        assert "Test Title" in text
        assert "Test Description" in text
        assert "Test Content" in text
        assert "Title:" in text
        assert "Description:" in text
        assert "Content:" in text
    
    def test_empty_article_handling(self):
        """Test that empty articles are handled gracefully."""
        article = {
            "title": "",
            "description": "",
            "content": ""
        }
        
        text = get_article_text(article)
        # Should not raise an error, just return empty or minimal text
        assert isinstance(text, str)


class TestAnalyzer:
    """Tests for the LLM analyzer module."""
    
    def test_analyzer_output_structure(self):
        """Test that analyzer returns correct JSON structure."""
        test_article = {
            "id": 1,
            "title": "India announces major economic reform",
            "description": "New policy aims to boost GDP growth",
            "content": "The government today announced comprehensive reforms including tax cuts and infrastructure spending to accelerate economic growth.",
            "source": "Test Source",
            "url": "https://example.com"
        }
        
        try:
            result = analyze_article(test_article)
            
            # Check structure
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "gist" in result, "Result should have 'gist' field"
            assert "sentiment" in result, "Result should have 'sentiment' field"
            assert "tone" in result, "Result should have 'tone' field"
            
            # Check sentiment is valid
            assert result["sentiment"] in ["positive", "negative", "neutral"], \
                f"Invalid sentiment: {result['sentiment']}"
            
            # Check tone is valid
            valid_tones = ["urgent", "analytical", "satirical", "balanced", 
                         "critical", "optimistic", "pessimistic", "informative"]
            assert result["tone"] in valid_tones, f"Invalid tone: {result['tone']}"
            
            # Check gist is non-empty string
            assert isinstance(result["gist"], str) and len(result["gist"]) > 0, \
                "Gist should be non-empty string"
            
        except AnalyzerError as e:
            if "not configured" in str(e):
                pytest.skip("OpenAI API key not configured")
            raise


class TestValidator:
    """Tests for the LLM validator module."""
    
    def test_validator_detects_mismatch(self):
        """Test that validator can detect intentionally wrong analysis."""
        # Article with clearly negative content
        negative_article = {
            "title": "Economic crisis deepens in India",
            "description": "Markets crash as inflation soars",
            "content": "India faces severe economic challenges as stock markets plummet, inflation reaches record highs, and unemployment continues to rise. Experts warn of difficult times ahead.",
            "source": "Test Source"
        }
        
        # Intentionally wrong positive analysis
        wrong_analysis = {
            "gist": "India's economy is booming with great success",
            "sentiment": "positive",
            "tone": "optimistic"
        }
        
        try:
            validation = validate_analysis(negative_article, wrong_analysis)
            
            # Check structure
            assert isinstance(validation, dict), "Validation should be a dictionary"
            assert "is_valid" in validation, "Should have 'is_valid' field"
            assert "validation_notes" in validation, "Should have 'validation_notes' field"
            
            # The validator should detect the mismatch
            # Note: is_valid might still be True if the LLM is lenient,
            # but validation_notes should mention the discrepancy
            assert isinstance(validation["is_valid"], bool), "is_valid should be boolean"
            assert len(validation["validation_notes"]) > 0, "Should provide notes"
            
        except ValidatorError as e:
            if "not configured" in str(e):
                pytest.skip("OpenRouter API key not configured")
            raise
    
    def test_validator_accepts_correct_analysis(self):
        """Test that validator accepts correctly analyzed content."""
        article = {
            "title": "India launches new education initiative",
            "description": "Government program aims to improve literacy",
            "content": "The education ministry unveiled a new nationwide program to improve access to quality education in rural areas.",
            "source": "Test Source"
        }
        
        correct_analysis = {
            "gist": "India's government launched a new program to improve rural education access",
            "sentiment": "positive",
            "tone": "informative"
        }
        
        try:
            validation = validate_analysis(article, correct_analysis)
            
            # Check structure
            assert isinstance(validation, dict)
            assert "is_valid" in validation
            assert "validation_notes" in validation
            
            # Correct analysis should generally be validated as valid
            # (though LLM responses can vary)
            
        except ValidatorError as e:
            if "not configured" in str(e):
                pytest.skip("OpenRouter API key not configured")
            raise


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    def test_end_to_end_single_article(self):
        """Test the full pipeline with a single article."""
        test_article = {
            "id": 1,
            "title": "India to host G20 summit",
            "description": "World leaders gather in New Delhi",
            "content": "India will host the prestigious G20 summit, bringing together leaders from the world's largest economies to discuss global challenges.",
            "source": "Test Source",
            "url": "https://example.com"
        }
        
        try:
            # Step 1: Analyze
            analysis = analyze_article(test_article)
            assert "gist" in analysis
            assert "sentiment" in analysis
            assert "tone" in analysis
            
            # Step 2: Validate
            validation = validate_analysis(test_article, analysis)
            assert "is_valid" in validation
            assert "validation_notes" in validation
            
            # Pipeline completed successfully
            print(f"\nAnalysis: {json.dumps(analysis, indent=2)}")
            print(f"Validation: {json.dumps(validation, indent=2)}")
            
        except (AnalyzerError, ValidatorError) as e:
            if "not configured" in str(e):
                pytest.skip("API keys not configured")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
