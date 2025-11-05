from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date

# ============ Authentication Models ============
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str

class TokenData(BaseModel):
    user_id: str
    username: str

# ============ Search Models ============
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    year: Optional[str] = None  # Filter by publication year (e.g., "2020")
    tokenizer: Literal["Standard", "N-Gram"] = "Standard"
    search_method: Literal["regular", "semantic"] = "regular"
    pagination: dict = {"page": 1, "size": 10}

class ArticleSnippet(BaseModel):
    id: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    title: str
    authors: List[str]
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    abstract_snippet: str

class SearchResponse(BaseModel):
    pagination: dict
    results: List[ArticleSnippet]

# ============ Article Models ============
class ArticleDetail(BaseModel):
    id: str
    title: str
    authors: List[str]
    full_abstract: str
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    full_text_url: Optional[str] = None
    clinical_trials: List[str] = []
    doi: Optional[str] = None

class RelatedArticle(BaseModel):
    id: str
    similarity_score: float
    title: str
    authors: List[str]
    abstract_snippet: str

class RelatedArticlesResponse(BaseModel):
    article_id: str
    related_papers: List[RelatedArticle]

# ============ Bookmark Models ============
class BookmarkRequest(BaseModel):
    article_id: str

class BookmarkResponse(BaseModel):
    message: str
    article_id: str

class BookmarkedArticle(BaseModel):
    id: str
    title: str
    authors: List[str]
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    abstract_snippet: str
    bookmarked_at: str

class BookmarksListResponse(BaseModel):
    bookmarks: List[BookmarkedArticle]
    total: int

# ============ Recommendation Models ============
class RecommendedArticle(BaseModel):
    id: str
    relevance_score: float
    title: str
    authors: List[str]
    abstract_snippet: str
    reason: str  # Why this is recommended

class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendedArticle]
    total: int
    based_on_bookmarks: int
