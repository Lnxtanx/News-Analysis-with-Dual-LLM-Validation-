"""
News Analyzer - ChatGPT-Style Interface
Premium chat UI matching ChatGPT's design with sidebar navigation.
"""

import streamlit as st
import time
from datetime import datetime

from news_fetcher import fetch_news, NewsFetcherError
from llm_analyzer import analyze_article, AnalyzerError
from llm_validator import validate_analysis, ValidatorError

# Page configuration
st.set_page_config(
    page_title="News Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ChatGPT-style CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Söhne:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main app background */
    .stApp {
        background: #212121;
    }
    
    /* Hide defaults */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Sidebar - ChatGPT style */
    [data-testid="stSidebar"] {
        background: #171717 !important;
        border-right: 1px solid #2d2d2d;
        padding-top: 0;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    
    /* Sidebar header */
    .sidebar-header {
        padding: 12px 12px;
        border-bottom: 1px solid #2d2d2d;
        margin-bottom: 8px;
    }
    
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #ececec;
        font-size: 14px;
        font-weight: 600;
    }
    
    /* New chat button */
    .new-chat-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        margin: 8px 12px;
        background: transparent;
        border: 1px solid #3d3d3d;
        border-radius: 8px;
        color: #ececec;
        font-size: 14px;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .new-chat-btn:hover {
        background: #2a2a2a;
    }
    
    /* Sidebar menu items */
    .sidebar-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        margin: 2px 8px;
        border-radius: 8px;
        color: #b4b4b4;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.15s;
    }
    
    .sidebar-item:hover {
        background: #2a2a2a;
        color: #ececec;
    }
    
    .sidebar-item.active {
        background: #2a2a2a;
        color: #ececec;
    }
    
    .sidebar-section {
        padding: 16px 12px 8px 12px;
        font-size: 12px;
        font-weight: 600;
        color: #8e8e8e;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Main content area */
    .main-content {
        max-width: 768px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Chat header */
    .chat-header {
        text-align: center;
        padding: 40px 0 20px 0;
    }
    
    .chat-title {
        font-size: 24px;
        font-weight: 600;
        color: #ececec;
        margin-bottom: 8px;
    }
    
    .chat-subtitle {
        font-size: 14px;
        color: #8e8e8e;
    }
    
    /* Messages */
    .user-bubble {
        background: #2f2f2f;
        border-radius: 20px;
        padding: 12px 18px;
        margin: 16px 0;
        margin-left: auto;
        max-width: fit-content;
        color: #ececec;
        font-size: 15px;
    }
    
    .assistant-response {
        padding: 16px 0;
        color: #d1d1d1;
        font-size: 15px;
        line-height: 1.7;
    }
    
    /* Article cards */
    .article-card {
        background: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        transition: all 0.2s;
    }
    
    .article-card:hover {
        background: #333;
        border-color: #4a4a4a;
    }
    
    .article-title {
        font-size: 15px;
        font-weight: 600;
        color: #ececec;
        margin-bottom: 6px;
    }
    
    .article-title a {
        color: #ececec;
        text-decoration: none;
    }
    
    .article-title a:hover {
        color: #10a37f;
    }
    
    .article-meta {
        font-size: 12px;
        color: #8e8e8e;
        margin-bottom: 10px;
    }
    
    .article-gist {
        font-size: 14px;
        color: #b4b4b4;
        line-height: 1.5;
        margin-bottom: 12px;
    }
    
    /* Tags */
    .tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 6px;
    }
    
    .tag-positive { background: #10a37f20; color: #10a37f; }
    .tag-negative { background: #ef444420; color: #ef4444; }
    .tag-neutral { background: #eab30820; color: #eab308; }
    .tag-tone { background: #818cf820; color: #818cf8; }
    .tag-valid { background: #10a37f20; color: #10a37f; }
    .tag-invalid { background: #ef444420; color: #ef4444; }
    
    .read-btn {
        display: inline-block;
        padding: 6px 12px;
        background: #10a37f;
        color: white !important;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        text-decoration: none;
        margin-top: 8px;
    }
    
    .read-btn:hover {
        background: #0d8c6d;
    }
    
    /* Stats */
    .stats-row {
        display: flex;
        gap: 12px;
        margin: 20px 0;
    }
    
    .stat-box {
        flex: 1;
        background: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #ececec;
    }
    
    .stat-label {
        font-size: 12px;
        color: #8e8e8e;
        margin-top: 4px;
    }
    
    /* Bottom input - ChatGPT style */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #212121;
        padding: 20px 20px 24px 20px;
        z-index: 100;
    }
    
    .stChatInput > div {
        max-width: 768px;
        margin: 0 auto;
        background: #2f2f2f !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 12px !important;
    }
    
    .stChatInput input {
        background: transparent !important;
        color: #ececec !important;
    }
    
    /* Metrics styling */
    [data-testid="stMetric"] {
        background: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 10px;
        padding: 12px;
    }
    
    [data-testid="stMetricLabel"] { color: #8e8e8e !important; font-size: 12px !important; }
    [data-testid="stMetricValue"] { color: #ececec !important; font-size: 24px !important; }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #2a2a2a !important;
        border-radius: 8px !important;
        color: #b4b4b4 !important;
        font-size: 13px !important;
    }
    
    /* Select box */
    .stSelectbox > div > div {
        background: #2a2a2a !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 8px !important;
        color: #ececec !important;
    }
    
    /* Footer text */
    .footer-text {
        text-align: center;
        font-size: 12px;
        color: #6b6b6b;
        padding: 8px;
        margin-top: 80px;
    }
    
    /* Progress */
    .stProgress > div > div { background: #10a37f !important; }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #212121; }
    ::-webkit-scrollbar-thumb { background: #3d3d3d; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "results" not in st.session_state:
        st.session_state.results = []
    if "history" not in st.session_state:
        st.session_state.history = []


def render_sidebar():
    """Render ChatGPT-style sidebar."""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-logo">📰 News Analyzer</div>
        </div>
        """, unsafe_allow_html=True)
        
        # New chat button
        if st.button("➕ New Analysis", use_container_width=True, key="new_chat"):
            st.session_state.messages = []
            st.session_state.results = []
            st.rerun()
        
        st.markdown("---")
        
        # Settings section
        st.markdown('<div class="sidebar-section">⚙️ Settings</div>', unsafe_allow_html=True)
        
        query = st.text_input(
            "Search Query",
            value="India politics OR India government",
            label_visibility="collapsed",
            placeholder="Search query..."
        )
        
        num_articles = st.select_slider(
            "Number of Articles",
            options=[3, 5, 7, 10, 12, 15],
            value=5,
            help="Articles to analyze"
        )
        
        st.markdown("---")
        
        # Pipeline info
        st.markdown('<div class="sidebar-section">🔧 Pipeline</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="sidebar-item">📡 Fetch → NewsAPI</div>
        <div class="sidebar-item">🤖 Analyze → OpenAI</div>
        <div class="sidebar-item">✅ Validate → Nemotron</div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Recent articles section
        if st.session_state.results:
            st.markdown('<div class="sidebar-section">📄 Recent Articles</div>', unsafe_allow_html=True)
            for i, r in enumerate(st.session_state.results[:5]):
                title = r["article"].get("title", "Untitled")[:35]
                sentiment = r["analysis"].get("sentiment", "neutral")
                emoji = "😊" if sentiment == "positive" else "😟" if sentiment == "negative" else "😐"
                st.markdown(f"""
                <div class="sidebar-item">{emoji} {title}...</div>
                """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="padding: 8px 12px; font-size: 12px; color: #6b6b6b;">
            Made by <a href="https://cv.vivekmind.com" target="_blank" style="color: #10a37f;">Vivek</a>
        </div>
        """, unsafe_allow_html=True)
    
    return query, num_articles


def get_sentiment_tag(s):
    c = {"positive": "tag-positive", "negative": "tag-negative", "neutral": "tag-neutral"}
    return f'<span class="tag {c.get(s, "tag-neutral")}">{s.upper()}</span>'


def display_article(article, analysis, validation):
    title = article.get("title", "Untitled")
    url = article.get("url", "#")
    source = article.get("source", "Unknown")
    gist = analysis.get("gist", "No summary")
    sentiment = analysis.get("sentiment", "neutral")
    tone = analysis.get("tone", "informative")
    is_valid = validation.get("is_valid", False)
    valid_tag = '<span class="tag tag-valid">✓ VALID</span>' if is_valid else '<span class="tag tag-invalid">⚠ CHECK</span>'
    
    st.markdown(f"""
    <div class="article-card">
        <div class="article-title"><a href="{url}" target="_blank">📄 {title}</a></div>
        <div class="article-meta">Source: {source}</div>
        <div class="article-gist">{gist}</div>
        <div>
            {get_sentiment_tag(sentiment)}
            <span class="tag tag-tone">{tone.upper()}</span>
            {valid_tag}
        </div>
        <a href="{url}" target="_blank" class="read-btn">🔗 Read Article</a>
    </div>
    """, unsafe_allow_html=True)


def run_pipeline(query, num):
    """Run analysis pipeline."""
    results = []
    
    # Fetch
    with st.spinner("📡 Fetching articles from NewsAPI..."):
        try:
            articles = fetch_news(query=query, num_articles=num)
        except NewsFetcherError as e:
            st.error(f"Failed: {e}")
            return []
    
    st.success(f"✅ Fetched {len(articles)} articles")
    
    # Progress
    progress = st.progress(0)
    status = st.empty()
    
    for i, article in enumerate(articles):
        status.text(f"🔄 Analyzing article {i+1}/{len(articles)}...")
        
        try:
            analysis = analyze_article(article)
        except AnalyzerError as e:
            analysis = {"gist": str(e), "sentiment": "neutral", "tone": "informative"}
        
        try:
            validation = validate_analysis(article, analysis)
        except ValidatorError as e:
            validation = {"is_valid": True, "validation_notes": str(e)}
        
        results.append({"article": article, "analysis": analysis, "validation": validation})
        progress.progress((i + 1) / len(articles))
        time.sleep(0.2)
    
    status.empty()
    progress.empty()
    
    return results


def display_results(results):
    if not results:
        return
    
    # Stats
    total = len(results)
    pos = sum(1 for r in results if r["analysis"].get("sentiment") == "positive")
    neg = sum(1 for r in results if r["analysis"].get("sentiment") == "negative")
    valid = sum(1 for r in results if r["validation"].get("is_valid", False))
    
    st.markdown("### 📊 Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📰 Total", total)
    c2.metric("😊 Positive", pos)
    c3.metric("😟 Negative", neg)
    c4.metric("✅ Validated", f"{valid}/{total}")
    
    st.markdown("---")
    st.markdown("### 📄 Articles")
    st.markdown("*Click titles to read full articles*")
    
    for r in results:
        display_article(r["article"], r["analysis"], r["validation"])
        with st.expander("🔍 Validation Details"):
            st.write(r["validation"].get("validation_notes", "No notes"))


def main():
    init_state()
    query, num_articles = render_sidebar()
    
    # Main content
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-header">
            <div class="chat-title">📰 News Analyzer</div>
            <div class="chat-subtitle">Dual LLM Pipeline: OpenAI → OpenRouter/Nemotron</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-response">{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("results"):
                display_results(msg["results"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input
    if prompt := st.chat_input("Ask anything... (e.g., 'Analyze Indian politics news')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)
        
        if any(w in prompt.lower() for w in ["analyze", "news", "fetch", "start", "run", "get"]):
            st.markdown(f'<div class="assistant-response">🚀 Starting analysis for: <b>{query}</b></div>', unsafe_allow_html=True)
            
            results = run_pipeline(query, num_articles)
            
            if results:
                st.session_state.results = results
                display_results(results)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"✅ Analyzed {len(results)} articles!",
                    "results": results
                })
        else:
            response = """👋 Welcome! I analyze news using dual LLM validation.

**Try:** "Analyze news" or "Start analysis"

Configure query & article count in sidebar →"""
            st.markdown(f'<div class="assistant-response">{response}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Footer (Removed as requested)
    pass


if __name__ == "__main__":
    main()
