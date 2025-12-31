# 🚀 Miles - AI-Powered Multi-Tenant Application

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)

A modern, scalable AI-powered application built with cutting-edge technologies. Features multi-tenant architecture, real-time capabilities, and seamless deployment on Vercel.

## ✨ Features

- 🔐 **Google OAuth Integration** - Secure authentication with invitation system
- 🏢 **Multi-Tenant Architecture** - Workspace-based organization
- 🤖 **AI-Powered Workflows** - LangGraph integration for complex AI tasks
- ⚡ **Real-time Features** - Supabase real-time subscriptions
- 📱 **Modern UI/UX** - React 18 with Tailwind CSS
- 🚀 **Serverless Deployment** - Optimized for Vercel platform
- 📊 **Rich Database Schema** - PostgreSQL with advanced features
- 🔄 **API-First Design** - RESTful APIs with automatic documentation

## 🛠️ Tech Stack

### Frontend
- **React 18** - Modern React with hooks and concurrent features
- **Vite** - Lightning-fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Declarative routing for React

### Backend
- **FastAPI** - High-performance async web framework
- **Python 3.8+** - Modern Python with type hints
- **Uvicorn** - Lightning-fast ASGI server

### AI & ML
- **LangGraph** - Framework for building complex AI workflows
- **LangChain** - Framework for developing LLM applications
- **OpenAI API** - Integration with GPT models
- **Sentence Transformers** - Text embeddings and similarity

### Database & Infrastructure
- **Supabase** - Open source Firebase alternative
- **PostgreSQL** - Advanced relational database
- **Supabase Auth** - Authentication and authorization
- **Supabase Storage** - File storage with CDN
- **Supabase Realtime** - Real-time subscriptions

### DevOps & Deployment
- **Vercel** - Global CDN and serverless functions
- **GitHub Actions** - CI/CD pipelines
- **Docker** - Containerization support

## 📁 Project Structure

```
miles/
├── frontend/                    # React SPA
│   ├── public/                  # Static assets
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── contexts/           # React context providers
│   │   ├── lib/                # Utilities and configurations
│   │   ├── services/           # API clients and services
│   │   └── pages/              # Page-level components
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
│
├── backend/                     # FastAPI application
│   ├── main.py                 # Application entry point
│   └── requirements.txt        # Python dependencies
│
├── supabase/                    # Database and configurations
│   ├── schema.sql              # Database schema
│   └── migrations/             # Database migrations
│
├── env.example                 # Environment variables template
├── vercel.json                 # Vercel deployment configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # Project documentation
```

## 🚀 Quick Start

### Prerequisites

Before running this application, make sure you have the following installed:

