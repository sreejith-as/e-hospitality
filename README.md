# 🏥 E-Hospitality - Hospital Management System

A modern, Django-based hospital management system designed to streamline healthcare operations with a clean, intuitive interface.

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)

## ✨ Features

### 👥 Multi-Role System
- **Patients**: Book appointments, view medical records, pay bills online
- **Doctors**: Manage appointments, update patient records, generate prescriptions
- **Admins**: Comprehensive dashboard for managing all hospital operations

### 🏥 Core Functionality
- **Appointment Management**: Real-time scheduling with doctor availability
- **Electronic Health Records**: Secure patient medical history storage
- **Billing System**: Integrated payment processing with Stripe
- **Health Education**: Medical articles and health information portal
- **Email Notifications**: Appointment reminders and verification emails

### 🔒 Security Features
- Role-based access control
- Email verification system
- Secure password management
- Environment-based configuration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sreejith-as/e-hospitality.git
   cd e-hospitality
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-django-secret-key
   DATABASE_NAME=ehospitality_db
   DATABASE_USER=your-db-user
   DATABASE_PASSWORD=your-db-password
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

Visit `http://localhost:8000` to access the application.

## 📁 Project Structure

```
e-hospitality/
├── accounts/          # User authentication & profiles
├── patients/          # Patient management
├── doctors/           # Doctor operations
├── admins/            # Admin dashboard
├── ehospitality/      # Project settings
├── templates/         # HTML templates
├── static/           # Static files
├── media/            # Uploaded files
└── requirements.txt  # Dependencies
```

## 🎯 User Roles

### Patient
- Register and manage profile
- Book and manage appointments
- View medical history and bills
- Make online payments

### Doctor
- View appointment schedule
- Update patient records
- Generate prescriptions
- Manage availability

### Admin
- Full system management
- User account management
- Financial reporting
- Content management

## 💳 Payment Integration

The system integrates with **Stripe** for secure payment processing:
- One-time consultation payments
- Secure card processing
- Payment history tracking

## 📧 Email System

- Account verification emails
- Appointment reminders
- Password reset functionality
- Custom email templates

## 🔧 Configuration

Key configuration options in `ehospitality/settings.py`:
- Database settings (MySQL)
- Email service (Gmail SMTP)
- Payment gateway (Stripe)
- Static and media file handling
- Security settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments

---

**Built with ❤️ using Django and modern web technologies**
