# Learnlyf - Frontend

Next.js 15 frontend for Learnlyf.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env.local` and update if needed:

```bash
cp .env.example .env.local
```

Default configuration connects to backend at `http://127.0.0.1:8000`

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at: `http://localhost:3000`

## 🔑 Demo Accounts

### System Admin
- **Email**: admin@learnlyf.com
- **Password**: Admin123!@#
- **Access**: Platform administration dashboard

### School Admin
- **Email**: admin@demo-school.com
- **Password**: Admin123!@#
- **Access**: Demo School dashboard

## 📁 Project Structure

```
frontend/
├── app/
│   ├── dashboard/              # School admin dashboard
│   │   ├── students/          # Student management (Phase 2)
│   │   ├── teachers/          # Teacher management (Phase 2)
│   │   └── page.tsx           # Main dashboard
│   ├── login/                 # Login page
│   ├── register-school/       # School registration
│   ├── system-admin/          # System admin dashboard
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Landing page
│   └── globals.css            # Global styles
├── components/
│   └── ProtectedRoute.tsx     # Authentication guard
├── contexts/
│   └── AuthContext.tsx        # Authentication state
├── lib/
│   └── api.ts                 # API client
├── .env.local                 # Environment variables
└── package.json               # Dependencies
```

## 📄 Pages

### Public Pages
- `/` - Landing page with features overview
- `/login` - Login for all user types
- `/register-school` - School registration with free trial

### Protected Pages
- `/dashboard` - School admin dashboard
- `/dashboard/students` - Student management (placeholder)
- `/dashboard/teachers` - Teacher management (placeholder)
- `/system-admin` - Platform administration dashboard

## 🔌 API Integration

The frontend connects to the backend API via the `api` client in `lib/api.ts`:

```typescript
import { api } from '@/lib/api';

// Login
const result = await api.login({ email, password });

// Get current user
const user = await api.getCurrentUser();

// Register school
await api.registerSchool({ ... });
```

All API calls automatically include credentials (HttpOnly cookies) for authentication.

## 🎨 Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context API
- **HTTP Client**: Fetch API with custom wrapper

## 🔐 Authentication

Authentication is handled via:
1. HttpOnly cookies set by the backend
2. JWT tokens for API requests
3. AuthContext for client-side state
4. ProtectedRoute component for route guards

### Login Flow
1. User submits credentials on `/login`
2. Backend validates and sets HttpOnly cookie
3. Frontend stores user data in AuthContext
4. User redirected to appropriate dashboard

### Protected Routes
Routes are protected using the `ProtectedRoute` component:

```tsx
<ProtectedRoute requiredRole="system_admin">
  <YourComponent />
</ProtectedRoute>
```

## 🛠️ Development

### Running the Development Server

```bash
npm run dev
```

### Building for Production

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

## 📊 Phase 1 Features

- ✅ Landing page with features showcase
- ✅ User authentication (login/logout)
- ✅ School registration with trial signup
- ✅ System admin dashboard with analytics
- ✅ School admin dashboard with organization info
- ✅ Role-based access control
- ✅ Protected routes
- ✅ Responsive design

## 🚧 Phase 2 Features (Coming Soon)

- ❌ Student management
- ❌ Teacher management
- ❌ Class and subject management
- ❌ Attendance tracking
- ❌ Grading system
- ❌ Report card generation
- ❌ Parent portal
- ❌ Payment processing
- ❌ Email notifications

## 🔧 Configuration

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_APP_NAME=Learnlyf
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Backend Connection

Ensure the backend is running on `http://127.0.0.1:8000` before starting the frontend.

## 🐛 Troubleshooting

### CORS Errors

Make sure the backend `ALLOWED_ORIGINS` includes `http://localhost:3000`:

```env
# In backend/.env
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Authentication Issues

1. Check that cookies are being sent (credentials: 'include')
2. Verify backend is running and accessible
3. Clear browser cookies and try again

### API Connection Errors

1. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
2. Check backend is running on the correct port
3. Check browser console for detailed error messages

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop (1024px and above)
- Tablet (768px - 1023px)
- Mobile (below 768px)

## 🎯 Phase 1 MVP Status

| Feature | Status |
|---------|--------|
| Landing Page | ✅ Complete |
| Login Page | ✅ Complete |
| School Registration | ✅ Complete |
| System Admin Dashboard | ✅ Complete |
| School Admin Dashboard | ✅ Complete |
| Authentication | ✅ Complete |
| Protected Routes | ✅ Complete |
| API Integration | ✅ Complete |
| Responsive Design | ✅ Complete |

## 🎉 Next Steps

1. ✅ Backend running
2. ✅ Frontend running
3. ✅ Test complete user flows
4. 🔄 Fix any integration issues
5. 🔄 Deploy to production

## 📞 Support

For issues or questions, check the main project README or documentation.

---

**Frontend Status**: ✅ COMPLETE FOR PHASE 1 MVP
**Version**: 1.0.0
**Last Updated**: June 4, 2026
