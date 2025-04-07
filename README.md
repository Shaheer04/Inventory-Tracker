# 📌 Project Overview
This Store Inventory API is designed to solve the challenge of inventory tracking across multiple retail stores. It provides a comprehensive solution for tracking product stock-ins, sales, and manual removals, enabling real-time visibility to prevent stockouts and overstocking.

The system is architected to scale from a single kiryana store to thousands of stores with built-in audit capabilities, designed for high performance, scalability, and reliability to support high-volume retail operations.

# 🛠️ Tech Stack

- Framework: FastAPI

- ORM: SQLModel

- Databases:

- SQLite (Development/Stage 1)

- PostgreSQL (Production/Stage 2-3)

- Caching: Redis

- Authentication: API key-based auth

- Rate Limiting: SlowAPI

# 🏗️ Architecture & Design Decisions

## Key Components

- API Layer: RESTful endpoints with proper validation and error handling

- Data Access Layer: Database interactions through SQLModel ORM

- Caching Layer: Redis for high-frequency read operations

- Authentication: API key mechanism with role-based permissions

# 📈 Evolution Rationale (V1 → V3)

## Stage 1: Single Store Solution

- SQLite database for local storage

- Basic API

- Focuses on core functionality: stock-in, sales, and manual removals

- SQLModel ORM for database interactions, setting foundation for easy migration

### Data Models v1:

- Product Model

- Store Model

- StockMovement

- Current Stock 

### Endpoints v1:

- GET/POST /products - Manage products

- GET/POST /store - Manage store

- GET/POST /movements - Record/Retirve Stock Movements

- GET /products/product_id/stock - Get Current stock of a product

### Design Decisions:

- SQLite chosen for simplicity and zero-config setup

- Monolithic design for rapid development

- SQLModel ORM used to provide consistent data access patterns regardless of database backend

## Stage 2: Multi-Store Solution

- Migration to PostgreSQL for reliability and concurrency

- Expanded REST API with filtering capabilities

- Implementation of store-specific inventory tracking

- Basic authentication and request throttling

- SQLModel ORM maintained for seamless database transition

### Data Models v2:

- Store model with location details

- Enhanced Product model with additional attributes

- Addded Store Specific Stock Model

- User model with role based permission for authentication


### Endpoints v2:

- GET/POST/PUT/DELETE /stores - Store management

- GET/POST/PUT/DELETE /products - Product management

- GET/POST/PUT/DELETE /stores/{store_id}/stock - Store-specific stock operations

- GET /reports/stock-levels - Stock Reporting

- GET /reports/sales - Sales Reporting

- POST /generate-api-key - API based Authentication

### Design Decisions:

- Same SQLModel code works with both SQLite and PostgreSQL, enabling smooth transition

- Introduction of proper API key authentication

- Request rate limiting to prevent abuse

- Query optimization for store-specific reporting


## Stage 3: Scalable Solution

- Horizontally scalable architecture

- Caching Using Redis

- Read/write separation

- Comprehensive audit logging

- SQLModel ORM continues to provide database abstraction with optimized queries

- Docker for scaliblity 

### Data Models v3:

- All Models from stage 2

- Added AuditLog model for comprehensive tracking

- User model with role-based permissions

### Endpoints v3:

- All endpoints from Stage 2

- GET/POST /audit - Audit log management


### Design Decisions:

- SQLModel ORM's consistent API allows for seamless scaling without code refactoring

- Cache invalidation middleware for data consistency

- Database connection pooling for better resource utilization

- Asynchronous processing for non-critical operations

- Docker Containerization for deplomyment scaliblity


# 🔒 Security Considerations

- API keys stored as secure hashes

- Rate limiting to prevent abuse

- API Key Based Auth

- Input validation on all endpoints

- Comprehensive audit logging

- Role-based access control

# 📋 Assumptions

- Each store operates with a stable internet connection to enable real-time synchronization with the central inventory system.

- Products have a unique system-wide identifier (e.g., product_id).

- Store staff regularly update stock activities (stock-in, sales, and manual removals) to maintain accurate inventory levels.

- Basic hardware (e.g., smartphones, tablets, or POS systems) is available at stores to interact with the API.

- Initial deployments will handle limited concurrency, with scaling strategies (e.g., horizontal scaling, caching) introduced in later phases.

# 🔧 Setup & Installation

## Clone the repository

`git clone https://github.com/yourusername/store-inventory-api.git`

`cd inventory-tracker`

## Install dependencies
`pip install -r requirements.txt`

### Set up environment variables
`cp .env.example .env`

Edit .env with your configuration

## Run development server
`uvicorn main:app --reload`