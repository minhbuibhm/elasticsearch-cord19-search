# Paper-Finder - Research Paper Discovery Platform

A modern web application for discovering and exploring research papers using AI-powered semantic search.

![Tech Stack](https://img.shields.io/badge/Vue.js-3.3-4FC08D?logo=vue.js&logoColor=white)
![Tech Stack](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![Tech Stack](https://img.shields.io/badge/Elasticsearch-8.11-005571?logo=elasticsearch&logoColor=white)
![Tech Stack](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

## Features

### Search & Discovery
- **Semantic Search**: AI-powered keyword-based similarity scoring
- **Advanced Filters**: Filter by publication date, article type, sort by relevance or date
- **Similarity Scores**: Each result shows relevance score (0.00-1.00)

### Article Management
- **Detailed View**: Full article information with abstract, authors, journal, DOI
- **Related Papers**: Automatically discover papers related to any article
- **Bookmarks**: Save interesting papers for later review

### Personalization
- **User Accounts**: Simple JWT-based authentication
- **My Bookmarks**: Personal collection of saved papers
- **AI Recommendations**: Personalized suggestions based on bookmarked papers

### User Interface
- **Modern Design**: Clean, teal/cyan color scheme
- **Responsive**: Works on desktop and mobile devices
- **Smooth Animations**: Polished transitions and interactions

## Tech Stack

### Frontend
- **Vue.js 3** (Composition API)
- **Vue Router** (SPA navigation)
- **Tailwind CSS** (Styling)
- **Axios** (HTTP client)
- **Vite** (Build tool)

### Backend
- **FastAPI** (Python web framework)
- **Pydantic** (Data validation)
- **JWT** (Authentication)
- **Python 3.11+**

### Infrastructure
- **Docker & Docker Compose**
- **Nginx** (Production web server)
- **Elasticsearch 8.11** (Ready for future integration)

## Project Structure

```
miniproject/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── search.py          # Search endpoint
│   │   │   ├── articles.py        # Article detail & related
│   │   │   ├── bookmarks.py       # Bookmark CRUD
│   │   │   └── recommendations.py # Personalized suggestions
│   │   ├── auth/
│   │   │   └── auth.py            # JWT authentication
│   │   ├── data/
│   │   │   └── mock_cord19.json   # 10 research papers
│   │   ├── main.py                # FastAPI app
│   │   └── models.py              # Pydantic models
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.vue
│   │   │   ├── SearchBar.vue
│   │   │   ├── AdvancedFilters.vue
│   │   │   ├── ResultCard.vue
│   │   │   ├── ArticleModal.vue
│   │   │   └── RelatedPapers.vue
│   │   ├── views/
│   │   │   ├── SearchPage.vue
│   │   │   ├── ResultsPage.vue
│   │   │   └── BookmarksPage.vue
│   │   ├── composables/
│   │   │   ├── useAuth.js
│   │   │   └── useApi.js
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── docker-compose.yml
```

## Getting Started

### Prerequisites
- Docker & Docker Compose installed
- (Optional) Node.js 18+ and Python 3.11+ for local development

### Quick Start with Docker Compose

1. **Clone the repository** (or navigate to the project directory)
   ```bash
   cd miniproject
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Elasticsearch: http://localhost:9200

4. **Login**
   - Enter any username (minimum 3 characters)
   - The system will create a user account automatically

### Local Development

#### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Access API at http://localhost:8000

#### Frontend (Vue.js)

```bash
cd frontend
npm install
npm run dev
```

Access UI at http://localhost:5173

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with username
- `GET /api/auth/me` - Get current user info

### Search
- `POST /api/search` - Search papers with filters

### Articles
- `GET /api/articles/{id}` - Get article details
- `GET /api/articles/{id}/related` - Get related papers

### Bookmarks
- `GET /api/bookmarks` - Get user's bookmarks
- `POST /api/bookmarks` - Add bookmark
- `DELETE /api/bookmarks/{id}` - Remove bookmark
- `GET /api/bookmarks/check/{id}` - Check if bookmarked

### Recommendations
- `GET /api/recommendations` - Get personalized recommendations

## Mock Data

The application includes 10 realistic research papers covering various topics:
- Clinical treatment trials
- Vaccine effectiveness studies
- Disease syndrome research
- Molecular analysis studies
- Clinical trials
- Environmental health studies
- Pediatric health research
- Therapeutic research
- Mental health impact studies
- Vaccine development research

## User Flow

1. **Landing Page**: Enter search query with optional advanced filters
2. **Search Results**: View papers sorted by relevance with similarity scores
3. **Article Details**: Click any paper to see full abstract and related papers
4. **Bookmarking**: Save interesting papers to your collection
5. **Recommendations**: Get AI-powered suggestions based on your bookmarks

## Features in Detail

### Advanced Search Filters
- **Time Range**: Any time, Since year (2025/2024/2021), Custom range
- **Sort By**: Relevance or Date (newest first)
- **Article Type**: Any type or Review articles only
- **Include**: Patents and/or Citations

### Similarity Scoring
- Keyword-based matching between query and paper content
- Title matches get higher scores
- Scores normalized to 0.00-1.00 range

### Recommendation Algorithm
- Calculate similarity between user's bookmarks and all other papers
- Average similarity scores across all bookmarked papers
- Return top papers with highest average similarity

## Docker Services

### frontend
- Multi-stage build (Node.js build + Nginx serve)
- Port: 8080
- Nginx proxy to backend API

### backend
- FastAPI with Uvicorn
- Port: 8000
- Auto-reload enabled for development

### elasticsearch
- Single-node cluster
- Port: 9200 (HTTP), 9300 (Transport)
- Security disabled for development
- Ready for future semantic search integration

## Environment Variables

### Backend
- `JWT_SECRET`: Secret key for JWT tokens (default: "your-secret-key-change-in-production")
- `ELASTICSEARCH_URL`: Elasticsearch connection URL (default: "http://elasticsearch:9200")

### Frontend
- `VITE_API_URL`: Backend API URL (default: "http://localhost:8000")

## Future Enhancements

- [ ] Integrate Elasticsearch for real-time indexing
- [ ] Implement true semantic search using embeddings
- [ ] Add user registration and persistent user accounts
- [ ] Export bookmarks to CSV/PDF
- [ ] Citation network visualization
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Dark mode theme

## License

This project is created for educational purposes as part of the HCMUT Big Data course (251-big-data).

## Contributors

- **Student**: Minh BH
- **Course**: Big Data (251)
- **Institution**: HCMUT
