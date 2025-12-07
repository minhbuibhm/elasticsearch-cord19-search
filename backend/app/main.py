from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import search, articles, bookmarks, recommendations, raw_text
from app.auth import auth

app = FastAPI(
    title="Paper-Finder API",
    description="Backend API for Paper-Finder - Research Paper Discovery Platform",
    version="1.0.0"
)

# CORS Configuration - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["Bookmarks"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(raw_text.router, prefix="/api", tags=["Raw Text"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Paper-Finder API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
