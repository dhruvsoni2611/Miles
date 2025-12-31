# Miles - AI-Powered Application

A full-stack application built with React, FastAPI, LangGraph, and Node.js, designed for deployment on Vercel.

## 🚀 Tech Stack

- **Frontend**: React 18 + Vite + Tailwind CSS
- **Backend**: FastAPI + Python
- **AI/ML**: LangGraph (ready for integration)
- **Database**: Supabase
- **Deployment**: Vercel
- **Languages**: JavaScript/TypeScript, Python

## 📁 Project Structure

```
Miles/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── contexts/           # React contexts for state management
│   │   ├── lib/                # Utilities (Supabase client)
│   │   ├── services/           # API client functions
│   │   └── pages/              # Page components
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
├── backend/                     # FastAPI application
│   ├── main.py                 # FastAPI app entry point
│   └── requirements.txt        # Python dependencies
├── env.example                 # Environment variables template
├── vercel.json                 # Vercel deployment config
└── README.md
```

## 🛠️ Setup & Development

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Git

### Installation

1. **Clone and setup:**
   ```bash
   git clone <your-repo-url>
   cd miles
   ```

2. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

4. **Environment setup:**
   ```bash
   cp env.example .env
   # Edit .env with your actual API keys
   ```

### Running the Application

1. **Start the backend:**
   ```bash
   cd backend
   python main.py
   ```
   Backend will run on: http://localhost:8000

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will run on: http://localhost:3000

### Testing the Setup

- **Backend health check**: http://localhost:8000/api/health
- **Frontend**: http://localhost:3000
- **API test**: http://localhost:8000/

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and fill in your values:

```env
# Frontend
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000

# Backend
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
OPENAI_API_KEY=your_openai_api_key
```

### Supabase Setup

1. Create a new Supabase project
2. Copy your project URL and anon key to the environment variables
3. Run database migrations (when you have them)

## 🚀 Deployment

### Vercel Deployment

1. Connect your GitHub repository to Vercel
2. Vercel will automatically detect the configuration from `vercel.json`
3. Set environment variables in Vercel dashboard
4. Deploy!

The `vercel.json` configuration:
- Builds the frontend as a static site
- Deploys the backend as serverless functions
- Routes API calls to the Python backend

## 🔮 Next Steps

### Immediate Tasks
- [ ] Set up Supabase database schema
- [ ] Add LangGraph workflows to backend
- [ ] Implement authentication
- [ ] Add more React components
- [ ] Set up proper error handling

### AI/ML Integration
- [ ] Install LangChain and LangGraph (currently commented out due to Python version compatibility)
- [ ] Create AI agent workflows
- [ ] Add OpenAI API integration
- [ ] Implement conversation memory

### Features to Add
- [ ] User authentication with Supabase Auth
- [ ] Real-time features with Supabase Realtime
- [ ] File upload functionality
- [ ] Admin dashboard
- [ ] API documentation with Swagger

## 📚 API Documentation

Once running, visit:
- **FastAPI Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Note**: Some advanced AI packages (LangChain, LangGraph, OpenAI) are currently excluded from requirements.txt due to Python 3.13 compatibility issues. Install them manually when needed:

```bash
pip install langchain langgraph openai
```
