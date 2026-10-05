import asyncio
import os
import pickle
from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import httpx

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

API_KEY = os.getenv("API_KEY")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"
TMDB_IMG_1280 = "https://image.tmdb.org/t/p/w1280"

if not API_KEY:
    raise RuntimeError(
        "API_KEY is missing. Add API_KEY=your_tmdb_key to .env"
    )


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Movie Recommendation API",
    description="Content-based movie recommendation system using TF-IDF and TMDB.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DF_PATH = os.path.join(
    BASE_DIR,
    "df.pkl"
)

INDICES_PATH = os.path.join(
    BASE_DIR,
    "indices.pkl"
)

TFIDF_MATRIX_PATH = os.path.join(
    BASE_DIR,
    "tfidf_matrix.pkl"
)

TFIDF_PATH = os.path.join(
    BASE_DIR,
    "tfidf.pkl"
)


# ============================================================
# GLOBAL MODEL OBJECTS
# ============================================================

df: Optional[pd.DataFrame] = None

indices_obj: Any = None

tfidf_matrix: Any = None

tfidf_obj: Any = None

TITLE_TO_IDX: Dict[str, int] = {}


# ============================================================
# PYDANTIC MODELS
# ============================================================

class TMDBMovieCard(BaseModel):
    tmdb_id: int
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None


class TMDBMovieDetails(BaseModel):
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genres: List[dict] = []


class TFIDFRecItem(BaseModel):
    title: str
    score: float
    tmdb: Optional[TMDBMovieCard] = None


class SearchBundleResponse(BaseModel):
    query: str
    movie_details: TMDBMovieDetails
    tfidf_recommendations: List[TFIDFRecItem]
    genre_recommendations: List[TMDBMovieCard]


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_title(title: str) -> str:
    return str(title).strip().lower()


def make_poster_url(
    poster_path: Optional[str]
) -> Optional[str]:

    if not poster_path:
        return None

    return f"{TMDB_IMG_500}{poster_path}"


def make_backdrop_url(
    backdrop_path: Optional[str]
) -> Optional[str]:

    if not backdrop_path:
        return None

    return f"{TMDB_IMG_1280}{backdrop_path}"


# ============================================================
# TMDB REQUEST HELPER
# ============================================================

async def tmdb_get(
    endpoint: str,
    params: Optional[dict] = None,
) -> dict:

    query_params = {}

    if params:
        query_params.update(params)

    query_params["api_key"] = API_KEY

    url = f"{TMDB_BASE}{endpoint}"

    try:

        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            response = await client.get(
                url,
                params=query_params,
            )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail="Unable to connect to TMDB.",
        ) from exc

    if response.status_code != 200:

        try:
            error_data = response.json()
            error_message = error_data.get(
                "status_message",
                "TMDB request failed.",
            )
        except Exception:
            error_message = "TMDB request failed."

        raise HTTPException(
            status_code=502,
            detail=error_message,
        )

    try:

        return response.json()

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail="TMDB returned an invalid response.",
        ) from exc


# ============================================================
# TMDB MOVIE -> CARD
# ============================================================

def tmdb_to_card(
    movie: dict
) -> TMDBMovieCard:

    movie_id = movie.get("id")

    if movie_id is None:

        raise ValueError(
            "TMDB movie does not contain an id."
        )

    title = (
        movie.get("title")
        or movie.get("name")
        or "Unknown title"
    )

    vote_average = movie.get(
        "vote_average"
    )

    if vote_average is not None:

        try:
            vote_average = float(
                vote_average
            )
        except (
            TypeError,
            ValueError,
        ):
            vote_average = None

    return TMDBMovieCard(
        tmdb_id=int(movie_id),
        title=str(title),
        poster_url=make_poster_url(
            movie.get("poster_path")
        ),
        release_date=movie.get(
            "release_date"
        ),
        vote_average=vote_average,
    )


# ============================================================
# MOVIE DETAILS
# ============================================================

