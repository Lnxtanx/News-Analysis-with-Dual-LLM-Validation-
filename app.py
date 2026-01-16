"""
News Analyzer - Streamlit Chat UI
A ChatGPT-style conversational interface for analyzing news with dual LLM validation.
"""

import streamlit as st
import json
import os
import re
from datetime import datetime

from news_fetcher import fetch_news, NewsFetcherError
from llm_analyzer import analyze_articles, AnalyzerError
from llm_validator import validate_analyses, ValidatorError

# Page configuration
st.set_page_config(
    page_title="News Analyzer AI",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-style dark theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables */
    :root {
        --bg-primary: #0f0f0f;
        --bg-secondary: #1a1a1a;
        --bg-tertiary: #252525;
        --accent-purple: #8b5cf6;
        --accent-blue: #3b82f6;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-yellow: #f59e0b;
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
        --border-color: #333333;
    }
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1a2e 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }

    /* Fixed Sidebar Selectbox Styling */
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #1a1a2e !important;
        color: white !important;
        border-color: rgba(139, 92, 246, 0.4) !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] span {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] svg {
        fill: white !important;
    }

    /* Dropdown Options Styling */
    [data-baseweb="popover"], [data-baseweb="menu"] {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
    }

    [data-baseweb="menu"] > ul > li {
        background-color: transparent !important;
        color: white !important;
    }

    [data-baseweb="menu"] > ul > li:hover, [data-baseweb="menu"] > ul > li[aria-selected="true"] {
        background-color: rgba(139, 92, 246, 0.2) !important;
    }    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fix bottom chat input area background */
    [data-testid="stBottom"] {
        background: transparent !important;
    }
    
    [data-testid="stBottom"] > div {
        background: linear-gradient(180deg, transparent 0%, rgba(15, 15, 15, 0.95) 30%, #0f0f0f 100%) !important;
        padding-top: 2rem !important;
    }
    
    .stChatFloatingInputContainer {
        background: transparent !important;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, #2d2d4a 0%, #1e293b 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .chat-message.assistant {
        background: linear-gradient(135deg, #1e1e2e 0%, #252540 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        flex-shrink: 0;
    }
    
    .chat-message.user .avatar {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    }
    
    .chat-message.assistant .avatar {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    }
    
    .chat-message .content {
        flex: 1;
        color: #fff;
        line-height: 1.6;
    }
    
    .chat-message .content p {
        margin: 0;
    }
    
    /* Article cards */
    .article-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .article-card:hover {
        transform: translateY(-2px);
        border-color: rgba(139, 92, 246, 0.5);
    }
    
    .article-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .article-title a {
        color: #8b5cf6;
        text-decoration: none;
    }
    
    .article-title a:hover {
        color: #a78bfa;
    }
    
    /* Sentiment badges */
    .sentiment-positive {
        display: inline-block;
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .sentiment-negative {
        display: inline-block;
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: white;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .sentiment-neutral {
        display: inline-block;
        background: linear-gradient(135deg, #4b5563 0%, #6b7280 100%);
        color: white;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Tone badge */
    .tone-badge {
        display: inline-block;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-left: 0.5rem;
    }
    
    /* Validation status */
    .validation-valid {
        color: #10b981;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    
    .validation-invalid {
        color: #ef4444;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #252540 100%);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label {
        color: var(--text-secondary);
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    
    /* Gist text */
    .gist-text {
        font-style: italic;
        color: #a1a1aa;
        background: rgba(139, 92, 246, 0.1);
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 3px solid #8b5cf6;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    
    /* Source info */
    .source-info {
        color: #71717a;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    /* Custom divider */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(139, 92, 246, 0.3) 50%, transparent 100%);
        margin: 1.5rem 0;
    }
    
    /* Chat input styling - centered and curved */
    /* Chat input styling - centered and curved */
    [data-testid="stChatInput"] {
        max-width: 700px !important;
        margin: 0 auto !important;
        padding: 0.5rem 1rem !important;
    }
    
    [data-testid="stChatInput"] > div {
        background: linear-gradient(135deg, #1a1a2e 0%, #252540 100%) !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
        border-radius: 28px !important;
        padding: 0.25rem 0.5rem !important;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.15) !important;
        color: white !important;
    }
    
    [data-testid="stChatInput"] textarea, [data-testid="stChatInput"] input {
        color: #e4e4e7 !important;
        background-color: transparent !important;
        background: transparent !important;
        font-size: 0.95rem !important;
        caret-color: #8b5cf6 !important;
    }
    
    /* Deep targeting for chat input background */
    [data-testid="stChatInput"] [data-baseweb="textarea"], 
    [data-testid="stChatInput"] [data-baseweb="base-input"] {
        background-color: transparent !important;
        background: transparent !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #71717a !important;
    }
    
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%) !important;
        border-radius: 50% !important;
        width: 35px !important;
        height: 35px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: white !important;
    }

    /* Style the input container specifically */
    .stChatInputContainer {
        padding-bottom: 1rem !important;
    }
    
    /* Welcome box */
    .welcome-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    
    .welcome-box h2 {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .example-queries {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        justify-content: center;
        margin-top: 1.5rem;
    }
    
    .example-query {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        color: #a78bfa;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .example-query:hover {
        background: rgba(139, 92, 246, 0.2);
        border-color: rgba(139, 92, 246, 0.5);
    }
</style>
""", unsafe_allow_html=True)


def get_sentiment_class(sentiment: str) -> str:
    """Get CSS class for sentiment badge."""
    sentiment = sentiment.lower()
    if sentiment == "positive":
        return "sentiment-positive"
    elif sentiment == "negative":
        return "sentiment-negative"
    return "sentiment-neutral"


def render_article_card(result: dict, index: int) -> str:
    """Render a single article analysis card as HTML."""
    title = result.get("title", "Unknown Title")
    url = result.get("url", "#")
    source = result.get("source", "Unknown")
    
    analysis = result.get("analysis", {})
    gist = analysis.get("gist", "No summary available")
    sentiment = analysis.get("sentiment", "neutral")
    tone = analysis.get("tone", "informative")
    
    validation = result.get("validation", {})
    is_valid = validation.get("is_valid", False)
    validation_notes = validation.get("validation_notes", "")[:80]
    
    sentiment_class = get_sentiment_class(sentiment)
    validation_class = "validation-valid" if is_valid else "validation-invalid"
    validation_icon = "✓" if is_valid else "✗"
    
    return f"""
    <div class="article-card">
        <div class="article-title">
            <a href="{url}" target="_blank">📰 {title[:70]}{'...' if len(title) > 70 else ''}</a>
        </div>
        <div class="gist-text">"{gist}"</div>
        <div>
            <span class="{sentiment_class}">{sentiment.capitalize()}</span>
            <span class="tone-badge">{tone.capitalize()}</span>
        </div>
        <div class="{validation_class}">{validation_icon} {validation_notes}</div>
        <div class="source-info">Source: {source}</div>
    </div>
    """


def render_stats_html(results: list) -> str:
    """Render statistics as HTML."""
    total = len(results)
    positive = sum(1 for r in results if r.get("analysis", {}).get("sentiment") == "positive")
    negative = sum(1 for r in results if r.get("analysis", {}).get("sentiment") == "negative")
    neutral = sum(1 for r in results if r.get("analysis", {}).get("sentiment") == "neutral")
    validated = sum(1 for r in results if r.get("validation", {}).get("is_valid", False))
    validation_rate = int((validated / total) * 100) if total > 0 else 0
    
    return f"""
    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; margin: 1rem 0;">
        <div class="stat-card">
            <div class="stat-number">{total}</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="background: linear-gradient(135deg, #059669, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{positive}</div>
            <div class="stat-label">Positive</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="background: linear-gradient(135deg, #dc2626, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{negative}</div>
            <div class="stat-label">Negative</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="background: linear-gradient(135deg, #4b5563, #6b7280); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{neutral}</div>
            <div class="stat-label">Neutral</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{validation_rate}%</div>
            <div class="stat-label">Validated</div>
        </div>
    </div>
    </div>
    """


def render_pipeline_inspector(debug_data: dict):
    """Render the pipeline inspector with architecture and data."""
    with st.expander("🔍 Pipeline Inspector (Under the Hood)", expanded=False):
        st.markdown("### 🧩 Pipeline Architecture")
        
        # Architecture Visualization
        st.markdown("""
        <div style="background: #0f0f0f; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; border: 1px solid rgba(139, 92, 246, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; text-align: center; position: relative;">
                <div style="flex: 1;">
                    <div style="font-size: 2rem;">👤</div>
                    <div style="font-size: 0.8rem; color: #a1a1aa; margin-top: 0.5rem;">User Query</div>
                    <div style="font-size: 0.7rem; color: #71717a; margin-top: 0.2rem;">"{debug_data.get('query', 'Topic')}"</div>
                </div>
                <div style="font-size: 1.5rem; color: #4b5563;">➜</div>
                 <div style="flex: 1;">
                    <div style="font-size: 2rem;">🌍</div>
                    <div style="font-size: 0.8rem; color: #a1a1aa; margin-top: 0.5rem;">NewsAPI</div>
                     <div style="font-size: 0.7rem; color: #71717a; margin-top: 0.2rem;">{debug_data.get('articles_fetched', 0)} articles</div>
                </div>
                <div style="font-size: 1.5rem; color: #4b5563;">➜</div>
                <div style="flex: 1; position: relative;">
                    <div style="font-size: 2rem; filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.3));">🧠</div>
                    <div style="font-size: 0.8rem; color: #a1a1aa; margin-top: 0.5rem;">LLM #1<br>(GPT-4o)</div>
                    <span style="position: absolute; top: -10px; right: 10px; background: #8b5cf6; color: white; font-size: 0.6rem; padding: 2px 6px; border-radius: 10px;">Analysis</span>
                </div>
                <div style="font-size: 1.5rem; color: #4b5563;">➜</div>
                <div style="flex: 1; position: relative;">
                    <div style="font-size: 2rem; filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.3));">🛡️</div>
                    <div style="font-size: 0.8rem; color: #a1a1aa; margin-top: 0.5rem;">LLM #2<br>(Nemotron)</div>
                     <span style="position: absolute; top: -10px; right: 10px; background: #10b981; color: white; font-size: 0.6rem; padding: 2px 6px; border-radius: 10px;">Validation</span>
                </div>
            </div>
            <div style="margin-top: 1rem; text-align: center; font-size: 0.75rem; color: #52525b; font-style: italic;">
                Double-Agent Verification Architecture
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Data Inspection Tabs
        tab1, tab2, tab3 = st.tabs(["📄 Raw Articles", "🧠 Agent 1 Output", "🛡️ Agent 2 Output"])
        
        with tab1:
            st.caption(f"Fetching top {debug_data.get('articles_fetched', 0)} articles")
            st.json(debug_data.get("articles_preview", []))
            
        with tab2:
            st.caption("Raw analysis from OpenAI GPT-4o-mini (Before Validation)")
            if debug_data.get("raw_analysis"):
                st.json(debug_data.get("raw_analysis")[0] if isinstance(debug_data.get("raw_analysis"), list) and debug_data.get("raw_analysis") else {})
            else:
                st.info("No analysis data available")
                
        with tab3:
            st.caption("Validated output from OpenRouter/Nemotron (Final Result)")
            if debug_data.get("raw_validation"):
                # showing first valid result
                st.json(debug_data.get("raw_validation")[0] if isinstance(debug_data.get("raw_validation"), list) and debug_data.get("raw_validation") else {})
            else:
                st.info("No validation data available")

def parse_user_query(query: str) -> tuple[str, int]:
    """Parse user query to extract topic and number of articles."""
    # Default values
    topic = query.strip()
    num_articles = 10
    
    # Check for number patterns like "5 articles", "get 10", etc.
    num_match = re.search(r'(\d+)\s*(articles?|news|stories)?', query.lower())
    if num_match:
        num = int(num_match.group(1))
        if 1 <= num <= 20:
            num_articles = num
    
    # Clean up the topic
    topic = re.sub(r'\d+\s*(articles?|news|stories)?', '', topic, flags=re.IGNORECASE).strip()
    topic = re.sub(r'^(analyze|fetch|find|show|search)\s*(me)?\s*(news|articles?)?\s*(about|on|for)?\s*', '', topic, flags=re.IGNORECASE).strip()
    
    # Don't strip "get" if it might be part of "get lucky" or similar, but "get 5 articles" is okay to strip
    topic = re.sub(r'^get\s+(\d+\s+)?(articles?|news)\s+(about|on|for)?', '', topic, flags=re.IGNORECASE).strip()
    
    if not topic:
        topic = "India politics OR India government"
    
    return topic, num_articles


def run_analysis(topic: str, num_articles: int, status_callback=None) -> tuple[list, str, dict]:
    """Run the full analysis pipeline and return results with a summary message."""
    try:
        # Fetch news
        if status_callback: status_callback(f"🌍 Fetching top {num_articles} articles for '{topic}'...")
        articles = fetch_news(query=topic, num_articles=num_articles)
        
        # Analyze with LLM#1
        if status_callback: status_callback("🧠 Analyzing content with GPT-4o-mini...")
        analyses = analyze_articles(articles)
        
        # Validate with LLM#2
        if status_callback: status_callback("🛡️ Validating insights with Nemotron...")
        validated_results = validate_analyses(articles, analyses)
        
        # Generate summary
        total = len(validated_results)
        positive = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "positive")
        negative = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "negative")
        neutral = sum(1 for r in validated_results if r.get("analysis", {}).get("sentiment") == "neutral")
        
        summary = f"I analyzed **{total} articles** about '{topic}'.\n\n"
        summary += f"**Sentiment breakdown:** {positive} positive, {negative} negative, {neutral} neutral.\n\n"
        
        if positive > negative:
            summary += "📈 Overall, the news coverage appears **more positive** than negative."
        elif negative > positive:
            summary += "📉 Overall, the news coverage appears **more negative** than positive."
        else:
            summary += "⚖️ The news coverage appears **balanced** between positive and negative sentiments."
        
        return validated_results, summary, {
            "query": topic,
            "articles_fetched": len(articles),
            "articles_preview": [a.get("title") for a in articles[:3]],
            "raw_analysis": analyses,
            "raw_validation": validated_results
        }
        
    except NewsFetcherError as e:
        error_msg = f"❌ Failed to fetch news: {e}"
        if "No articles found" in str(e):
            error_msg += "\n\n💡 **Tip:** Try checking for typos or using broader keywords."
        return [], error_msg, {}
    except AnalyzerError as e:
        return [], f"❌ Analysis error: {e}", {}
    except ValidatorError as e:
        return [], f"❌ Validation error: {e}", {}
    except Exception as e:
        return [], f"❌ Unexpected error: {e}", {}


def main():
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "results" not in st.session_state:
        st.session_state.results = {}
    if "num_articles" not in st.session_state:
        st.session_state.num_articles = 10
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">⚡ News Analyzer</h2>
            <p style="color: #a1a1aa; font-size: 0.9rem;">Chat with AI about news</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        
        # Search configuration
        st.markdown("### 🔧 Search Settings")
        
        # Category Selector
        categories = ["General", "Politics", "Technology", "Business", "Entertainment", "Health", "Science", "Sports"]
        st.session_state.category = st.selectbox(
            "News Category",
            options=categories,
            index=0,
            help="Filter news by category"
        )
        
        st.session_state.num_articles = st.slider(
            "Number of Articles",
            min_value=5,
            max_value=20,
            value=st.session_state.num_articles,
            help="How many articles to analyze per search"
        )
        
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        
        st.markdown("### 🎯 Quick Commands")
        if st.button("🇮🇳 India Politics News", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Analyze India politics news"})
            st.session_state.trigger_analysis = True
        
        if st.button("💻 Tech Trends", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Get 5 articles about technology"})
            st.session_state.trigger_analysis = True
            
        if st.button("💹 Stock Market", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What's happening in the stock market?"})
            st.session_state.trigger_analysis = True
            
        if st.button("🌍 Global Climate", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Search for 15 articles on climate"})
            st.session_state.trigger_analysis = True
        
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.results = {}
            st.rerun()
        
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        
        st.markdown("### ℹ️ How it works")
        st.markdown("""
        <div style="color: #a1a1aa; font-size: 0.85rem; line-height: 1.6;">
        1️⃣ <strong>You ask</strong> about any news topic<br><br>
        2️⃣ <strong>GPT-4o-mini</strong> analyzes the articles<br><br>
        3️⃣ <strong>Nemotron</strong> validates the analysis<br><br>
        4️⃣ <strong>You get</strong> sentiment & insights
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; color: #71717a; font-size: 0.8rem;">
            Built by <a href="https://cv.vivekmind.com" target="_blank" style="color: #8b5cf6;">Vivek</a>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 style="font-size: 2.2rem; background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">📰 News Analyzer AI</h1>
        <p style="color: #a1a1aa;">Ask me about any news topic and I'll analyze it for you</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    if not st.session_state.messages:
        # Show welcome message
        st.markdown("""
        <div class="welcome-box">
            <h2>👋 Hi! I'm your News Analyzer</h2>
            <p style="color: #a1a1aa; max-width: 500px; margin: 0 auto;">
                Ask me to analyze news on any topic. I use <strong>dual AI validation</strong> to give you accurate sentiment analysis.
            </p>
            <div class="example-queries">
                <div class="example-query">🇮🇳 "Analyze India politics news"</div>
                <div class="example-query">💹 "Get stock market updates"</div>
                <div class="example-query">🌍 "What's happening globally?"</div>
                <div class="example-query">💻 "5 articles about AI technology"</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display chat history
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="avatar">👤</div>
                    <div class="content"><p>{message["content"]}</p></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <div class="avatar">🤖</div>
                    <div class="content"><p>{message["content"]}</p></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show results if this message has associated results
                if f"results_{i}" in st.session_state.results:
                    results = st.session_state.results[f"results_{i}"]
                    if results:
                        st.markdown(render_stats_html(results), unsafe_allow_html=True)
                        
                        with st.expander(f"📋 View all {len(results)} articles", expanded=False):
                            for j, result in enumerate(results):
                                st.markdown(render_article_card(result, j), unsafe_allow_html=True)
                        
                        # Download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            json_data = json.dumps(results, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="📥 Download JSON",
                                data=json_data,
                                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True,
                                key=f"json_{i}"
                            )
                        with col2:
                            md_report = generate_markdown_report(results)
                            st.download_button(
                                label="📄 Download Report",
                                data=md_report,
                                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                use_container_width=True,
                                key=f"md_{i}"
                            )
                        
                        # Pipeline Inspector
                        if f"debug_{i}" in st.session_state.results:
                            render_pipeline_inspector(st.session_state.results[f"debug_{i}"])
    
    # Handle triggered analysis from buttons OR chat input
    trigger = False
    prompt = None
    
    if st.session_state.get("trigger_analysis", False):
        # Result from button click
        prompt = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
        st.session_state.trigger_analysis = False
        trigger = True
    elif user_input := st.chat_input("Ask me about any news topic..."):
        prompt = user_input
        st.session_state.messages.append({"role": "user", "content": prompt})
        trigger = True
        
    if trigger and prompt:
        # Parse the query - use sidebar settings
        topic, _ = parse_user_query(prompt)
        
        # Add category context if not General
        if "category" in st.session_state and st.session_state.category != "General":
            search_topic = f"{st.session_state.category} news {topic}"
        else:
            search_topic = topic
            
        num_articles = st.session_state.num_articles
        
        # Show processing message with detailed status
        with st.status("🚀 Starting News Analysis...", expanded=True) as status:
            results, summary, debug_data = run_analysis(search_topic, num_articles, status_callback=lambda msg: status.update(label=msg))
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
        # Add assistant response
        message_index = len(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": summary})
        
        # Store results
        if results:
            st.session_state.results[f"results_{message_index}"] = results
            st.session_state.results[f"debug_{message_index}"] = debug_data
        
        st.rerun()


def generate_markdown_report(results: list) -> str:
    """Generate markdown report from results."""
    total = len(results)
    positive = sum(1 for r in results if r.get("analysis", {}).get("sentiment") == "positive")
    negative = sum(1 for r in results if r.get("analysis", {}).get("sentiment") == "negative")
    neutral = sum(1 for r in results if r.get("analysis", {}).get("sentiment") == "neutral")
    validated = sum(1 for r in results if r.get("validation", {}).get("is_valid", False))
    
    lines = [
        "# News Analysis Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Articles:** {total}",
        "",
        "## Summary",
        "",
        f"- Positive: {positive}",
        f"- Negative: {negative}",
        f"- Neutral: {neutral}",
        f"- Validation Rate: {validated}/{total}",
        "",
        "---",
        "",
        "## Articles",
        ""
    ]
    
    for i, result in enumerate(results, 1):
        title = result.get("title", "Unknown")
        url = result.get("url", "#")
        analysis = result.get("analysis", {})
        validation = result.get("validation", {})
        
        lines.extend([
            f"### {i}. {title}",
            "",
            f"**Source:** [{result.get('source', 'Unknown')}]({url})",
            f"**Gist:** {analysis.get('gist', 'N/A')}",
            f"**Sentiment:** {analysis.get('sentiment', 'N/A').capitalize()}",
            f"**Tone:** {analysis.get('tone', 'N/A').capitalize()}",
            f"**Validated:** {'✓' if validation.get('is_valid') else '✗'} - {validation.get('validation_notes', 'N/A')[:100]}",
            "",
            "---",
            ""
        ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()