- **Node.js 18+** and **npm** - [Download here](https://nodejs.org/)
- **Python 3.8+** - [Download here](https://python.org/)
- **Git** - [Download here](https://git-scm.com/)
- **Supabase Account** - [Sign up here](https://supabase.com/)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dhruvsoni2611/Miles.git
   cd miles
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   pip install -r requirements.txt
   cd ..
   ```

3. **Set up the frontend:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Environment configuration:**
   ```bash
   cp env.example .env
   # Edit .env with your actual values (see Environment Setup below)
   ```

### Running the Application

1. **Start the backend server:**
   ```bash
   cd backend
   python main.py
   ```
   🌐 Backend API: http://localhost:8000

2. **Start the frontend (in a new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```
   🌐 Frontend App: http://localhost:3000

### 🧪 Testing the Setup

- **API Health Check:** http://localhost:8000/api/health
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc
- **Frontend Application:** http://localhost:3000

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory and configure the following variables:

```env
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# API Configuration
VITE_API_URL=http://localhost:8000

# AI/ML Services
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CLIENT_ID=your_google_oauth_client_id_here
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret_here

# Application Settings
ENVIRONMENT=development
DEBUG=true
```

### 🗄️ Database Setup

1. **Create a Supabase project:**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Wait for setup to complete

2. **Configure the database:**
   - Copy your project URL and API keys from Supabase dashboard
   - Update your `.env` file with these values
   - Run the schema migration:
   ```sql
   -- Execute the contents of supabase/schema.sql in your Supabase SQL editor
   ```

3. **Enable required extensions:**
   - Go to Database → Extensions in your Supabase dashboard
   - Enable: `uuid-ossp`, `pgcrypto`

### 🔐 Authentication Setup

#### Google OAuth Configuration

1. **Google Cloud Console:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google+ API

2. **OAuth Credentials:**
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Set application type to "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:3000` (development)
     - `https://your-domain.com` (production)

3. **Update environment variables:**
   ```env
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

#### Supabase Auth Configuration

1. **Authentication Settings:**
   - In Supabase dashboard, go to Authentication → Settings
   - Configure OAuth providers (Google)
   - Set up redirect URLs

2. **Custom SMTP (Optional):**
   - Configure email templates for invitation system
   - Set up SMTP credentials for email delivery

## 🚀 Deployment

### Vercel Deployment (Recommended)

1. **Connect Repository:**
   - Sign up at [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will auto-detect the configuration

2. **Environment Variables:**
   - In Vercel dashboard, go to Project Settings → Environment Variables
   - Add all variables from your `.env` file

3. **Deploy:**
   - Push to main branch to trigger automatic deployment
   - Your app will be available at `https://your-project.vercel.app`

### Manual Deployment Options

#### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

#### Railway/Render Deployment
- Connect your GitHub repository
- Set environment variables
- Deploy automatically

## 📊 Database Schema

The application uses the following core tables:

### Core Tables
- **`users`** - User accounts with Google OAuth integration
- **`workspaces`** - Multi-tenant workspace isolation
- **`invitations`** - Invitation system for workspace access

### Key Features
- **Row Level Security (RLS)** enabled on all tables
- **UUID primary keys** for security
- **Automatic timestamps** with triggers
- **Workspace-based data isolation**

## 🔧 Development Workflow

### Code Quality
```bash
# Frontend linting
cd frontend
npm run lint

# Type checking (if using TypeScript)
npm run type-check

# Backend testing
cd backend
python -m pytest
```

### Git Workflow
```bash
# Feature development
git checkout -b feature/your-feature-name
git commit -m "feat: add new feature"
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## 🤖 AI/ML Integration

### Current AI Capabilities
- **LangGraph Workflows** - Complex AI agent orchestration
- **OpenAI Integration** - GPT models for text generation
- **Sentence Transformers** - Text similarity and embeddings
- **Playwright** - Web automation for data collection

### Adding New AI Features
```python
# Example: Adding a new LangGraph workflow
from langgraph import StateGraph
from langchain_openai import ChatOpenAI

# Define your workflow in backend/
```

## 📈 Monitoring & Analytics

### Application Monitoring
- **Vercel Analytics** - Built-in performance monitoring
- **Supabase Dashboard** - Database performance and usage
- **Custom Logging** - Structured logging with correlation IDs

### Error Tracking
- **Sentry Integration** - Real-time error tracking
- **Custom Error Boundaries** - React error boundaries for graceful failures

## 🔐 Security Features

- **OAuth 2.0** - Secure authentication with Google
- **JWT Tokens** - Stateless authentication
- **Row Level Security** - Database-level access control
- **HTTPS Only** - Enforced SSL/TLS
- **CORS Protection** - Configured cross-origin policies
- **Input Validation** - Comprehensive data validation

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/Miles.git`
3. Create feature branch: `git checkout -b feature/amazing-feature`
4. Make changes and test thoroughly
5. Submit a pull request

## 📝 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints
- `GET /api/health` - Health check
- `POST /api/invitations` - Create workspace invitation
- `GET /api/invitations/verify` - Verify invitation token
- `POST /api/auth/google` - Google OAuth authentication

## 🐛 Troubleshooting

### Common Issues

**Frontend not loading:**
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Backend connection issues:**
```bash
# Check if backend is running
curl http://localhost:8000/api/health
```

**Database connection errors:**
- Verify Supabase credentials in `.env`
- Check Supabase project status
- Ensure database schema is applied

### Getting Help
- Check existing [GitHub Issues](https://github.com/dhruvsoni2611/Miles/issues)
- Create a new issue with detailed error logs
- Include your environment details and steps to reproduce

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Supabase** - For the amazing open-source Firebase alternative
- **Vercel** - For the exceptional deployment platform
- **FastAPI** - For the incredible Python web framework
- **React** - For the robust frontend library
- **Tailwind CSS** - For the utility-first CSS framework

## 📞 Support

- **GitHub Issues** - For bug reports and feature requests
- **Discussions** - For questions and general discussion
- **Email** - For security issues or sensitive matters

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Basic project structure
- ✅ Authentication system
- ✅ Multi-tenant architecture
- ✅ Database schema
- 🚧 AI workflow integration

### Phase 2 (Next)
- 🔄 Real-time features
- 📊 Analytics dashboard
- 📧 Email notifications
- 🔍 Advanced search
- 📱 Mobile responsiveness

### Phase 3 (Future)
- 🤖 Advanced AI agents
- 📈 Machine learning models
- 🔗 Third-party integrations
- 🌐 Multi-language support
- 📊 Advanced analytics

---

## ⚠️ Important Notes

### AI Dependencies
Some advanced AI packages are conditionally included in `requirements.txt`. If you encounter import errors:

```bash
# Install additional AI dependencies
pip install langchain langgraph openai sentence-transformers torch
```

### Python Version Compatibility
- **Recommended**: Python 3.8 - 3.11 (avoid 3.12+ for AI packages)
- **FastAPI** requires Python 3.8+
- **AI packages** may have compatibility issues with Python 3.12+

### Environment Setup
- Always use virtual environments
- Never commit `.env` files
- Use `env.example` as a template
- Test locally before deploying

---

<p align="center">
  <strong>Built with ❤️ using modern web technologies</strong>
</p>

<p align="center">
  <a href="#miles---ai-powered-multi-tenant-application">Back to top</a>
</p>
