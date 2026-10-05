import html
import os
import textwrap
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cinema",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = os.getenv(
    "API_BASE",
    "https://movie-recommendation-system-auh6.onrender.com"
).rstrip("/")

ACCENT = "#9d2436"


def render_markup(markup: str) -> None:
    """Render an HTML fragment without passing it through Markdown."""
    st.html(textwrap.dedent(markup))


# ============================================================
# GLOBAL CSS
# ============================================================

render_markup(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
    );

    :root {
        --bg: #0b0b0f;
        --surface: #121217;
        --surface-2: #18181f;
        --text: #e8e8ea;
        --muted: #9a9aa3;
        --accent: #9d2436;
        --border: rgba(255,255,255,0.10);
    }

    html,
    body,
    [class*="css"] {
        font-family: "Inter", system-ui, sans-serif;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    #MainMenu,
    header,
    footer,
    [data-testid="stHeader"],
    [data-testid="stToolbar"] {
        display: none;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 0.8rem;
        padding-bottom: 4rem;
    }

    /* ========================================================
       TOP BAR
       ======================================================== */

    .topbar {
        min-height: 68px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 30px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 18px;
    }

    .brand {
        display: inline-block;
        color: var(--text);
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-decoration: none;
        white-space: nowrap;
    }

    .brand span {
        color: var(--accent);
    }

    div[data-testid="stTextInput"] {
        margin: 0;
    }

    div[data-testid="stTextInput"] > div {
        background: transparent;
    }

    div[data-testid="stTextInput"] input {
        background: var(--surface);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 5px;
        height: 40px;
        font-size: 13px;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: rgba(157,36,54,0.75);
        box-shadow: none;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #6f7079;
    }

    /* ========================================================
       HERO
       ======================================================== */

    .hero {
        position: relative;
        min-height: 540px;
        margin: 10px 0 54px;
        overflow: hidden;
        border-radius: 6px;
        background: var(--surface);
        border: 1px solid var(--border);
    }

    .hero-image {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
    }

    .hero-fade {
        position: absolute;
        inset: 0;
        background:
            linear-gradient(
                to top,
                #0b0b0f 0%,
                rgba(11,11,15,0.92) 20%,
                rgba(11,11,15,0.48) 48%,
                rgba(11,11,15,0.08) 75%,
                rgba(11,11,15,0.02) 100%
            );
    }

    .hero-content {
        position: absolute;
        left: 42px;
        bottom: 42px;
        max-width: 650px;
        z-index: 2;
    }

    .hero-kicker {
        color: #c0c0c7;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero-title {
        color: var(--text);
        font-size: clamp(32px, 5vw, 58px);
        line-height: 1.02;
        font-weight: 700;
        letter-spacing: -0.035em;
        margin-bottom: 15px;
    }

    .hero-meta {
        display: flex;
        gap: 15px;
        color: #c5c5cb;
        font-size: 13px;
        margin-bottom: 15px;
    }

    .hero-overview {
        color: #b0b0b8;
        font-size: 14px;
        line-height: 1.65;
        max-width: 620px;
        margin-bottom: 24px;
    }

    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        border-radius: 5px;
        min-height: 40px;
        font-family: "Inter", system-ui, sans-serif;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.15s ease;
    }

    .primary-btn .stButton > button {
        background: var(--accent);
        color: white;
        border: 1px solid var(--accent);
    }

    .primary-btn .stButton > button:hover {
        background: #b02b40;
        border-color: #b02b40;
    }

    .ghost-btn .stButton > button {
        background: rgba(18,18,23,0.65);
        color: var(--text);
        border: 1px solid rgba(255,255,255,0.20);
    }

    .ghost-btn .stButton > button:hover {
        background: var(--surface-2);
        border-color: rgba(255,255,255,0.38);
    }

    /* ========================================================
       SECTIONS
       ======================================================== */

    .section {
        margin-top: 38px;
        margin-bottom: 14px;
    }

    .section-label {
        color: #d8d8dc;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }

    .section-line {
        width: 28px;
        height: 2px;
        background: var(--accent);
        margin-top: 8px;
    }

    /* ========================================================
       POSTER ROW
       ======================================================== */

    .poster-row {
        display: flex;
        gap: 13px;
        overflow-x: auto;
        padding: 5px 2px 15px;
        scroll-behavior: smooth;
    }

    .poster-row::-webkit-scrollbar {
        height: 4px;
    }

    .poster-row::-webkit-scrollbar-track {
        background: transparent;
    }

    .poster-row::-webkit-scrollbar-thumb {
        background: #303039;
        border-radius: 10px;
    }

    .movie-card-link {
        flex: 0 0 174px;
        text-decoration: none;
        color: inherit;
    }

    .movie-card {
        position: relative;
        width: 174px;
        height: 261px;
        overflow: hidden;
        background: #18181f;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 5px;
        transition:
            transform 0.18s ease,
            border-color 0.18s ease;
    }

    .movie-card:hover {
        transform: scale(1.04);
        border-color: rgba(255,255,255,0.25);
        z-index: 3;
    }

    .movie-card img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    .movie-card-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #686872;
        font-size: 11px;
        text-align: center;
        padding: 15px;
    }

    .movie-card-overlay {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 38px 11px 11px;
        background:
            linear-gradient(
                to top,
                rgba(5,5,8,0.94),
                rgba(5,5,8,0.45),
                transparent
            );
        opacity: 0;
        transition: opacity 0.18s ease;
    }

    .movie-card:hover .movie-card-overlay {
        opacity: 1;
    }

    .movie-card-title {
        color: white;
        font-size: 12px;
        line-height: 1.35;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .movie-card-meta {
        color: #b7b7be;
        font-size: 10px;
        margin-top: 4px;
    }

    /* ========================================================
       SEARCH
       ======================================================== */

    .search-heading {
        font-size: 28px;
        font-weight: 600;
        letter-spacing: -0.025em;
        margin: 34px 0 25px;
    }

    .search-title {
        color: var(--text);
        font-size: 13px;
        font-weight: 600;
        margin-top: 9px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .search-meta {
        color: var(--muted);
        font-size: 11px;
        margin-top: 4px;
    }

    /* ========================================================
       DETAIL
       ======================================================== */

    .detail-backdrop {
        position: relative;
        min-height: 550px;
        margin-top: 8px;
        margin-bottom: 38px;
        overflow: hidden;
        border-radius: 6px;
        border: 1px solid var(--border);
        background: var(--surface);
    }

    .detail-bg {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
    }

    .detail-bg-fade {
        position: absolute;
        inset: 0;
        background:
            linear-gradient(
                to right,
                rgba(11,11,15,0.98) 0%,
                rgba(11,11,15,0.83) 37%,
                rgba(11,11,15,0.35) 72%,
                rgba(11,11,15,0.18) 100%
            ),
            linear-gradient(
                to top,
                #0b0b0f 0%,
                transparent 45%
            );
    }

    .detail-content {
        position: relative;
        z-index: 2;
        display: grid;
        grid-template-columns: 220px minmax(0, 680px);
        gap: 34px;
        align-items: end;
        min-height: 550px;
        padding: 45px;
    }

    .detail-poster {
        width: 220px;
        aspect-ratio: 2 / 3;
        object-fit: cover;
        border-radius: 5px;
        border: 1px solid rgba(255,255,255,0.15);
    }

    .detail-title {
        font-size: clamp(32px, 4vw, 52px);
        line-height: 1.05;
        font-weight: 700;
        letter-spacing: -0.035em;
        margin-bottom: 14px;
        color: var(--text);
    }

    .detail-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        color: #c4c4cb;
        font-size: 13px;
        margin-bottom: 17px;
    }

    .genre-pill {
        display: inline-block;
        padding: 5px 9px;
        margin: 0 5px 5px 0;
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 4px;
        color: #c9c9cf;
        font-size: 10px;
    }

    .detail-overview {
        color: #b5b5bd;
        font-size: 14px;
        line-height: 1.7;
        max-width: 650px;
        margin-top: 15px;
    }

    /* ========================================================
       EMPTY / ERROR
       ======================================================== */

    .empty-state {
        padding: 55px 20px;
        text-align: center;
        color: var(--muted);
        font-size: 13px;
        border-top: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
    }

    .error-state {
        padding: 18px;
        margin: 25px 0;
        color: #c4c4ca;
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 2px solid var(--accent);
        border-radius: 5px;
        font-size: 13px;
    }

    /* ========================================================
       RESPONSIVE
       ======================================================== */

    @media (max-width: 800px) {

        .block-container {
            padding-left: 15px;
            padding-right: 15px;
        }

        .topbar {
            align-items: center;
            gap: 15px;
        }

        .brand {
            font-size: 15px;
        }

        .hero {
            min-height: 480px;
        }

        .hero-content {
            left: 23px;
            right: 23px;
            bottom: 27px;
        }

        .detail-content {
            grid-template-columns: 130px 1fr;
            gap: 20px;
            padding: 25px;
        }

        .detail-poster {
            width: 130px;
        }

        .detail-backdrop {
            min-height: 500px;
        }

        .movie-card-link {
            flex-basis: 145px;
        }

        .movie-card {
            width: 145px;
            height: 218px;
        }
    }

    @media (max-width: 520px) {

        .topbar {
            display: block;
            padding: 12px 0;
        }

        .brand {
            margin-bottom: 12px;
        }

        .hero {
            min-height: 500px;
        }

        .hero-title {
            font-size: 34px;
        }

        .detail-content {
            grid-template-columns: 1fr;
            align-items: start;
        }

        .detail-poster {
            width: 145px;
        }

        .detail-backdrop {
            min-height: auto;
        }
    }

    </style>
    """
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

if "search_query" not in st.session_state:
    st.session_state.search_query = ""


# ============================================================
# QUERY PARAMETERS
# ============================================================

def sync_from_url():

    try:

        page = st.query_params.get("page")

        if page in {"home", "search", "movie"}:
            st.session_state.page = page

        if page == "home":
            st.session_state.selected_movie_id = None
            st.session_state.search_query = ""
            st.session_state.top_search = ""

        movie_id = st.query_params.get("id")

        if movie_id:

            try:
                st.session_state.selected_movie_id = int(movie_id)

            except ValueError:
                st.session_state.selected_movie_id = None

        query = st.query_params.get("q")

        if query:
            st.session_state.search_query = query

    except Exception:
        pass


sync_from_url()


# ============================================================
# NAVIGATION
# ============================================================

def go_home():

    st.session_state.page = "home"
    st.session_state.selected_movie_id = None
    st.session_state.search_query = ""

    st.query_params.clear()
    st.query_params["page"] = "home"


def go_movie(movie_id: int):

    st.session_state.page = "movie"
    st.session_state.selected_movie_id = int(movie_id)

    st.query_params.clear()
    st.query_params["page"] = "movie"
    st.query_params["id"] = str(movie_id)


def go_search(query: str):

    query = query.strip()

    if not query:
        go_home()
        return

    st.session_state.page = "search"
    st.session_state.search_query = query
    st.session_state.selected_movie_id = None

    st.query_params.clear()
    st.query_params["page"] = "search"
    st.query_params["q"] = query


def open_search_from_input():

    query = st.session_state.get(
        "top_search",
        ""
    ).strip()

    if query:
        go_search(query)
    else:
        go_home()


# ============================================================
# API HELPERS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def api_get(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 15,
) -> Any:

    response = requests.get(
        f"{API_BASE}{endpoint}",
        params=params,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=300, show_spinner=False)
def get_home_movies(
    category: str,
    limit: int = 18
) -> List[Dict[str, Any]]:

    return api_get(
        "/home",
        {
            "category": category,
            "limit": limit,
        },
    )


@st.cache_data(ttl=120, show_spinner=False)
def search_movies(
    query: str
) -> Dict[str, Any]:

    return api_get(
        "/tmdb/search",
        {
            "query": query,
        },
    )


@st.cache_data(ttl=600, show_spinner=False)
def get_movie_details(
    movie_id: int
) -> Dict[str, Any]:

    return api_get(
        f"/movie/id/{movie_id}"
    )


@st.cache_data(ttl=600, show_spinner=False)
def get_movie_bundle(
    movie_id: int,
    query: str,
) -> Dict[str, Any]:

    return api_get(
        "/movie/search",
        {
            "query": query,
            "tmdb_id": movie_id,
            "tfidf_top_n": 12,
            "genre_limit": 12,
        },
        timeout=90,
    )


# ============================================================
# DATA HELPERS
# ============================================================

def safe_text(value: Any) -> str:

    if value is None:
        return ""

    return str(value).strip()


def movie_year(
    movie: Dict[str, Any]
) -> str:

    release_date = safe_text(
        movie.get("release_date")
    )

    if len(release_date) >= 4:
        return release_date[:4]

    return ""


def movie_rating(
    movie: Dict[str, Any]
) -> str:

    rating = movie.get("vote_average")

    if rating is None:
        return ""

    try:
        return f"{float(rating):.1f}"

    except (TypeError, ValueError):
        return ""


def truncate(
    text: str,
    max_length: int
) -> str:

    text = safe_text(text)

    if len(text) <= max_length:
        return text

    return text[:max_length].rstrip() + "..."


# ============================================================
# TOP BAR
# ============================================================

def render_topbar():

    left, right = st.columns(
        [1.1, 2.2],
        vertical_alignment="center"
    )

    with left:

        render_markup(
            '<a class="brand" href="?page=home" target="_self" '
            'aria-label="Go to home">CINEMA<span>.</span></a>'
        )

    with right:

        st.text_input(
            "Search movies",
            placeholder="Search movies...",
            label_visibility="collapsed",
            key="top_search",
            on_change=open_search_from_input,
        )


# ============================================================
# MOVIE CARD
# ============================================================

def movie_card_html(
    movie: Dict[str, Any]
) -> str:

    movie_id = movie.get("tmdb_id")
    title = safe_text(
        movie.get("title")
    )

    poster = movie.get("poster_url")

    year = movie_year(movie)
    rating = movie_rating(movie)

    meta = []

    if year:
        meta.append(year)

    if rating:
        meta.append(f"TMDB {rating}")

    meta_text = " · ".join(meta)

    if poster:

        image_html = f"""
        <img
            src="{html.escape(str(poster), quote=True)}"
            alt="{html.escape(title, quote=True)} poster"
            loading="lazy"
        >
        """

    else:

        image_html = """
        <div class="movie-card-placeholder">
            Poster unavailable
        </div>
        """

    if movie_id:

        href = (
            f"?page=movie&id="
            f"{html.escape(str(movie_id), quote=True)}"
        )

    else:

        href = "#"

    return f"""
    <a
        class="movie-card-link"
        href="{href}"
        target="_self"
        aria-label="Open {html.escape(title, quote=True)}"
    >

        <div class="movie-card">

            {image_html}

            <div class="movie-card-overlay">

                <div class="movie-card-title">
                    {html.escape(title)}
                </div>

                <div class="movie-card-meta">
                    {html.escape(meta_text)}
                </div>

            </div>

        </div>

    </a>
    """


# ============================================================
# POSTER ROW
# ============================================================

def render_poster_row(
    label: str,
    movies: List[Dict[str, Any]]
):

    if not movies:
        return

    cards = "".join(
        movie_card_html(movie)
        for movie in movies
    )

    render_markup(
        f"""
        <div class="section">

            <div class="section-label">
                {html.escape(label)}
            </div>

            <div class="section-line"></div>

        </div>

        <div class="poster-row">

            {cards}

        </div>
        """
    )


# ============================================================
# HERO
# ============================================================

def render_hero(
    movie: Dict[str, Any]
):

    title = safe_text(
        movie.get("title")
    )

    backdrop = movie.get(
        "backdrop_url"
    )

    overview = truncate(
        safe_text(movie.get("overview")),
        280
    )

    year = movie_year(movie)
    rating = movie_rating(movie)

    movie_id = movie.get(
        "tmdb_id"
    )

    # IMPORTANT:
    # Use <img> instead of CSS background-image.
    # This prevents HTML from being displayed as text.

    if backdrop:

        hero_image = f"""
        <img
            class="hero-image"
            src="{html.escape(str(backdrop), quote=True)}"
            alt=""
        >
        """

    else:

        hero_image = ""

    meta = []

    if year:
        meta.append(year)

    if rating:
        meta.append(
            f"TMDB {rating}"
        )

    meta_html = " · ".join(
        html.escape(item)
        for item in meta
    )

    render_markup(
        f"""
        <div class="hero">

            {hero_image}

            <div class="hero-fade"></div>

            <div class="hero-content">

                <div class="hero-kicker">
                    Trending now
                </div>

                <div class="hero-title">
                    {html.escape(title)}
                </div>

                <div class="hero-meta">
                    {meta_html}
                </div>

                <div class="hero-overview">
                    {html.escape(overview)}
                </div>

            </div>

        </div>
        """
    )

    col1, col2, _ = st.columns(
        [1, 1, 4],
        gap="small"
    )

    with col1:

        render_markup(
            '<div class="primary-btn">'
        )

        if st.button(
            "View details",
            key=f"hero_details_{movie_id}",
            use_container_width=True,
        ):

            go_movie(
                int(movie_id)
            )

            st.rerun()

        render_markup(
            "</div>"
        )

    with col2:

        render_markup(
            '<div class="ghost-btn">'
        )

        if st.button(
            "Similar movies",
            key=f"hero_similar_{movie_id}",
            use_container_width=True,
        ):

            go_movie(
                int(movie_id)
            )

            st.rerun()

        render_markup(
            "</div>"
        )


# ============================================================
# HOME
# ============================================================

def render_home():

    try:

        trending = get_home_movies(
            "trending",
            30
        )

        popular = get_home_movies(
            "popular",
            18
        )

        top_rated = get_home_movies(
            "top_rated",
            18
        )

        upcoming = get_home_movies(
            "upcoming",
            18
        )

    except requests.RequestException as exc:

        render_backend_error(exc)
        return

    if not trending:

        render_markup(
            """
            <div class="empty-state">
                No movies are available right now.
            </div>
            """
        )

        return

    hero_movie = trending[0]

    try:

        details = get_movie_details(
            int(hero_movie["tmdb_id"])
        )

        hero_movie = {
            **hero_movie,
            **details,
        }

    except (
        requests.RequestException,
        KeyError,
        ValueError
    ):

        pass

    render_hero(
        hero_movie
    )

    render_poster_row(
        "Trending",
        trending
    )

    render_poster_row(
        "Popular",
        popular
    )

    render_poster_row(
        "Top Rated",
        top_rated
    )

    render_poster_row(
        "Upcoming",
        upcoming
    )


# ============================================================
# SEARCH
# ============================================================

def render_search():

    query = (
        st.session_state.search_query
        .strip()
    )

    if not query:

        go_home()
        st.rerun()

    render_markup(
        f"""
        <div class="search-heading">
            Results for "{html.escape(query)}"
        </div>
        """
    )

    try:

        data = search_movies(query)

    except requests.RequestException as exc:

        render_backend_error(exc)
        return

    results = data.get(
        "results",
        []
    )

    if not results:

        render_markup(
            """
            <div class="empty-state">
                No movies found for this search.
            </div>
            """
        )

        return

    cols_per_row = 6

    for start in range(
        0,
        len(results),
        cols_per_row
    ):

        row = results[
            start:start + cols_per_row
        ]

        columns = st.columns(
            len(row),
            gap="small"
        )

        for column, movie in zip(
            columns,
            row
        ):

            with column:

                poster = movie.get(
                    "poster_url"
                )

                title = safe_text(
                    movie.get("title")
                )

                if poster:

                    st.image(
                        poster,
                        use_column_width=True,
                    )

                else:

                    render_markup(
                        """
                        <div
                            class="movie-card-placeholder"
                            style="
                                aspect-ratio:2/3;
                                background:#18181f;
                                border:1px solid rgba(255,255,255,0.08);
                            "
                        >
                            Poster unavailable
                        </div>
                        """
                    )

                movie_year_value = movie_year(
                    movie
                )

                movie_rating_value = movie_rating(
                    movie
                )

                if movie_year_value and movie_rating_value:

                    meta = (
                        f"{movie_year_value}"
                        f" · TMDB "
                        f"{movie_rating_value}"
                    )

                elif movie_year_value:

                    meta = movie_year_value

                elif movie_rating_value:

                    meta = (
                        f"TMDB "
                        f"{movie_rating_value}"
                    )

                else:

                    meta = ""

                render_markup(
                    f"""
                    <div class="search-title">
                        {html.escape(title)}
                    </div>

                    <div class="search-meta">
                        {html.escape(meta)}
                    </div>
                    """
                )

                if st.button(
                    "View",
                    key=f"search_{movie.get('tmdb_id')}",
                    use_container_width=True,
                ):

                    go_movie(
                        int(movie["tmdb_id"])
                    )

                    st.rerun()


# ============================================================
# DETAIL PAGE
# ============================================================

def render_detail(
    movie_id: int
):

    try:

        details = get_movie_details(
            movie_id
        )

    except requests.RequestException as exc:

        render_backend_error(exc)
        return

    title = safe_text(
        details.get("title")
    )

    overview = safe_text(
        details.get("overview")
    )

    backdrop = details.get(
        "backdrop_url"
    )

    poster = details.get(
        "poster_url"
    )

    year = movie_year(
        details
    )

    rating = movie_rating(
        details
    )

    genres = details.get(
        "genres"
    ) or []

    # --------------------------------------------------------
    # GENRES
    # --------------------------------------------------------

    genre_html = "".join(
        f"""
        <span class="genre-pill">
            {html.escape(
                safe_text(
                    genre.get("name")
                )
            )}
        </span>
        """
        for genre in genres
        if genre.get("name")
    )

    # --------------------------------------------------------
    # BACKDROP
    # --------------------------------------------------------

    if backdrop:

        backdrop_html = f"""
        <img
            class="detail-bg"
            src="{html.escape(str(backdrop), quote=True)}"
            alt=""
        >
        """

    else:

        backdrop_html = ""

    # --------------------------------------------------------
    # POSTER
    # --------------------------------------------------------

    if poster:

        poster_html = f"""
        <img
            class="detail-poster"
            src="{html.escape(str(poster), quote=True)}"
            alt="{html.escape(title, quote=True)} poster"
        >
        """

    else:

        poster_html = """
        <div
            class="detail-poster movie-card-placeholder"
            style="background:#18181f;"
        >
            Poster unavailable
        </div>
        """

    # --------------------------------------------------------
    # META
    # --------------------------------------------------------

    meta_parts = []

    if year:
        meta_parts.append(year)

    if rating:
        meta_parts.append(
            f"TMDB {rating}"
        )

    meta_html = " · ".join(
        html.escape(part)
        for part in meta_parts
    )

    # --------------------------------------------------------
    # DETAIL CONTENT
    # --------------------------------------------------------

    render_markup(
        f"""
        <div class="detail-backdrop">

            {backdrop_html}

            <div class="detail-bg-fade"></div>

            <div class="detail-content">

                <div>
                    {poster_html}
                </div>

                <div>

                    <div class="detail-title">
                        {html.escape(title)}
                    </div>

                    <div class="detail-meta">
                        {meta_html}
                    </div>

                    <div>
                        {genre_html}
                    </div>

                    <div class="detail-overview">
                        {html.escape(
                            overview
                            if overview
                            else
                            "No overview is available for this title."
                        )}
                    </div>

                </div>

            </div>

        </div>
        """
    )

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if st.button(
        "Back",
        key="detail_back"
    ):

        go_home()
        st.rerun()

    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    try:

        with st.spinner("Finding similar movies…"):
            bundle = get_movie_bundle(movie_id, title)

    except requests.RequestException as exc:

        render_backend_error(
            exc,
            fallback="Recommendations are temporarily unavailable.",
        )

        return

    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    tfidf_recommendations = []

    for item in bundle.get(
        "tfidf_recommendations",
        []
    ):

        tmdb_movie = item.get(
            "tmdb"
        )

        if tmdb_movie:

            tfidf_recommendations.append(
                tmdb_movie
            )

    # --------------------------------------------------------
    # GENRE
    # --------------------------------------------------------

    genre_recommendations = bundle.get(
        "genre_recommendations",
        []
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    render_poster_row(
        "More like this",
        tfidf_recommendations
    )

    genre_name = "this genre"

    if genres:

        genre_name = safe_text(
            genres[0].get("name")
        )

    render_poster_row(
        f"Because you are exploring {genre_name}",
        genre_recommendations
    )


# ============================================================
# ERROR HANDLING
# ============================================================

def render_backend_error(
    error: Optional[requests.RequestException] = None,
    fallback: str = "The movie service is temporarily unavailable.",
):

    message = fallback

    if error is not None and error.response is not None:

        try:
            detail = error.response.json().get("detail")

            if detail:
                message = str(detail)

        except (ValueError, AttributeError):
            pass

    render_markup(
        f'<div class="error-state">{html.escape(message)}</div>'
    )

    if st.button(
        "Retry",
        key="backend_retry"
    ):

        st.cache_data.clear()
        st.rerun()


# ============================================================
# TOP BAR
# ============================================================

render_topbar()


# ============================================================
# PAGE ROUTING
# ============================================================

if st.session_state.page == "movie":

    movie_id = (
        st.session_state.selected_movie_id
    )

    if movie_id:

        render_detail(
            int(movie_id)
        )

    else:

        go_home()
        st.rerun()

elif st.session_state.page == "search":

    render_search()

else:

    render_home()