async def get_movie_details(
    tmdb_id: int
) -> TMDBMovieDetails:

    movie = await tmdb_get(
        f"/movie/{tmdb_id}"
    )

    movie_id = movie.get("id")

    if movie_id is None:

        raise HTTPException(
            status_code=404,
            detail="Movie not found.",
        )

    return TMDBMovieDetails(
        tmdb_id=int(movie_id),
        title=str(
            movie.get("title")
            or ""
        ),
        overview=movie.get(
            "overview"
        ),
        release_date=movie.get(
            "release_date"
        ),
        poster_url=make_poster_url(
            movie.get("poster_path")
        ),
        backdrop_url=make_backdrop_url(
            movie.get("backdrop_path")
        ),
        genres=movie.get(
            "genres"
        ) or [],
    )


# ============================================================
# TMDB SEARCH
# ============================================================

async def tmdb_search(
    query: str,
    page: int = 1,
) -> List[TMDBMovieCard]:

    data = await tmdb_get(
        "/search/movie",
        {
            "query": query,
            "page": page,
            "include_adult": False,
        },
    )

    results = []

    for movie in data.get(
        "results",
        []
    ):

        try:

            results.append(
                tmdb_to_card(movie)
            )

        except Exception:

            continue

    return results


async def tmdb_first_search(
    query: str
) -> TMDBMovieCard:

    results = await tmdb_search(
        query
    )

    if not results:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Movie not found on TMDB: '{query}'"
            ),
        )

    return results[0]


# ============================================================
# BUILD LOCAL TITLE INDEX
# ============================================================

def build_title_to_idx_map(
    indices: Any
) -> Dict[str, int]:

    result: Dict[str, int] = {}

    try:

        items = indices.items()

    except AttributeError as exc:

        raise RuntimeError(
            "indices.pkl must contain a dictionary "
            "or pandas Series-like object."
        ) from exc

    for title, index in items:

        try:

            result[
                normalize_title(title)
            ] = int(index)

        except (
            TypeError,
            ValueError,
        ):

            continue

    if not result:

        raise RuntimeError(
            "No valid movie titles were found in indices.pkl."
        )

    return result


# ============================================================
# FIND LOCAL MOVIE INDEX
# ============================================================

def get_local_movie_index(
    title: str
) -> int:

    normalized = normalize_title(
        title
    )

    if normalized not in TITLE_TO_IDX:

        raise HTTPException(
            status_code=404,
            detail=(
                f"'{title}' is not available "
                "in the local recommendation dataset."
            ),
        )

    return int(
        TITLE_TO_IDX[normalized]
    )


# ============================================================
# TF-IDF RECOMMENDATION
# ============================================================

def tfidf_recommend_titles(
    query_title: str,
    top_n: int = 10,
) -> List[Tuple[str, float]]:

    if df is None:

        raise HTTPException(
            status_code=500,
            detail="Movie dataset is not loaded.",
        )

    if tfidf_matrix is None:

        raise HTTPException(
            status_code=500,
            detail="TF-IDF matrix is not loaded.",
        )

    if "title" not in df.columns:

        raise HTTPException(
            status_code=500,
            detail="Movie dataset does not contain a title column.",
        )

    idx = get_local_movie_index(
        query_title
    )

    if idx < 0 or idx >= tfidf_matrix.shape[0]:

        raise HTTPException(
            status_code=500,
            detail="Invalid TF-IDF index.",
        )

    query_vector = tfidf_matrix[idx]

    # The TF-IDF vectors are L2-normalized by sklearn's
    # TfidfVectorizer by default, so their dot product is
    # equivalent to cosine similarity.
    scores = (
        tfidf_matrix @ query_vector.T
    ).toarray().ravel()

    ranked_indices = np.argsort(
        -scores
    )

    recommendations = []

    for movie_idx in ranked_indices:

        movie_idx = int(
            movie_idx
        )

        # Skip the movie itself.
        if movie_idx == idx:
            continue

        try:

            movie_title = str(
                df.iloc[movie_idx]["title"]
            ).strip()

        except Exception:

            continue

        if not movie_title:
            continue

        recommendations.append(
            (
                movie_title,
                float(
                    scores[movie_idx]
                ),
            )
        )

        if len(
            recommendations
        ) >= top_n:

            break

    return recommendations


# ============================================================
# ATTACH TMDB INFORMATION
# ============================================================

async def attach_tmdb_card(
    title: str
) -> Optional[TMDBMovieCard]:

    try:

        return await tmdb_first_search(
            title
        )

    except HTTPException:

        return None

    except Exception:

        return None


# ============================================================
# LOAD MODELS AT STARTUP
# ============================================================

