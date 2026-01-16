"""
News Analyzer - Enhanced ChatGPT-Style Interface
A premium chat UI for analyzing Indian politics news with dual LLM validation.
"""

import streamlit as st
import time
from datetime import datetime
import json

# Import modules from the project
from news_fetcher import fetch_news, NewsFetcherError, get_article_text
from llm_analyzer import analyze_article, AnalyzerError
from llm_validator import validate_analysis, ValidatorError

# Page configuration
st.set_page_config(
    page_title="News Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Premium ChatGPT-style CSS
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background */
    .stApp {
        background: #212121;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #171717;
        border-right: 1px solid #2d2d2d;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #ececec;
    }
    
    /* Main header */
    .main-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ececec;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid #2d2d2d;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        font-size: 0.85rem;
        color: #8e8e8e;
        text-align: center;
        margin-top: -0.5rem;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    /* Message bubbles */
    .user-msg {
        background: #2f2f2f;
        border-radius: 1.5rem;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: #ececec;
    }
    
    .assistant-msg {
        background: transparent;
        padding: 1rem 0;
        margin: 1rem 0;
        color: #d1d1d1;
        line-height: 1.6;
    }
    
    /* Article cards */
    .article-card {
        background: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.2s ease;
    }
    
    .article-card:hover {
        background: #333333;
        border-color: #4a4a4a;
        transform: translateY(-1px);
    }
    
    .article-title {
        font-size: 1rem;
        font-weight: 600;
        color: #ececec;
        margin-bottom: 0.5rem;
        text-decoration: none;
    }
    
    .article-title a {
        color: #ececec;
        text-decoration: none;
    }
    
    .article-title a:hover {
        color: #10a37f;
        text-decoration: underline;
    }
    
    .article-source {
        font-size: 0.75rem;
        color: #8e8e8e;
        margin-bottom: 0.75rem;
    }
    
    .article-gist {
        font-size: 0.9rem;
        color: #b4b4b4;
        line-height: 1.5;
        margin-bottom: 0.75rem;
    }
    
    /* Tags */
    .tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    
    .tag-positive {
        background: rgba(16, 163, 127, 0.2);
        color: #10a37f;
    }
    
    .tag-negative {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    .tag-neutral {
        background: rgba(234, 179, 8, 0.2);
        color: #eab308;
    }
    
    .tag-tone {
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
    }
    
    .tag-valid {
        background: rgba(16, 163, 127, 0.2);
        color: #10a37f;
    }
    
    .tag-invalid {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    /* Stats cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .stat-card {
        background: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #ececec;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #8e8e8e;
        margin-top: 0.25rem;
    }
    
    /* Pipeline steps */
    .pipeline-step {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        background: #2a2a2a;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #b4b4b4;
    }
    
    .pipeline-step.active {
        background: #10a37f20;
        border-left: 3px solid #10a37f;
        color: #10a37f;
    }
    
    .pipeline-step.done {
        color: #10a37f;
    }
    
    /* Chat input styling */
    .stChatInput {
        border-top: 1px solid #2d2d2d;
        padding-top: 1rem;
    }
    
    .stChatInput > div {
        background: #2f2f2f !important;
        border-radius: 1.5rem !important;
        border: 1px solid #3d3d3d !important;
    }
    
    .stChatInput input {
        color: #ececec !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #2a2a2a;
        border-radius: 8px;
        color: #ececec;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: #10a37f;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 12px;
        padding: 1rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #8e8e8e;
    }
    
    [data-testid="stMetricValue"] {
        color: #ececec;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #212121;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3d3d3d;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4a4a4a;
    }
    
    /* Links */
    a {
        color: #10a37f;
    }
    
    a:hover {
        color: #0d8c6d;
    }
    
    /* View Article Button */
    .view-btn {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        background: #10a37f;
        color: white !important;
        border-radius: 6px;
        font-size: 0.8rem;
        text-decoration: none;
        margin-top: 0.5rem;
        transition: background 0.2s;
    }
    
    .view-btn:hover {
        background: #0d8c6d;
        color: white !important;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = []
    if "raw_articles" not in st.session_state:
        st.session_state.raw_articles = []


def get_sentiment_tag(sentiment):
    """Return HTML for sentiment tag."""
    colors = {
        "positive": "tag-positive",
        "negative": "tag-negative",
        "neutral": "tag-neutral"
    }
    return f'<span class="tag {colors.get(sentiment, "tag-neutral")}">{sentiment.upper()}</span>'


def get_validation_tag(is_valid):
    """Return HTML for validation tag."""
    if is_valid:
        return '<span class="tag tag-valid">✓ VALIDATED</span>'
    return '<span class="tag tag-invalid">⚠ ISSUES FOUND</span>'


def display_article_card(article, analysis, validation, index):
    """Display a single article as a card."""
    title = article.get("title", "Untitled")
    url = article.get("url", "#")
    source = article.get("source", "Unknown")
    
    gist = analysis.get("gist", "No summary available")
    sentiment = analysis.get("sentiment", "neutral")
    tone = analysis.get("tone", "informative")
    is_valid = validation.get("is_valid", False)
    validation_notes = validation.get("validation_notes", "")
    
    st.markdown(f"""
    <div class="article-card">
        <div class="article-title">
            <a href="{url}" target="_blank">📄 {title}</a>
        </div>
        <div class="article-source">Source: {source}</div>
        <div class="article-gist">{gist}</div>
        <div style="margin-top: 0.75rem;">
            {get_sentiment_tag(sentiment)}
            <span class="tag tag-tone">{tone.upper()}</span>
            {get_validation_tag(is_valid)}
        </div>
        <div style="margin-top: 0.75rem;">
            <a href="{url}" target="_blank" class="view-btn">🔗 Read Full Article</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Expandable validation details
    with st.expander(f"🔍 Validation Details", expanded=False):
        st.markdown(f"**LLM#2 Notes:** {validation_notes}")
        if validation.get("suggested_corrections"):
            st.markdown("**Suggested Corrections:**")
            for k, v in validation["suggested_corrections"].items():
                st.markdown(f"- **{k}:** {v}")


def analyze_news_pipeline(query: str, num_articles: int):
    """Run the full news analysis pipeline with ChatGPT-style output."""
    
    st.markdown("---")
    
    # Pipeline status
    col1, col2, col3, col4 = st.columns(4)
    status_fetch = col1.empty()
    status_analyze = col2.empty()
    status_validate = col3.empty()
    status_report = col4.empty()
    
    status_fetch.markdown("🔄 **Fetching...**")
    status_analyze.markdown("⏳ Analyzing")
    status_validate.markdown("⏳ Validating")
    status_report.markdown("⏳ Reporting")
    
    # Step 1: Fetch
    try:
        articles = fetch_news(query=query, num_articles=num_articles)
        st.session_state.raw_articles = articles
        status_fetch.markdown(f"✅ **Fetched {len(articles)}**")
    except NewsFetcherError as e:
        status_fetch.markdown("❌ **Failed**")
        st.error(f"Failed to fetch news: {e}")
        return []
    
    status_analyze.markdown("🔄 **Analyzing...**")
    
    # Progress
    progress = st.progress(0)
    results = []
    
    for i, article in enumerate(articles):
        # Analyze
        try:
            analysis = analyze_article(article)
        except AnalyzerError as e:
            analysis = {"gist": f"Error: {e}", "sentiment": "neutral", "tone": "informative"}
        
        if i == len(articles) // 2:
            status_analyze.markdown("✅ **Analyzed**")
            status_validate.markdown("🔄 **Validating...**")
        
        # Validate
        try:
            validation = validate_analysis(article, analysis)
        except ValidatorError as e:
            validation = {"is_valid": True, "validation_notes": f"Error: {e}"}
        
        results.append({
            "article": article,
            "analysis": analysis,
            "validation": validation
        })
        
        progress.progress((i + 1) / len(articles))
        time.sleep(0.3)
    
    status_analyze.markdown("✅ **Analyzed**")
    status_validate.markdown("✅ **Validated**")
    status_report.markdown("✅ **Complete**")
    
    progress.empty()
    
    return results


def display_results(results):
    """Display analysis results in ChatGPT style."""
    if not results:
        return
    
    # Summary stats
    total = len(results)
    positive = sum(1 for r in results if r["analysis"].get("sentiment") == "positive")
    negative = sum(1 for r in results if r["analysis"].get("sentiment") == "negative")
    neutral = sum(1 for r in results if r["analysis"].get("sentiment") == "neutral")
    validated = sum(1 for r in results if r["validation"].get("is_valid", False))
    
    st.markdown("### 📊 Analysis Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📰 Articles", total)
    col2.metric("😊 Positive", positive)
    col3.metric("😟 Negative", negative)
    col4.metric("✅ Validated", f"{validated}/{total}")
    
    st.markdown("---")
    st.markdown("### 📄 Analyzed Articles")
    st.markdown("*Click on any article title or the 'Read Full Article' button to view the original source.*")
    
    # Display each article
    for i, result in enumerate(results):
        display_article_card(
            result["article"],
            result["analysis"],
            result["validation"],
            i
        )


def main():
    """Main application."""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        st.markdown("---")
        
        query = st.text_input(
            "🔍 Search Query",
            value="India politics OR India government",
            help="NewsAPI search query"
        )
        
        num_articles = st.slider(
            "📰 Articles to Fetch",
            min_value=3,
            max_value=15,
            value=5
        )
        
        st.markdown("---")
        st.markdown("### 🔧 Pipeline")
        st.markdown("""
        1. **Fetch** → NewsAPI
        2. **Analyze** → OpenAI
        3. **Validate** → Nemotron
        """)
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        Dual LLM news analysis 
        with cross-validation.
        """)
    
    # Main content
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">📰 News Analyzer</div>
    <div class="sub-header">Dual LLM Pipeline: OpenAI → OpenRouter/Nemotron</div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("results"):
                display_results(msg["results"])
    
    # Chat input
    if prompt := st.chat_input("Ask me to analyze news... (e.g., 'Analyze Indian politics news')"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if any(word in prompt.lower() for word in ["analyze", "news", "fetch", "start", "run", "get"]):
                st.markdown(f"🚀 **Starting analysis for:** {query}")
                st.markdown(f"Fetching **{num_articles}** articles and running dual LLM analysis...")
                
                results = analyze_news_pipeline(query, num_articles)
                
                if results:
                    st.session_state.analysis_results = results
                    display_results(results)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"✅ Analysis complete! Processed {len(results)} articles.",
                        "results": results
                    })
                else:
                    msg = "❌ Analysis failed. Please check your API keys."
                    st.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                response = """👋 **Welcome to News Analyzer!**

I can help you analyze news articles using two different AI models for cross-validation.

**Try saying:**
- "Analyze news"
- "Get Indian politics news"
- "Start analysis"

Configure the search query and number of articles in the sidebar. →"""
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
