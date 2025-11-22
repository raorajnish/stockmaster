# StockMaster - Inventory Management System

StockMaster is a comprehensive Django-based inventory management system designed to replace Excel sheets and manual registers. It provides a modern, web-based solution for managing inventory operations with role-based access control.

## 🚀 Features

### Core Features
- **Product Management**: Complete CRUD operations for products with categories, SKU tracking, and unit of measure
- **Receipt Management**: Track incoming goods from suppliers with detailed receipt operations
- **Delivery Orders**: Manage outgoing shipments to customers with delivery tracking
- **Internal Transfers**: Move inventory between warehouses and locations seamlessly
- **Stock Adjustments**: Perform physical inventory counts and synchronize system quantities
- **Multi-Warehouse Support**: Manage multiple warehouses and locations with location-level tracking
- **Stock Ledger**: Complete audit trail of all stock movements with detailed history
- **Real-Time Analytics**: Dashboard with KPI cards showing:
  - Total Products in Stock
  - Low Stock Items
  - Out of Stock Items
  - Pending Receipts
  - Pending Deliveries
  - Internal Transfers Scheduled

### User Features
- **Role-Based Access Control**: 
  - Inventory Manager: Full access to all features
  - Warehouse Staff: Operational access for day-to-day tasks
- **User Authentication**: Secure login system with forgot password functionality
- **Password Reset**: OTP-based password reset via email
- **User Profile**: View personal statistics and activity

### Additional Features
- **Low Stock Alerts**: Automatic notifications for products below minimum stock levels
- **Advanced Filtering**: Filter operations by type, status, warehouse, category, and search
- **Responsive Design**: Mobile-friendly interface that works on all devices
- **Modern UI**: Clean, minimal design with accent color (#704a66)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/raorajnish/stockmaster.git
cd stockmaster
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Create PostgreSQL Database
1. Open pgAdmin 4 or use psql command line
2. Create a new database named `stockmaster_db`
3. Create a user `rajni` with password `#Raj0977` (or update settings.py with your credentials)

#### Using psql:
```sql
CREATE DATABASE stockmaster_db;
CREATE USER rajni WITH PASSWORD '#Raj0977';
ALTER ROLE rajni SET client_encoding TO 'utf8';
ALTER ROLE rajni SET default_transaction_isolation TO 'read committed';
ALTER ROLE rajni SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE stockmaster_db TO rajni;
```

### 5. Configure Database Settings

Update `stockmaster/settings.py` if you're using different database credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'stockmaster_db',
        'USER': 'rajni',
        'PASSWORD': '#Raj0977',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

## 🏃 Running the Application

### Start the Development Server
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

### Access the Application
- **Home Page**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/ (if superuser created)

## 👥 User Roles

### Inventory Manager
- Full access to all features
- Can create and manage products, categories, units of measure
- Can create and validate all operation types
- Access to all reports and analytics

### Warehouse Staff
- Can create receipts, deliveries, transfers, and adjustments
- Can validate operations
- Limited administrative access
- View-only access to certain reports

## 📁 Project Structure

```
stockmaster/
├── core/                    # Main application
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── forms.py            # Django forms
│   ├── urls.py             # URL routing
│   └── admin.py            # Admin configuration
├── users/                   # User authentication app
│   ├── models.py           # Custom User model
│   ├── views.py            # Auth views
│   ├── forms.py            # Auth forms
│   └── urls.py             # Auth URLs
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── core/              # Core app templates
│   └── users/             # User app templates
├── static/                 # Static files (CSS, JS, images)
├── stockmaster/           # Project settings
│   ├── settings.py        # Django settings
│   └── urls.py            # Main URL configuration
├── requirements.txt        # Python dependencies
└── manage.py              # Django management script
```

## 🗄️ Database Models

- **User**: Custom user model with role fields (is_manager, is_w_staff)
- **Product**: Products with SKU, name, category, cost, min_stock
- **Category**: Product categories
- **UnitOfMeasure**: Units of measure (kg, pcs, etc.)
- **Partner**: Suppliers and customers
- **Warehouse**: Warehouse locations
- **Location**: Storage locations within warehouses
- **InventoryOperation**: Receipts, deliveries, transfers, adjustments
- **OperationLine**: Line items for operations
- **StockLevel**: Current stock levels per location
- **StockLedgerEntry**: Complete audit trail

## 🔧 Configuration

### Email Settings (for Password Reset)
Update `stockmaster/settings.py` for production:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@stockmaster.com'
```

For development, the console backend is used (emails print to console).

## 🎨 UI/UX

- **Theme**: Light theme with accent color `#704a66`
- **Framework**: Bootstrap 5
- **Icons**: Bootstrap Icons
- **Responsive**: Mobile-friendly design
- **Navigation**: Sidebar navigation for authenticated users

## 📝 Key Pages

- **Dashboard**: KPI cards and recent operations with filters
- **Products**: Product list with search, filter, and CRUD operations
- **Receipts**: Incoming goods management
- **Deliveries**: Outgoing shipments management
- **Internal Transfers**: Inter-warehouse transfers
- **Stock Adjustments**: Physical count adjustments
- **Move History**: Complete stock ledger with filters
- **Warehouses**: Warehouse and location management
- **My Profile**: User profile and activity statistics

## 🔐 Security Features

- Password hashing (Django's default PBKDF2)
- CSRF protection
- SQL injection protection (Django ORM)
- Session-based authentication
- Role-based access control

## 🧪 Testing

Run tests (if available):
```bash
python manage.py test
```

## 📦 Dependencies

- Django 5.2.8
- psycopg2-binary 2.9.11 (PostgreSQL adapter)
- Bootstrap 5.3.0 (via CDN)
- Bootstrap Icons 1.10.0 (via CDN)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

**Rajnish Rao**
- GitHub: [@raorajnish](https://github.com/raorajnish)

## 🙏 Acknowledgments

- Django Framework
- Bootstrap Team
- PostgreSQL Community

## 📞 Support

For support, email support@stockmaster.com or open an issue in the repository.

---

**Note**: This is a development version. For production deployment, ensure to:
- Set `DEBUG = False`
- Configure proper email backend
- Use environment variables for sensitive data
- Set up proper static file serving
- Configure ALLOWED_HOSTS
- Use HTTPS
- Set up proper database backups