@app.on_event("startup")
def load_models():

    global df
    global indices_obj
    global tfidf_matrix
    global tfidf_obj
    global TITLE_TO_IDX

    required_files = [
        DF_PATH,
        INDICES_PATH,
        TFIDF_MATRIX_PATH,
        TFIDF_PATH,
    ]

    for file_path in required_files:

        if not os.path.exists(
            file_path
        ):

            raise RuntimeError(
                f"Required model file not found: "
                f"{os.path.basename(file_path)}"
            )

    try:

        with open(
            DF_PATH,
            "rb"
        ) as file:

            df = pickle.load(
                file
            )

        with open(
            INDICES_PATH,
            "rb"
        ) as file:

            indices_obj = pickle.load(
                file
            )

        with open(
            TFIDF_MATRIX_PATH,
            "rb"
        ) as file:

            tfidf_matrix = pickle.load(
                file
            )

        with open(
            TFIDF_PATH,
            "rb"
        ) as file:

            tfidf_obj = pickle.load(
                file
            )

    except Exception as exc:

        raise RuntimeError(
            f"Unable to load recommendation files: {exc}"
        ) from exc

    if not isinstance(
        df,
        pd.DataFrame
    ):

        raise RuntimeError(
            "df.pkl does not contain a pandas DataFrame."
        )

    if "title" not in df.columns:

        raise RuntimeError(
            "df.pkl must contain a 'title' column."
        )

    if tfidf_matrix.shape[0] != len(df):

        raise RuntimeError(
            "TF-IDF matrix row count does not match "
            "the number of movies in df.pkl."
        )

    TITLE_TO_IDX = build_title_to_idx_map(
        indices_obj
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    model_loaded = (
        df is not None
        and tfidf_matrix is not None
        and bool(TITLE_TO_IDX)
    )

    return {
        "status": "ok",
        "model_loaded": model_loaded,
    }


# ============================================================
# HOME FEED
# ============================================================

@app.get("/home")
async def home(
    category: str = Query(
        "trending"
    ),
    limit: int = Query(
        24,
        ge=1,
        le=100,
    ),
):

    category_endpoints = {

        "trending":
            "/trending/movie/day",

        "popular":
            "/movie/popular",

        "top_rated":
            "/movie/top_rated",

        "upcoming":
            "/movie/upcoming",

        "now_playing":
            "/movie/now_playing",
    }

    if category not in category_endpoints:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid category. "
                "Available categories: "
                + ", ".join(
                    category_endpoints.keys()
                )
            ),
        )

    page_count = (limit + 19) // 20
    pages = await asyncio.gather(
        *(
            tmdb_get(
                category_endpoints[category],
                {"page": page},
            )
            for page in range(1, page_count + 1)
        )
    )

    movies = []

    for movie in (
        movie
        for page in pages
        for movie in page.get("results", [])
    ):

        try:

            movies.append(
                tmdb_to_card(movie)
            )

        except Exception:

            continue

    return movies[:limit]


# ============================================================
# TMDB SEARCH
# ============================================================

@app.get("/tmdb/search")
async def search_tmdb(
    query: str = Query(
        ...,
        min_length=1,
    )
):

    query = query.strip()

    if not query:

        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    results = await tmdb_search(
        query
    )

    return {
        "results": [
            movie.model_dump()
            for movie in results
        ]
    }


# ============================================================
# MOVIE DETAILS
# ============================================================

@app.get("/movie/id/{tmdb_id}")
async def movie_details(
    tmdb_id: int
):

    if tmdb_id <= 0:

        raise HTTPException(
            status_code=400,
            detail="Invalid TMDB movie ID.",
        )

    return await get_movie_details(
        tmdb_id
    )


# ============================================================
# GENRE RECOMMENDATIONS
# ============================================================

