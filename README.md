# ATS CV Generator

A production-ready, job-description-driven ATS-optimized CV generator platform. Users maintain a persistent professional profile and generate tailored CVs based on job descriptions, achieving 90%+ ATS compatibility scores.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30-red)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## 🌟 Features

- **User Authentication**: Secure signup/login with JWT-based authentication
- **Profile Management**: Store and manage personal details, education, skills, projects, internships, certifications, and achievements
- **AI-Powered Keyword Extraction**: Uses Groq LLaMA-3.1-70B to extract keywords from job descriptions
- **Hybrid ATS Engine**: Combines rule-based and AI-based optimization for 90%+ ATS scores
- **LaTeX CV Generation**: Professional, ATS-optimized LaTeX templates
- **PDF & DOCX Export**: Compile LaTeX to PDF and convert to DOCX
- **Background Processing**: Celery workers for async document generation
- **Docker Ready**: Complete Docker Compose setup for easy deployment

## 🏗️ Architecture

```
┌─────────────────┐     REST API     ┌─────────────────┐
│                 │◄───────────────► │                 │
│   Streamlit     │                  │    FastAPI      │
│   Frontend      │                  │    Backend      │
│                 │                  │                 │
└─────────────────┘                  └────────┬────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
            ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
            │   MongoDB     │         │   Groq API    │         │    Redis      │
            │   Database    │         │   (LLM)       │         │   (Celery)    │
            └───────────────┘         └───────────────┘         └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- Redis
- LaTeX (pdflatex or xelatex)
- Pandoc
- Groq API Key

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "A Ultimate CV generator"
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set your Groq API key**
   ```bash
   # In .env file
   GROQ_API_KEY=your-groq-api-key
   ```

4. **Start all services**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Configure environment**
   ```bash
   cp ../.env.example .env
   # Edit .env with your configuration
   ```

4. **Start MongoDB and Redis**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 mongo:7.0
   docker run -d -p 6379:6379 redis:7-alpine
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Start Celery worker** (in separate terminal)
   ```bash
   celery -A app.services.tasks worker --loglevel=info
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Configure API URL**
   ```bash
   export API_BASE_URL=http://localhost:8000/api/v1
   ```

3. **Run Streamlit**
   ```bash
   streamlit run app.py --server.port 8501
   ```

## 📖 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user info |
| POST | `/api/v1/auth/logout` | Logout user |

### Profile Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/profile/` | Create profile |
| GET | `/api/v1/profile/` | Get profile |
| PUT | `/api/v1/profile/` | Update profile |
| POST | `/api/v1/profile/education` | Add education |
| PUT | `/api/v1/profile/education/{index}` | Update education |
| DELETE | `/api/v1/profile/education/{index}` | Delete education |
| PUT | `/api/v1/profile/skills` | Update skills |
| POST | `/api/v1/profile/projects` | Add project |
| POST | `/api/v1/profile/internships` | Add internship |
| POST | `/api/v1/profile/certifications` | Add certification |
| POST | `/api/v1/profile/achievements` | Add achievement |

### CV Generation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/cv/generate` | Generate ATS-optimized CV |
| GET | `/api/v1/cv/analyze` | Analyze ATS compatibility |
| GET | `/api/v1/cv/history` | Get CV history |
| GET | `/api/v1/cv/{cv_id}` | Get specific CV |
| GET | `/api/v1/cv/{cv_id}/latex` | Get LaTeX code |
| GET | `/api/v1/cv/{cv_id}/download-pdf` | Download PDF |
| GET | `/api/v1/cv/{cv_id}/download-docx` | Download DOCX |
| DELETE | `/api/v1/cv/{cv_id}` | Delete CV |

## 📊 Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "email": "string",
  "password_hash": "string",
  "created_at": "datetime",
  "last_login": "datetime"
}
```

### Profiles Collection
```javascript
{
  "user_id": ObjectId,
  "personal_details": {
    "full_name": "string",
    "location": "string",
    "phone": "string",
    "email": "string",
    "linkedin": "string",
    "github": "string"
  },
  "education": [...],
  "skills": {
    "programming_languages": [...],
    "technical_skills": [...],
    "developer_tools": [...]
  },
  "projects": [...],
  "internships": [...],
  "certifications": [...],
  "achievements": [...],
  "updated_at": "datetime"
}
```

### Generated CVs Collection
```javascript
{
  "user_id": ObjectId,
  "job_description": "string",
  "aligned_skills": [...],
  "ats_score": number,
  "latex_code": "string",
  "created_at": "datetime"
}
```

## 🎯 ATS Optimization Engine

The hybrid ATS engine combines:

### Rule-Based Logic
- Keyword match percentage calculation
- Skill frequency control (anti-stuffing)
- Bullet point length validation (12-20 words)
- Section header standardization
- Single-column layout enforcement

### AI-Based Logic
- JD keyword extraction using LLaMA-3.1-70B
- Skill alignment and gap analysis
- Bullet point enhancement
- Natural language optimization

### Scoring Weights
- Keyword Match: 35%
- Semantic Similarity: 30%
- Bullet Quality: 20%
- Section Coverage: 15%

## 🔒 Security Features

- Bcrypt password hashing
- JWT with access/refresh tokens
- CORS protection
- Input sanitization
- Sandboxed LaTeX compilation
- Environment-based secrets

## 🛠️ Configuration

All configuration is done via environment variables. See `.env.example` for all options.

Key configurations:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | Required |
| `MONGODB_URL` | MongoDB connection string | Required |
| `GROQ_API_KEY` | Groq API key for LLM | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `ATS_MIN_SCORE` | Minimum ATS score target | `90` |
| `LATEX_COMPILER` | LaTeX compiler to use | `pdflatex` |

## 🧪 Testing

```bash
cd backend
pytest tests/ -v --cov=app
```

## 📁 Project Structure

```
A Ultimate CV generator/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Pydantic models
│   │   ├── services/      # Business logic
│   │   ├── templates/     # LaTeX templates
│   │   └── utils/         # Utilities
│   ├── tests/             # Unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── pages/             # Streamlit pages
│   ├── app.py             # Main Streamlit app
│   ├── api_client.py      # API client
│   ├── config.py          # Configuration
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Development

### Adding New Features

1. Add API endpoint in `backend/app/api/`
2. Add service logic in `backend/app/services/`
3. Add Pydantic models in `backend/app/models/schemas.py`
4. Update frontend in `frontend/app.py`
5. Write tests in `backend/tests/`

### Customizing LaTeX Template

Edit `backend/app/templates/cv_template.tex` to modify the CV layout. The template uses Jinja2 syntax with `<<` and `>>` delimiters.

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📧 Support

For issues and questions, please open a GitHub issue.
