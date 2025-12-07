# Paper-Finder - CORD-19 Research Paper Discovery Platform

A modern web application for discovering and exploring COVID-19 research papers using **Hybrid Search** (BM25 + Semantic k-NN) powered by Elasticsearch.

![Tech Stack](https://img.shields.io/badge/Vue.js-3.3-4FC08D?logo=vue.js&logoColor=white)
![Tech Stack](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![Tech Stack](https://img.shields.io/badge/Elasticsearch-8.11-005571?logo=elasticsearch&logoColor=white)
![Tech Stack](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

## Features

### 🔍 Hybrid Search
- **BM25 + k-NN**: Combines keyword matching with AI semantic similarity
- **Embedding Model**: `all-miniLM-L6-v2` (384-dimensional vectors)
- **Index**: `cord19_hybrid_search` with ~400K research papers
- **Filters**: Publication year, sort by relevance/date

### 📄 Article Details
- **Separate Detail Page**: Full article view at `/article/:id`
- **Full Metadata**: Title, authors, abstract, journal, publication date
- **Reference Papers**: Bibliography from original paper
- **DOI Links**: Direct links to original sources

### 🔗 Related Papers Discovery
- **k-NN Similarity Search**: Find semantically similar papers using embeddings
- **MLT Fallback**: More Like This query when k-NN unavailable
- **Unique Key**: Uses `cord_uid` for lookups, `_id` for MLT queries

### 📖 Full Text Viewer
- **Multi-Source Selection**: Dropdown to choose from multiple URLs
- **HTTP Links**: Open original paper in new tab
- **JSON Content**: View parsed full text from CORD-19 dataset
- **Section Navigation**: Jump to specific sections (Introduction, Methods, Results)

### 📑 Bookmarks & Recommendations
- **Personal Collection**: Save papers for later review
- **AI Recommendations**: Suggestions based on bookmarked papers
- **JWT Authentication**: User-specific bookmarks

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Vue.js      │────▶│     FastAPI     │────▶│  Elasticsearch  │
│    Frontend     │◀────│     Backend     │◀────│    (Hybrid)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   Port 5173               Port 8000               Port 9200
```

### Data Model

**Elasticsearch Document Structure:**
```json
{
  "cord_uid": "6unac0pg",          // Primary key for all operations
  "title": "Paper Title...",
  "abstract": "Paper abstract...",
  "publish_time": "2021-06-08",
  "url": "https://...; document_parses/pmc_json/...",
  "journal": "bioRxiv",
  "authors": "Author1; Author2",
  "references": [...],
  "embedding": [0.123, ...]         // 384-dim vector for k-NN
}
```

## Project Structure

```
miniproject/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── search.py          # Hybrid search endpoint
│   │   │   ├── articles.py        # Article detail & related (k-NN + MLT)
│   │   │   ├── bookmarks.py       # Bookmark CRUD
│   │   │   ├── recommendations.py # Personalized suggestions
│   │   │   └── raw_text.py        # Full text content API
│   │   ├── auth/
│   │   │   └── auth.py            # JWT authentication
│   │   └── main.py                # FastAPI app
│   ├── datasets/
│   │   └── ready_for_indexing.json
│   ├── temp/
│   │   ├── index_data_reference.py # Indexing script with embeddings
│   │   └── enrich_url_with_json_paths.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── SearchPage.vue      # Home & search
│   │   │   ├── ResultsPage.vue     # Search results
│   │   │   ├── ArticleDetailPage.vue # Article details with tabs
│   │   │   ├── RawTextPage.vue     # Full text viewer
│   │   │   └── BookmarksPage.vue   # Saved papers
│   │   ├── composables/
│   │   │   ├── useAuth.js
│   │   │   └── useApi.js
│   │   └── router/
│   │       └── index.js
│   └── package.json
└── docker-compose.yml
```

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- CORD-19 dataset (for full text viewing)

### Quick Start

1. **Start services**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000/docs
   - Elasticsearch: http://localhost:9200

### Local Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Search
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | POST | Hybrid search with filters |

### Articles
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/articles/{cord_uid}` | GET | Get article by cord_uid |
| `/api/articles/{cord_uid}/related` | GET | Get related papers (k-NN + MLT) |

### Full Text
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/raw-text?path=...` | GET | Get parsed JSON content |

### Bookmarks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bookmarks` | GET | Get user's bookmarks |
| `/api/bookmarks` | POST | Add bookmark |
| `/api/bookmarks/{cord_uid}` | DELETE | Remove bookmark |

### Recommendations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/recommendations` | GET | Get personalized suggestions |

## Environment Variables

### Backend
| Variable | Description | Default |
|----------|-------------|---------|
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `JWT_SECRET` | JWT signing key | (required) |
| `CORD19_DATASET_PATH` | Path to CORD-19 dataset | `E:\...\cord19_dataset` |

## Key Concepts

### cord_uid vs _id
- **`cord_uid`**: CORD-19 unique identifier, used for all API operations
- **`_id`**: Elasticsearch internal ID, used for MLT queries

### Full Text URL Format
URLs may contain multiple sources separated by `;`:
```
https://doi.org/10.1234/...; document_parses/pmc_json/PMC12345.xml.json
```

### Related Papers Algorithm
1. **k-NN Search**: Find papers with similar embeddings (cosine similarity)
2. **MLT Fallback**: If k-NN unavailable, use text-based More Like This
3. **Exclusion**: Current article excluded from results

## License

This project is created for educational purposes as part of the HCMUT Big Data course (251-big-data).

## Contributors

- **Student**: Minh BH
- **Course**: Big Data (251)
- **Institution**: HCMUT