@app.get("/recommend/genre")
async def genre_recommendations(
    genre_id: Optional[int] = Query(
        None,
        ge=1,
    ),
    tmdb_id: Optional[int] = Query(
        None,
        ge=1,
    ),
    top_n: int = Query(
        10,
        ge=1,
        le=100,
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=100,
    ),
):

    requested_limit = (
        limit
        if limit is not None
        else top_n
    )

    # The frontend may provide a movie ID instead
    # of a direct TMDB genre ID.
    if genre_id is None:

        if tmdb_id is None:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Provide either genre_id or tmdb_id."
                ),
            )

        details = await get_movie_details(
            tmdb_id
        )

        genres = details.genres

        if not genres:

            return []

        genre_id = int(
            genres[0]["id"]
        )

    data = await tmdb_get(
        "/discover/movie",
        {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "page": 1,
        },
    )

    movies = []

    for movie in data.get(
        "results",
        []
    ):

        try:

            card = tmdb_to_card(
                movie
            )

            # Never recommend the currently selected movie.
            if (
                tmdb_id is not None
                and card.tmdb_id == tmdb_id
            ):

                continue

            movies.append(
                card.model_dump()
            )

        except Exception:

            continue

    return movies[:requested_limit]


# ============================================================
# TF-IDF RECOMMENDATIONS
# ============================================================

@app.get("/recommend/tfidf")
async def tfidf_recommendation(
    title: str = Query(
        ...,
        min_length=1,
    ),
    top_n: int = Query(
        10,
        ge=1,
        le=50,
    ),
):

    title = title.strip()

    recommendations = (
        tfidf_recommend_titles(
            title,
            top_n,
        )
    )

    return {
        "query": title,
        "recommendations": [
            {
                "title": movie_title,
                "score": round(
                    score,
                    6,
                ),
            }
            for movie_title, score
            in recommendations
        ],
    }


# ============================================================
# COMBINED MOVIE SEARCH
# ============================================================

@app.get(
    "/movie/search",
    response_model=SearchBundleResponse,
)
async def movie_search_bundle(
    query: Optional[str] = Query(
        None,
        min_length=1,
    ),
    tmdb_id: Optional[int] = Query(
        None,
        ge=1,
    ),
    tfidf_top_n: int = Query(
        10,
        ge=1,
        le=50,
    ),
    genre_limit: int = Query(
        10,
        ge=1,
        le=50,
    ),
):

    if tmdb_id is not None:
        details = await get_movie_details(tmdb_id)
    else:
        query = (query or "").strip()

        if not query:
            raise HTTPException(
                status_code=400,
                detail="Provide either query or tmdb_id.",
            )

        movie = await tmdb_first_search(query)
        details = await get_movie_details(movie.tmdb_id)

    # --------------------------------------------------------
    # TF-IDF recommendations
    # --------------------------------------------------------

    tfidf_recommendations = (
        tfidf_recommend_titles(
            details.title,
            tfidf_top_n,
        )
    )

    semaphore = asyncio.Semaphore(6)

    async def attach_with_limit(title: str) -> Optional[TMDBMovieCard]:
        async with semaphore:
            return await attach_tmdb_card(title)

    tmdb_cards = await asyncio.gather(
        *(
            attach_with_limit(recommended_title)
            for recommended_title, _ in tfidf_recommendations
        )
    )

    tfidf_items = []

    for (recommended_title, score), tmdb_card in zip(
        tfidf_recommendations,
        tmdb_cards,
    ):

        tfidf_items.append(
            TFIDFRecItem(
                title=recommended_title,
                score=round(
                    score,
                    6,
                ),
                tmdb=tmdb_card,
            )
        )

    # --------------------------------------------------------
    # Genre recommendations
    # --------------------------------------------------------

    genre_recommendations = []

    if details.genres:

        first_genre_id = int(
            details.genres[0]["id"]
        )

        genre_data = await tmdb_get(
            "/discover/movie",
            {
                "with_genres":
                    first_genre_id,

                "sort_by":
                    "popularity.desc",

                "page":
                    1,
            },
        )

        for genre_movie in genre_data.get(
            "results",
            []
        ):

            try:

                genre_movie_id = int(
                    genre_movie.get(
                        "id",
                        -1,
                    )
                )

                # Exclude the movie currently being viewed.
                if (
                    genre_movie_id
                    == details.tmdb_id
                ):

                    continue

                card = tmdb_to_card(
                    genre_movie
                )

                genre_recommendations.append(
                    card
                )

                if len(
                    genre_recommendations
                ) >= genre_limit:

                    break

            except Exception:

                continue

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return SearchBundleResponse(
        query=details.title,
        movie_details=details,
        tfidf_recommendations=tfidf_items,
        genre_recommendations=genre_recommendations,
    )
