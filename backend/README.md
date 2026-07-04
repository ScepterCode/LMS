# Nigerian LMS Backend - Phase 1 MVP

FastAPI backend for the Nigerian Learning Management System.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required configuration:
- `DATABASE_URL`: Your Supabase PostgreSQL connection string
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `JWT_SECRET`: A secure random string for JWT tokens

### 3. Setup Database

Run the database schema setup script:

```bash
cd ..
python apply_phase1_schema.py
```

### 4. Start Server

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at: `http://127.0.0.1:8000`

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 🔑 Default Credentials

### System Admin
- Email: `admin@nigerianlms.com`
- Password: `Admin123!@#`

### Demo School Admin
- Email: `admin@demo-school.com`
- Password: `Admin123!@#`

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py              # Authentication endpoints
│   │       │   ├── system_admin.py      # System admin endpoints
│   │       │   └── organizations.py     # Organization endpoints
│   │       └── api.py                   # API router
│   ├── core/
│   │   ├── config.py                    # Configuration settings
│   │   ├── database.py                  # Database connections
│   │   ├── security.py                  # Authentication & security
│   │   └── exceptions.py                # Custom exceptions
│   ├── middleware/
│   │   └── error_handler.py             # Error handling
│   └── main.py                          # FastAPI application
├── tests/                               # Test files
├── .env                                 # Environment variables
├── .env.example                         # Environment template
├── requirements.txt                     # Python dependencies
└── README.md                            # This file
```

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/register-school` - Register new school

### System Admin
- `GET /api/v1/system-admin/organizations` - List all organizations
- `GET /api/v1/system-admin/organizations/{id}` - Get organization details
- `PATCH /api/v1/system-admin/organizations/{id}/status` - Update organization status
- `GET /api/v1/system-admin/analytics` - Platform analytics
- `GET /api/v1/system-admin/subscription-plans` - List subscription plans
- `GET /api/v1/system-admin/users` - List all users

### Organizations
- `GET /api/v1/organizations/{id}` - Get organization details
- `GET /api/v1/organizations/{id}/users` - List organization users
- `GET /api/v1/organizations/{id}/campuses` - List organization campuses

## 🔒 Authentication

The API uses JWT tokens with HttpOnly cookies for authentication:

1. Login via `/api/v1/auth/login`
2. Token is set as HttpOnly cookie
3. Token is also returned in response for flexibility
4. All protected endpoints require authentication

## 🛠️ Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
```

### Checking Logs

Logs are written to `app.log` and stdout.

## 🐛 Troubleshooting

### Database Connection Issues

If you see "Database pool initialization failed":

1. Check your `DATABASE_URL` in `.env`
2. Verify Supabase project is running
3. On Windows, try using `127.0.0.1` instead of `localhost`
4. The app will fallback to Supabase client if PostgreSQL connection fails

### Import Errors

Make sure you're in the `backend` directory when running the server:

```bash
cd backend
uvicorn app.main:app --reload
```

### CORS Errors

Check `ALLOWED_ORIGINS` in `.env` includes your frontend URL.

## 📝 Phase 1 Features

- ✅ User authentication (login/logout)
- ✅ School registration with trial
- ✅ System admin dashboard
- ✅ Organization management
- ✅ User management
- ✅ Platform analytics
- ✅ Role-based access control

## 🚧 Coming in Phase 2

- Student management
- Teacher management
- Attendance system
- Grading system
- Payment processing
- Advanced analytics

## 📞 Support

For issues or questions, check the main project README or documentation.