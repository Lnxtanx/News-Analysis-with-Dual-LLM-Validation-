"""
News Analyzer - Flask Application
Main entry point that orchestrates the news analysis pipeline.
"""

import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from dotenv import load_dotenv

from news_fetcher import fetch_news, NewsFetcherError, get_article_text
from llm_analyzer import analyze_articles, AnalyzerError
from llm_validator import validate_analyses, ValidatorError

load_dotenv()

app = Flask(__name__)

# Ensure output directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(data: dict | list, filename: str) -> str:
    """Save data to JSON file in output directory."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath


def generate_markdown_report(validated_results: list, raw_articles: list) -> str:
    """
    Generate a human-readable Markdown report.
    
    Args:
        validated_results: List of validated analysis results
        raw_articles: Original raw articles
        
    Returns:
        Path to the generated report file
    """
    # Calculate statistics
    total = len(validated_results)
    positive = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "positive")
    negative = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "negative")
    neutral = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "neutral")
    
    validated_count = sum(1 for r in validated_results if r.get("validation", {}).get("is_valid", False))
    
    # Build report
    report_lines = [
        "# News Analysis Report",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Articles Analyzed:** {total}",
        f"**Source:** NewsAPI",
        f"**Topic:** India Politics / India Government",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Positive:** {positive} articles",
        f"- **Negative:** {negative} articles",
        f"- **Neutral:** {neutral} articles",
        "",
        f"**Validation Rate:** {validated_count}/{total} analyses validated by LLM#2",
        "",
        "---",
        "",
        "## Detailed Analysis",
        ""
    ]
    
    for i, result in enumerate(validated_results, 1):
        title = result.get("title", "Unknown Title")
        url = result.get("url", "#")
        source = result.get("source", "Unknown")
        
        analysis = result.get("analysis", {})
        gist = analysis.get("gist", "N/A")
        sentiment = analysis.get("sentiment", "N/A")
        tone = analysis.get("tone", "N/A")
        
        validation = result.get("validation", {})
        is_valid = validation.get("is_valid", False)
        validation_notes = validation.get("validation_notes", "No validation performed")
        suggested = validation.get("suggested_corrections")
        
        # Validation symbol
        valid_symbol = "✓" if is_valid else "✗"
        
        report_lines.extend([
            f"### Article {i}: \"{title[:80]}{'...' if len(title) > 80 else ''}\"",
            "",
            f"- **Source:** [{source}]({url})",
            f"- **Gist:** {gist}",
            f"- **LLM#1 Sentiment:** {sentiment.capitalize()}",
            f"- **LLM#1 Tone:** {tone.capitalize()}",
            f"- **LLM#2 Validation:** {valid_symbol} {validation_notes}",
        ])
        
        if suggested:
            corrections = ", ".join([f"{k}: {v}" for k, v in suggested.items()])
            report_lines.append(f"- **Suggested Corrections:** {corrections}")
        
        report_lines.extend(["", "---", ""])
    
    # Write report
    report_content = "\n".join(report_lines)
    filepath = os.path.join(OUTPUT_DIR, "final_report.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    return filepath


@app.route("/")
def index():
    """Status page."""
    return jsonify({
        "status": "running",
        "service": "News Analyzer with Dual LLM Validation",
        "endpoints": {
            "POST /analyze": "Run full analysis pipeline",
            "GET /report": "Get latest Markdown report",
            "GET /results": "Get latest JSON results"
        }
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Run the full news analysis pipeline.
    
    Optional JSON body:
    - query: Custom search query (default: "India politics OR India government")
    - num_articles: Number of articles to fetch (default: 15)
    """
    try:
        # Get parameters
        data = request.get_json() or {}
        query = data.get("query", "India politics OR India government")
        num_articles = data.get("num_articles", 15)
        
        print(f"\n{'='*60}")
        print(f"Starting News Analysis Pipeline")
        print(f"Query: {query}")
        print(f"Articles: {num_articles}")
        print(f"{'='*60}\n")
        
        # Step 1: Fetch news articles
        print("Step 1: Fetching news articles...")
        try:
            articles = fetch_news(query=query, num_articles=num_articles)
            print(f"  ✓ Fetched {len(articles)} articles")
        except NewsFetcherError as e:
            return jsonify({"error": f"Failed to fetch news: {e}"}), 500
        
        # Save raw articles
        save_json(articles, "raw_articles.json")
        print(f"  ✓ Saved raw articles to output/raw_articles.json")
        
        # Step 2: Analyze with LLM#1 (Gemini)
        print("\nStep 2: Analyzing with Gemini (LLM#1)...")
        try:
            analyses = analyze_articles(articles)
            print(f"  ✓ Analyzed {len(analyses)} articles")
        except AnalyzerError as e:
            return jsonify({"error": f"Failed to analyze: {e}"}), 500
        
        # Step 3: Validate with LLM#2 (OpenAI)
        print("\nStep 3: Validating with OpenAI (LLM#2)...")
        try:
            validated_results = validate_analyses(articles, analyses)
            print(f"  ✓ Validated {len(validated_results)} analyses")
        except ValidatorError as e:
            return jsonify({"error": f"Failed to validate: {e}"}), 500
        
        # Save analysis results
        save_json(validated_results, "analysis_results.json")
        print(f"  ✓ Saved analysis results to output/analysis_results.json")
        
        # Step 4: Generate report
        print("\nStep 4: Generating Markdown report...")
        report_path = generate_markdown_report(validated_results, articles)
        print(f"  ✓ Generated report at output/final_report.md")
        
        # Summary
        positive = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "positive")
        negative = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "negative")
        neutral = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "neutral")
        validated = sum(1 for r in validated_results if r.get("validation", {}).get("is_valid", False))
        
        print(f"\n{'='*60}")
        print(f"Analysis Complete!")
        print(f"{'='*60}")
        
        return jsonify({
            "status": "success",
            "summary": {
                "total_articles": len(articles),
                "analyzed": len(analyses),
                "validated": validated,
                "sentiment_breakdown": {
                    "positive": positive,
                    "negative": negative,
                    "neutral": neutral
                }
            },
            "files": {
                "raw_articles": "output/raw_articles.json",
                "analysis_results": "output/analysis_results.json",
                "final_report": "output/final_report.md"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/report")
def get_report():
    """Get the latest Markdown report."""
    report_path = os.path.join(OUTPUT_DIR, "final_report.md")
    if not os.path.exists(report_path):
        return jsonify({"error": "No report available. Run /analyze first."}), 404
    
    return send_file(report_path, mimetype="text/markdown")


@app.route("/results")
def get_results():
    """Get the latest JSON results."""
    results_path = os.path.join(OUTPUT_DIR, "analysis_results.json")
    if not os.path.exists(results_path):
        return jsonify({"error": "No results available. Run /analyze first."}), 404
    
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    return jsonify(results)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("News Analyzer with Dual LLM Validation")
    print("="*60)
    print("\nEndpoints:")
    print("  GET  /         - Status page")
    print("  POST /analyze  - Run analysis pipeline")
    print("  GET  /report   - Get Markdown report")
    print("  GET  /results  - Get JSON results")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=5000)
