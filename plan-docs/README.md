# Clean Operations Dashboard

A minimal, clean operations dashboard built with modern web technologies.

## Architecture

- **Frontend**: Pure HTML + HTMX + Alpine.js + TailwindCSS
- **Backend**: FastAPI with minimal dependencies
- **Data**: In-memory storage (can be upgraded to database later)

## Features

- Single-page application with clean UI
- Complete CRUD operations for users and functions
- Request history and tracking
- Role-based authentication
- Minimal dependencies and clean code

## Project Structure

```
dashboard-clean/
├── frontend/
│   └── assets/
│       ├── css/           # Custom styles
│       ├── js/            # JavaScript utilities
│       ├── index.html     # Main SPA entry point
│       ├── dashboard.html # Dashboard content
│       ├── functions.html # Functions management
│       ├── users.html     # User management
│       └── requests.html  # Request history
└── backend/
    ├── main.py           # FastAPI application
    ├── requirements.txt  # Python dependencies
    └── ...               # API modules
```

## Development

1. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python main.py
   ```

3. Open http://localhost:8000

## Design Principles

- **Simplicity**: Minimal code, maximum functionality
- **Clean Architecture**: Clear separation of concerns
- **Modern Stack**: Using latest web standards
- **No Database**: In-memory storage for simplicity
- **Pure Frontend**: No complex build processes