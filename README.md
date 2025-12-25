# QA Testing API

REST API for manual QA testing with PostgreSQL database.

## Features

- JWT Authentication with role-based access
- Full CRUD for Users, Categories, Products, Orders
- Filtering, pagination, sorting
- Swagger UI documentation
- Database reset endpoint
- Pre-seeded test data

## Quick Start (Local)

```bash
docker compose up --build
```

Open http://localhost:8000/docs

## Deployment (Coolify)

1. Push to GitHub
2. In Coolify: Create Project → Add Docker Compose
3. Set domain in application settings
4. Deploy

## API Documentation

After deployment, Swagger UI available at:
- `https://YOUR_DOMAIN/docs`

## Test Credentials

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| admin | admin123 | Admin | Full access, can reset DB |
| tester | tester123 | Tester | CRUD operations |
| viewer | viewer123 | Viewer | Read-only access |

## Database Connection

```
Host: YOUR_DOMAIN (or db container internally)
Port: 5432
Database: qa_db
Username: qa_user
Password: qa_password
```

Direct connection string:
```
postgresql://qa_user:qa_password@YOUR_DOMAIN:5432/qa_db
```

**Note**: For external DB access, expose port 5432 in Coolify or use SSH tunnel.

## API Endpoints

### Authentication
- `POST /auth/login` - Get JWT token
- `POST /auth/register` - Create new user
- `GET /auth/me` - Current user info

### Users (auth required)
- `GET /users` - List users
- `GET /users/{id}` - Get user
- `PUT /users/{id}` - Update user (admin)
- `DELETE /users/{id}` - Delete user (admin)

### Categories (auth required)
- `GET /categories` - List categories
- `POST /categories` - Create category (tester+)
- `GET /categories/{id}` - Get category
- `PUT /categories/{id}` - Update category (tester+)
- `DELETE /categories/{id}` - Delete category (tester+)

### Products (auth required)
- `GET /products` - List with filters (price, stock, category, search)
- `POST /products` - Create product (tester+)
- `GET /products/{id}` - Get product
- `PUT /products/{id}` - Update product (tester+)
- `DELETE /products/{id}` - Delete product (tester+)

### Orders (auth required)
- `GET /orders` - List orders (viewers see own only)
- `POST /orders` - Create order (tester+)
- `GET /orders/{id}` - Get order
- `PUT /orders/{id}` - Update order (tester+)
- `DELETE /orders/{id}` - Delete order (tester+)
- `POST /orders/{id}/cancel` - Cancel pending order

### Admin
- `POST /admin/reset` - Reset DB to seed data (admin only)
- `GET /admin/stats` - Get record counts (admin only)

### Health
- `GET /health` - Health check
- `GET /` - API info

## Testing Scenarios

### Happy Path
1. Login → Create category → Create product → Create order → Check order

### Validation
- Missing required fields
- Invalid email format
- Price <= 0
- Duplicate SKU/email/username

### Authorization
- Viewer trying to create/update/delete
- Accessing other user's orders as viewer

### Edge Cases
- Empty results
- Non-existent IDs (404)
- Inactive products in orders

### Reset Flow
- Login as admin → `POST /admin/reset` → Verify clean state
