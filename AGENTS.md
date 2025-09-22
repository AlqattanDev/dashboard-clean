# Development Guide for AI Agents

## Project Structure
- **Backend**: Python FastAPI app in `/backend/` with minimal dependencies
- **Frontend**: Vanilla HTML/CSS/JS in `/frontend/assets/` using TailwindCSS, HTMX, AlpineJS

## Commands
- **Run backend**: `cd backend && python main.py` (runs on port 8000)
- **Install dependencies**: `cd backend && pip install -r requirements.txt`
- **No build/test/lint commands** - this is a minimal project without these toolchains

## Code Style Guidelines

### Python (Backend)
- Use double quotes for strings
- Type hints with modern syntax (e.g., `list[str]` not `List[str]`)
- FastAPI route functions should be async
- Import order: standard library, third-party, local imports
- Docstrings in triple quotes for modules/functions

### JavaScript (Frontend)  
- camelCase for variables and functions
- Use modern ES6+ syntax (const/let, arrow functions, async/await)
- Object-oriented approach with namespace pattern (e.g., `window.DashboardApp`)
- Event-driven architecture with HTMX and AlpineJS
- Use template literals for HTML strings

### General
- Keep files minimal and focused - avoid over-engineering
- Use semantic HTML5 elements
- TailwindCSS utility classes for styling
- No TypeScript - use vanilla JavaScript
- File paths use kebab-case (e.g., `dashboard.js`)