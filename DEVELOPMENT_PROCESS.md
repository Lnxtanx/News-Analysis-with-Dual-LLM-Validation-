# Development Process - News Analyzer with Dual LLM Validation

## Project Overview

Built a fact-checking pipeline where Gemini analyzes news articles and OpenAI validates the analysis.

---

## Task Breakdown

### 1. Fetch Articles (NewsAPI)
- Query: "India politics OR India government"
- Fetch 10-15 recent articles
- Handle API errors: timeouts, rate limits, invalid keys
- Clean articles: skip removed/empty content

### 2. Analyze with LLM#1 (Gemini)
For each article, extract:
- **Gist**: 1-2 sentence summary
- **Sentiment**: positive/negative/neutral
- **Tone**: urgent/analytical/satirical/balanced/etc.

### 3. Validate with LLM#2 (OpenAI)
Cross-check each analysis:
- Does the gist accurately summarize the article?
- Does the sentiment match the content?
- Is the tone classification appropriate?
- Suggest corrections if needed

### 4. Generate Reports
- `raw_articles.json`: Original fetched articles
- `analysis_results.json`: Full analysis + validation data
- `final_report.md`: Human-readable report

---

## Design Decisions

### Why Gemini + OpenAI?

| Aspect | Gemini (Analyzer) | OpenAI (Validator) |
|--------|------------------|-------------------|
| Role | Primary analysis | Cross-validation |
| Model | gemini-1.5-flash | gpt-4o-mini |
| Strengths | Fast structured extraction | Strong reasoning |
| Cost | Competitive | Cost-effective |

**Key insight**: Using different LLM providers ensures genuine validation. Same-provider models share training biases, defeating the fact-checking purpose.

### Error Handling Strategy

1. **Transient failures**: Retry with exponential backoff (3 attempts)
2. **API key errors**: Clear error messages directing to setup
3. **Invalid JSON**: Parse cleanup for markdown-wrapped responses
4. **Empty content**: Skip gracefully, don't fail entire pipeline

### JSON Parsing Robustness

Both LLMs sometimes wrap JSON in markdown code blocks. Solution:
```python
if response_text.startswith("```"):
    lines = response_text.split("\n")
    response_text = "\n".join(lines[1:-1])
```

---

## Iteration Log

### Issue 1: LLM returns inconsistent sentiment values
**Problem**: Gemini sometimes returned "Positive" or "POSITIVE" instead of "positive"
**Solution**: Normalize to lowercase and validate against allowed values

### Issue 2: Rate limiting
**Problem**: Rapid API calls triggered rate limits
**Solution**: Added 1-second delay between article processing

### Issue 3: Empty article content
**Problem**: Some NewsAPI articles have truncated or removed content
**Solution**: Filter out articles with content < 50 characters

---

## File Structure

```
news-analyzer/
├── main.py              # Flask app + orchestration
├── llm_analyzer.py      # Gemini analysis
├── llm_validator.py     # OpenAI validation
├── news_fetcher.py      # NewsAPI integration
├── .env                 # API keys
├── .gitignore
├── requirements.txt
├── DEVELOPMENT_PROCESS.md
├── output/
│   ├── raw_articles.json
│   ├── analysis_results.json
│   └── final_report.md
└── tests/
    └── test_analyzer.py
```

---

## Testing Strategy

| Test | Purpose |
|------|---------|
| `test_news_fetcher_returns_articles` | Verify fetcher returns valid structure |
| `test_get_article_text_combines_fields` | Unit test for text extraction |
| `test_empty_article_handling` | Graceful handling of edge cases |
| `test_analyzer_output_structure` | Verify Gemini returns correct JSON |
| `test_validator_detects_mismatch` | Verify OpenAI catches wrong analysis |
| `test_validator_accepts_correct_analysis` | Positive validation case |
| `test_end_to_end_single_article` | Full pipeline integration test |

---

## Running the Application

```bash
# Setup
cd news-analyzer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configure API keys in .env

# Run Flask app
python main.py

# Trigger analysis
curl -X POST http://localhost:5000/analyze

# Run tests
python -m pytest tests/ -v
```

---

## Future Improvements

1. **Caching**: Cache NewsAPI responses to reduce API calls during development
2. **Parallel processing**: Use async/await for concurrent LLM calls
3. **Confidence scores**: Add confidence metrics to analysis
4. **Historical tracking**: Compare sentiment trends over time
5. **Multiple topics**: Support different news categories beyond politics
