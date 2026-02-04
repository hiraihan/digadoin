# Digadoin - Backend API

This is the backend REST API for the Digadoin platform, built with **FastAPI**. It handles authentication, business logic, database management, and serves data to the Next.js frontend.

## Tech Stack
*   **Framework**: FastAPI
*   **Database**: PostgreSQL
*   **ORM**: SQLAlchemy
*   **Migrations**: Alembic
*   **Validation**: Pydantic
*   **Testing**: Pytest

## Key Features
*   **Authentication**: JWT-based Auth (Login, Register, Role-based Access).
*   **Order System**: Manage orders, pricing plans, and payment status.
*   **Project CMS**: Track project development stages and details.
*   **Ticketing**: Support ticket system with admin-client messaging.
*   **Connection Pooling**: Optimized database connections for performance.

## Setup & Installation

### 1. Prerequisites
*   Python 3.10+
*   PostgreSQL installed and running.

### 2. Virtual Environment
Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Copy `.env.example` to `.env` and fill in your database credentials:
```bash
# Example .env content
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_SERVER=localhost
DB_PORT=5432
DB_NAME=digadoin_db
SECRET_KEY=your_secret_key
```

### 5. Database Migration
Apply database schema:
```bash
alembic upgrade head
```

### 6. Run Server
Start the development server with live reload:
```bash
uvicorn app.main:app --reload
```
API Documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

## Testing
Run the test suite:
```bash
pytest
```
