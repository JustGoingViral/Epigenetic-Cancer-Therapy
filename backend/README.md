# MTET Platform Backend API

The backend API for the Multi-Targeted Epigenetic Cancer Therapy (MTET) Platform - an AI-enabled healthcare solution for personalized cancer treatment optimization.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 13+ (or SQLite for development)
- Redis (optional, for caching and background tasks)

### Installation

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start the server**
   ```bash
   python run.py --reload --init-db
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## 🏗️ Architecture

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   └── v1/                 # API version 1
│   │       ├── __init__.py     # Router configuration
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── patients.py     # Patient management
│   │       ├── biomarkers.py   # Biomarker analysis
│   │       ├── treatments.py   # Treatment management
│   │       └── analytics.py    # Analytics and reporting
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration management
│   │   └── security.py         # Authentication & authorization
│   └── db/                     # Database layer
│       ├── __init__.py
│       ├── database.py         # Database connection & session
│       ├── models.py           # SQLAlchemy models
│       └── init_db.py          # Database initialization
├── .env.example                # Environment configuration template
├── requirements.txt            # Python dependencies
├── run.py                      # Server startup script
├── test_api.py                 # API testing script
└── README.md                   # This file
```

### Core Components

#### 1. **Authentication & Authorization**
- JWT-based authentication
- Role-based access control (Admin, Clinician, Researcher, Patient, Viewer)
- Secure password hashing with bcrypt
- Token refresh mechanism

#### 2. **Patient Management**
- Comprehensive patient profiles
- Clinical data tracking
- Risk assessment and stratification
- Demographics and medical history

#### 3. **Biomarker Analysis**
- Genomic, epigenetic, and protein marker processing
- AI-powered biomarker analysis
- Annotation and interpretation
- File upload support for laboratory data

#### 4. **Treatment Management**
- Treatment plan creation and tracking
- AI-driven treatment recommendations
- Outcome monitoring and assessment
- Drug compound database

#### 5. **Analytics & Reporting**
- Real-time dashboards
- Custom report generation
- Performance metrics
- Clinical outcome analysis

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Current user info

### Patients
- `GET /api/v1/patients/` - List patients
- `POST /api/v1/patients/` - Create patient
- `GET /api/v1/patients/{id}` - Get patient details
- `PUT /api/v1/patients/{id}` - Update patient
- `POST /api/v1/patients/{id}/clinical-data` - Add clinical data

### Biomarkers
- `POST /api/v1/biomarkers/profiles/{patient_id}` - Create biomarker profile
- `GET /api/v1/biomarkers/profiles/{patient_id}` - Get patient biomarker profiles
- `POST /api/v1/biomarkers/analyze` - Analyze biomarker data
- `POST /api/v1/biomarkers/compound-matching` - Find matching compounds

### Treatments
- `POST /api/v1/treatments/{patient_id}` - Create treatment plan
- `GET /api/v1/treatments/{patient_id}` - Get patient treatments
- `POST /api/v1/treatments/ai-recommendations` - Get AI treatment recommendations
- `POST /api/v1/treatments/{treatment_id}/outcomes` - Record treatment outcome

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard summary
- `GET /api/v1/analytics/patients` - Patient analytics
- `GET /api/v1/analytics/treatments` - Treatment analytics
- `POST /api/v1/analytics/custom-report` - Generate custom reports

## 💾 Database Models

### Core Entities

#### Users
- Authentication and user management
- Role-based permissions
- Professional credentials

#### Patients
- Demographics and medical history
- Cancer staging and diagnosis
- Risk assessment scores

#### Biomarker Profiles
- Genomic mutations
- Gene expressions
- Epigenetic markers
- Protein levels

#### Treatments
- Treatment plans and protocols
- Drug compounds and dosing
- AI recommendations

#### Outcomes
- Treatment responses
- Adverse events
- Quality of life metrics
- Biomarker changes

## 🔒 Security Features

### Authentication
- JWT tokens with configurable expiration
- Secure password hashing (bcrypt)
- Token refresh mechanism
- Session management

### Authorization
- Role-based access control (RBAC)
- Endpoint-level permissions
- Resource ownership validation
- Admin-only operations

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- CORS protection
- Rate limiting support

## 🧪 Testing

### Run API Tests
```bash
# Start the server first
python run.py --init-db

# In another terminal, run tests
python test_api.py --save-results
```

### Test Coverage
The test script validates:
- ✅ Health check endpoints
- ✅ Authentication flow
- ✅ Protected endpoints
- ✅ API documentation
- ✅ Database connectivity

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mtet_db

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI/ML Models
MODEL_CACHE_DIR=./data/models
BIOMARKER_MODEL_PATH=./data/models/biomarker_classifier.pkl

# External APIs
PUBCHEM_API_URL=https://pubchem.ncbi.nlm.nih.gov/rest/pug
```

### Default Users

After database initialization, these users are available:

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| Admin | admin@mtet-platform.com | admin123 | System administrator |
| Clinician | clinician@mtet-platform.com | clinician123 | Medical professional |
| Researcher | researcher@mtet-platform.com | researcher123 | Research scientist |

⚠️ **Change these passwords in production!**

## 🚀 Deployment

### Development
```bash
python run.py --reload --init-db
```

### Production
```bash
# Set environment variables
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=your-secure-secret-key

# Start with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker (Future)
```bash
# Build image
docker build -t mtet-api .

# Run container
docker run -p 8000:8000 mtet-api
```

## 📊 Monitoring

### Health Checks
- `GET /health` - Application health
- Database connectivity check
- Dependency status

### Metrics
- Request/response times
- Error rates
- Database performance
- Authentication metrics

## 🔮 AI/ML Integration

### Biomarker Analysis
- Automated biomarker classification
- Pathway enrichment analysis
- Drug sensitivity prediction
- Mutation burden calculation

### Treatment Recommendations
- Patient stratification algorithms
- Evidence-based treatment matching
- Outcome prediction models
- Clinical decision support

### Data Processing
- Genomic data pipelines
- Laboratory result parsing
- Image analysis (future)
- Natural language processing (future)

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests before committing
5. Submit a pull request

### Code Standards
- Follow PEP 8 guidelines
- Add type hints where possible
- Write comprehensive docstrings
- Maintain test coverage >90%

## 📝 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Authentication Example
```python
import requests

# Login
response = requests.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "clinician@mtet-platform.com",
    "password": "clinician123"
})
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
patients = requests.get("http://localhost:8000/api/v1/patients/", headers=headers)
```

## 🆘 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Verify database exists
psql -U postgres -c "SELECT 1;"

# Check .env configuration
cat .env | grep DATABASE_URL
```

**Import Errors**
```bash
# Ensure virtual environment is activated
which python

# Reinstall dependencies
pip install -r requirements.txt
```

**Permission Denied**
```bash
# Check user roles in database
python -c "from app.db.init_db import create_initial_data; create_initial_data()"
```

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint
- **Email**: support@mtet-platform.com

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](../LICENSE) file for details.

---

**Healthcare Compliance Notice**: This platform is designed for research and clinical decision support. All treatment decisions should be made in consultation with qualified healthcare professionals in accordance with applicable medical standards and regulations.
