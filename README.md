# TC Heiner's Professional Website

A modern, full-stack portfolio and blog built with Astro, featuring an AI-powered chatbot for interactive Q&A about TC's experience, projects, and expertise.

🌐 **Live Site**: [tcheiner.com](https://tcheiner.com)  
🤖 **AI Chatbot**: Interactive assistant powered by GPT-4o-mini + RAG

## 🧠 Human-AI Collaboration Philosophy

This project exemplifies the synergy between **human creativity** and **AI precision**:

- **Humans provide**: Strategic thinking, creative problem-solving, architecture decisions, content creation, and system improvements
- **AI provides**: Accurate context referencing, consistent knowledge retrieval, 24/7 availability, and detailed technical recall

The system is designed for **collaborative maintenance**:
- **Content creators** (humans) use templates and validation tools for quality assurance
- **AI chatbot** indexes and serves that content with perfect recall and source attribution
- **Developers** (humans) architect and improve the system while **AI assistants** help with code context and debugging
- **Users** get the best of both worlds: human insights delivered through AI precision

## 🚀 Features

### Frontend
- **Modern Portfolio**: Clean, responsive design showcasing projects, experience, and blog posts
- **AI Chatbot Integration**: Interactive Q&A with freemium model (5 free questions + user API key)
- **Content Management**: MDX-based blog posts, projects, experiences, and recipes
- **Template System**: Automated content creation with date-stamped templates
- **Responsive Design**: Mobile-first approach with Tailwind CSS

### Backend AI Chatbot
- **RAG Architecture**: FAISS vectorstore + OpenAI embeddings for accurate responses
- **Content Filtering**: Prevents API key abuse with personality/cultural fit assessment
- **AWS Lambda**: Serverless deployment with container images (10GB limit)
- **Security**: AWS SSM Parameter Store for API key management, CORS protection

## 🏗️ System Architecture Overview

Understanding the architecture empowers both humans and AI to collaborate on improvements:

### Data Flow & Human-AI Collaboration Points
```
[Human] Creates Content → [Templates/Validation] → [MDX Files] → [AI Processing]
                                     ↓
[Static Website] ← [Astro Build] ← [Content Collections] → [FAISS Vectorstore]
                                                                      ↓
[Human Users] → [Chatbot UI] → [API Gateway] → [Lambda Container] → [GPT-4o-mini + RAG]
```

### Key Architectural Decisions for Maintainability
- **Template System**: Reduces human error, ensures AI can parse content consistently
- **Schema Validation**: Catches issues early, prevents runtime chatbot errors  
- **Container Deployment**: Eliminates dependency conflicts, scales automatically
- **Separate Concerns**: Frontend (human-focused) + Backend (AI-focused) can evolve independently
- **Content as Code**: Version controlled, reviewable, auditable content changes

### Improvement Opportunities
- **Content Quality**: Better templates → Better AI responses
- **Performance**: Caching strategies, CDN optimization, Lambda cold start reduction
- **User Experience**: Enhanced chatbot UI, better error handling, mobile optimization  
- **AI Capabilities**: Fine-tuning, additional data sources, multi-modal support
- **Analytics**: User interaction tracking, content performance metrics
- **Security**: Rate limiting, enhanced content filtering, audit logging

## 🛠️ Technologies Used

### Frontend Stack
- **[Astro](https://astro.build/)**: Modern static site generator with component islands
- **[React](https://reactjs.org/)**: Interactive components with TypeScript
- **[Tailwind CSS](https://tailwindcss.com/)**: Utility-first CSS framework
- **[Shadcn/ui](https://ui.shadcn.com/)**: Accessible component library
- **MDX**: Markdown with JSX for rich content authoring

### AI Chatbot Stack
- **[FastAPI](https://fastapi.tiangolo.com/)**: Python web framework for API endpoints
- **[LangChain](https://langchain.com/)**: RAG pipeline orchestration
- **[OpenAI GPT-4o-mini](https://openai.com/)**: Language model with 150-token responses
- **[FAISS](https://faiss.ai/)**: Vector similarity search for content retrieval
- **[AWS Lambda](https://aws.amazon.com/lambda/)**: Serverless compute with container images

### Infrastructure & Deployment
- **[AWS Services](https://aws.amazon.com/)**: Lambda, API Gateway, ECR, SSM Parameter Store
- **[Terraform](https://terraform.io/)**: Infrastructure as Code
- **[Docker](https://docker.com/)**: Containerized deployments
- **[GitHub Actions](https://github.com/features/actions)**: CI/CD pipeline

## 📁 Project Structure

```
tcheiner-astro-bento/
├── src/
│   ├── components/           # React/Astro components
│   │   └── ChatbotUI.tsx    # AI chatbot interface
│   ├── content/             # MDX content collections
│   │   ├── posts/          # Blog posts (post-YYYY-MM-DD.mdx)
│   │   ├── projects/       # Project showcases
│   │   ├── experiences/    # Work experience
│   │   ├── books/         # Book reviews
│   │   └── recipes/       # Recipe collection
│   └── pages/             # Astro pages and API routes
├── backend/               # AI chatbot backend
│   ├── chatbot/
│   │   ├── main.py       # FastAPI app + Lambda handler
│   │   ├── services.py   # FAISS vectorstore + QA chain
│   │   └── models.py     # API schemas
│   ├── terraform/        # AWS infrastructure
│   └── Dockerfile       # Lambda container
└── templates/           # Content creation templates
    ├── post-template.mdx
    ├── project-template.mdx
    ├── experience-template.mdx
    └── create-content.sh  # Automated content creation
```

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+**
- **Python 3.12+**
- **Docker** (for chatbot deployment)
- **AWS CLI** (for cloud deployment)

### Frontend Development

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd tcheiner-astro-bento
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   # Visit http://localhost:4321
   ```

3. **Create New Content**:
   ```bash
   # Auto-generates with today's date
   ./templates/create-content.sh post        # → post-2025-09-02.mdx
   ./templates/create-content.sh project     # → project-2025-09-02.mdx
   ./templates/create-content.sh experience  # → experience-2025-09-02.mdx
   ```

4. **Validate Content**:
   ```bash
   node validate-mdx.js  # Checks all MDX files for schema compliance
   ```

5. **Build for Production**:
   ```bash
   npm run build
   ```

### AI Chatbot Setup

See [backend/README.md](./backend/README.md) for detailed chatbot setup, deployment, and content management.

**Quick Local Setup**:
```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-your-key-here" > .env
uvicorn chatbot.main:app --reload
```

## 📝 Content Management

### Content Types & Schema

| Type | Location | Schema | Auto-Generated Filename |
|------|----------|--------|------------------------|
| **Blog Posts** | `src/content/posts/` | title, startDate, description, tags, image | `post-YYYY-MM-DD.mdx` |
| **Projects** | `src/content/projects/` | title, startDate, description, tags, image | `project-YYYY-MM-DD.mdx` |
| **Experience** | `src/content/experiences/` | title, company, startDate, endDate, tags | `experience-YYYY-MM-DD.mdx` |
| **Books** | `src/content/books/` | title, author, readYear, tags | `book-YYYY-MM-DD.mdx` |
| **Recipes** | `src/content/recipes/` | title, description, postDate, course, cuisine, ingredients, preparation | `recipe-YYYY-MM-DD.mdx` |

### Adding New Content

1. **Use Templates** (Recommended):
   ```bash
   ./templates/create-content.sh post
   # Edit the generated file
   node validate-mdx.js  # Validate before committing
   ```

2. **Manual Creation**:
   ```bash
   cp templates/post-template.mdx src/content/posts/post-2025-09-02.mdx
   # Edit frontmatter and content
   ```

### Content Workflow
1. Create content using templates
2. Validate with `node validate-mdx.js`
3. Rebuild chatbot FAISS index (if using chatbot)
4. Deploy changes

## 🤖 AI Chatbot Features

### User Experience
- **Freemium Model**: 5 free questions, then user API key required
- **Smart Filtering**: Only accepts TC-related questions + personality/cultural fit topics
- **Response Limiting**: ~150 tokens for concise, focused answers
- **Source Attribution**: Links back to original blog posts and projects

### Technical Features
- **RAG System**: Vector similarity search + GPT-4o-mini generation
- **Content Indexing**: Auto-indexes blog posts, projects, and experiences
- **API Key Security**: AWS SSM Parameter Store integration
- **CORS Protection**: Domain-restricted access

### Supported Query Types
- ✅ Professional experience and skills
- ✅ Project details and technical approaches  
- ✅ Personality traits and working style
- ✅ Cultural fit and behavioral questions
- ✅ Educational background and career progression
- ❌ General knowledge, weather, unrelated topics

## 🚀 Deployment

### Frontend (Static Site)
```bash
npm run build
# Deploy dist/ to your hosting provider
```

### AI Chatbot (AWS Lambda)
```bash
cd backend
./build-container.sh        # Build & push container
cd terraform && tofu apply  # Deploy infrastructure
```

## 📊 Development Workflow

### Adding New Content
```bash
# 1. Create content
./templates/create-content.sh post
# Edit the generated file

# 2. Validate
node validate-mdx.js

# 3. Update chatbot knowledge (if applicable)
cd backend && python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"

# 4. Deploy
./backend/build-container.sh  # Update chatbot
npm run build                 # Build frontend
```

### Code Changes
```bash
# Frontend changes
npm run dev  # Test locally
npm run build && npm run preview  # Test build

# Backend changes  
cd backend && uvicorn chatbot.main:app --reload  # Test locally
./build-container.sh  # Deploy to AWS
```

## 🔧 Available Scripts

### Frontend
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `node validate-mdx.js` - Validate all MDX content

### Backend (from `backend/` directory)
- `uvicorn chatbot.main:app --reload` - Start local API server
- `./build-container.sh` - Build and deploy to AWS
- `python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"` - Rebuild content index

### Content Creation
- `./templates/create-content.sh <type>` - Create new content with templates

## 📄 License

This project serves as TC Heiner's professional portfolio and blog. Feel free to use the code structure and chatbot architecture for your own projects.

## 🤝 Contributing

This is a personal portfolio, but issues and suggestions are welcome!

---

**Built with ❤️ by TC Heiner** | [Website](https://tcheiner.com) | [LinkedIn](https://linkedin.com/in/tcheiner)