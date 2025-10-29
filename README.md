# TeleGen - AI-Powered Content Generation Platform

> Professional Telegram content automation platform powered by Artificial Intelligence

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Overview

TeleGen is an advanced AI-powered platform for automated content generation, aggregation, and publishing to Telegram channels. It combines intelligent content processing, multi-source aggregation, and flexible scheduling to streamline your content workflow.

### Key Features

#### 🤖 Intelligent Content Generation
- **AI-powered content creation** using GPT models (OpenAI/DeepSeek)
- **Smart content transformation** with customizable styles and formats
- **Multi-language support** for content generation
- **Emoji and formatting enhancement**
- **Custom AI prompts** and role-based generation

#### 📡 Content Aggregation
- **Telegram channel scraping** with userbot integration
- **RSS feed processing** and monitoring
- **Web content extraction** from multiple sources
- **Automatic duplicate detection** using source IDs
- **Content filtering** and validation

#### ⏰ Advanced Scheduling
- **Flexible posting schedules** (hourly, 12h, daily)
- **Time zone support** for accurate scheduling
- **Queue management** with buffer system
- **Automatic post cleanup** based on flow volume
- **Retry mechanisms** for failed posts

#### 📊 Management & Analytics
- **Django admin panel** for full control
- **User subscription management** with multiple tariff plans
- **Payment integration** (Monobank, CryptoBot)
- **Comprehensive statistics** and logging
- **Channel and flow management**

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Telegram Bot  │ ─── Aiogram 3.x
│   (User Layer)  │
└────────┬────────┘
         │
┌────────┴────────┐
│  Django Admin   │ ─── Django 5.1
│     Panel       │
└────────┬────────┘
         │
┌────────┴────────────────────┐
│   Shared Business Logic     │
│  ├─ Services                │
│  ├─ Repositories            │
│  ├─ AI Processing           │
│  └─ Media Handling          │
└────────┬────────────────────┘
         │
┌────────┴────────────────────┐
│  Celery Task Queue          │
│  ├─ Post Generation         │
│  ├─ Content Aggregation     │
│  ├─ Scheduled Publishing    │
│  └─ Background Jobs         │
└────────┬────────────────────┘
         │
┌────────┴────────────────────┐
│   Data Layer                │
│  ├─ PostgreSQL (main DB)    │
│  ├─ Redis (cache & queue)   │
│  └─ Media Storage           │
└─────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+** - Modern async/await support
- **Django 5.1** - Admin panel and web framework
- **Aiogram 3.x** - Telegram Bot framework
- **Celery** - Distributed task queue
- **Celery Beat** - Periodic task scheduler

### AI & Content Processing
- **OpenAI GPT-4** - Advanced content generation
- **DeepSeek API** - Alternative AI provider
- **Telethon** - Telegram userbot for channel scraping
- **Beautiful Soup** - Web content extraction
- **Pillow** - Image processing

### Databases & Caching
- **PostgreSQL 15** - Primary database with advanced indexing
- **Redis 7** - Caching and Celery broker
- **Django ORM** - Database abstraction with async support

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Gunicorn** - WSGI HTTP server
- **WhiteNoise** - Static file serving
- **GitHub Actions** - CI/CD (optional)

### Monitoring & Logging
- **Structured JSON logging** - Easy log parsing
- **Django logging** - Comprehensive error tracking
- **Telegram logging** - Real-time notifications

---

## 📦 Installation

### Prerequisites

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Python 3.11+** (for local development)
- **Telegram Bot Token** (from [@BotFather](https://t.me/botfather))
- **Telegram API credentials** (from [my.telegram.org](https://my.telegram.org))

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/atljh/TeleGen.git
   cd TeleGen
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (see Configuration section)
   ```

3. **Start the application**
   ```bash
   make up
   ```

4. **Apply database migrations**
   ```bash
   make migrate
   ```

5. **Access the application**
   - **Admin Panel**: http://localhost:8000/admin
   - **Bot**: Start conversation with your bot on Telegram

---

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file with the following configuration:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DJANGO_SETTINGS_MODULE=core.settings.dev

# CSRF Protection (Django 4.0+)
# Comma-separated list of origins with protocol
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://yourdomain.com

# PostgreSQL Database
DB_NAME=telegen_db
DB_USER=telegen_user
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_IDS=123456789,987654321
TELEGRAM_LOG_CHANNEL_ID=-1001234567890

# Telegram Userbot (for channel scraping)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890

# AI APIs
OPENAI_API_KEY=sk-proj-...
DEEPSEEK_API_KEY=vsk-...

# Payment Providers
MONOBANK_TOKEN=your-monobank-token
CRYPTOBOT_TOKEN=your-cryptobot-token

# Redis & Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Application
BASE_URL=http://localhost:8000
```

---

## 🎮 Usage

### Makefile Commands

```bash
# Container Management
make up              # Start all containers
make down            # Stop all containers
make restart         # Restart all containers
make logs            # View logs from all containers

# Database Operations
make migrate         # Run Django migrations
make makemigrations  # Create new migrations
make shell           # Open Django shell

# Development
make format          # Format code with Black
make lint            # Run linting checks
make type-check      # Run mypy type checking

# Deployment
make build           # Build Docker images
make deploy          # Deploy to production
```

### Bot Commands

Users can interact with the bot using these commands:

- `/start` - Start bot and show main menu
- `/help` - Display help information
- `/settings` - Configure bot settings
- `/create_flow` - Create new content flow
- `/my_channels` - Manage channels
- `/statistics` - View analytics
- `/subscribe` - Manage subscription

---

## 📊 Features in Detail

### Content Flows

A **Flow** is a content pipeline that:
1. Aggregates content from multiple sources (Telegram channels, RSS feeds, websites)
2. Processes and transforms content using AI
3. Manages a buffer of generated posts
4. Publishes posts on a schedule

**Flow Configuration:**
- **Theme**: Content topic/niche
- **Sources**: List of content sources with weights
- **Volume**: Number of posts to maintain in buffer
- **Frequency**: How often to generate new content
- **AI Settings**: Custom prompts, style, emojis, etc.

### Post Generation Pipeline

```
Source Content → Aggregation → AI Processing → Media Handling → Buffer → Scheduled Publishing
      ↓              ↓              ↓                ↓             ↓           ↓
   Telegram       Deduplication  GPT-4         Image/Video    Queue      Telegram
   RSS Feeds      Validation     Transform     Download       Mgmt       Channel
   Websites       Filtering      Enhance       Validation
```

### Transaction Safety

The system implements **robust transaction handling**:
- Atomic post creation with media
- Duplicate prevention using unique source IDs
- Media validation before database commits
- Automatic rollback on errors
- Cleanup of partial uploads

### Performance Optimizations

- **Database indexes** on frequently queried fields
- **Connection pooling** for database efficiency
- **Async/await** throughout the codebase
- **Batch processing** for bulk operations
- **Redis caching** for frequently accessed data
- **Semaphore limits** to prevent resource exhaustion

---

## 🗂️ Project Structure

```
TeleGen/
├── src/
│   ├── bot/                    # Telegram bot application
│   │   ├── handlers/           # Message and callback handlers
│   │   ├── dialogs/            # Aiogram dialogs (FSM)
│   │   ├── services/           # Business logic services
│   │   ├── database/           # Database models and repositories
│   │   └── watcher.py          # Bot entry point
│   │
│   ├── admin_panel/            # Django admin application
│   │   ├── models.py           # Django ORM models
│   │   ├── admin.py            # Admin interface config
│   │   ├── views.py            # Web views
│   │   └── migrations/         # Database migrations
│   │
│   ├── core/                   # Core settings and config
│   │   ├── settings/           # Django settings (dev/prod)
│   │   ├── celery_app.py       # Celery configuration
│   │   └── wsgi.py             # WSGI entry point
│   │
│   └── manage.py               # Django management script
│
├── deployments/                # Deployment configurations
│   ├── docker-compose.yml      # Docker services
│   └── Dockerfile              # Multi-stage build
│
├── media/                      # Uploaded media files
├── staticfiles/                # Collected static files
├── logs/                       # Application logs
├── sessions/                   # Telegram userbot sessions
│
├── .env                        # Environment variables
├── Makefile                    # Common commands
├── pyproject.toml              # Python dependencies
├── README.md                   # This file
└── POST_SAVING_IMPROVEMENTS.md # Technical documentation
```

---

## 🔧 Development

### Local Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Start services**
   ```bash
   docker-compose up -d db redis
   ```

4. **Run migrations**
   ```bash
   cd src
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   # Terminal 1: Django
   python manage.py runserver

   # Terminal 2: Celery Worker
   celery -A core.celery_app worker -l info

   # Terminal 3: Celery Beat
   celery -A core.celery_app beat -l info

   # Terminal 4: Bot
   python bot/watcher.py
   ```

### Code Style

This project follows PEP 8 and uses:
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

Run all checks:
```bash
make lint
```

---

## 🚢 Deployment

### Docker Deployment

1. **Build images**
   ```bash
   docker-compose -f deployments/docker-compose.yml build
   ```

2. **Start services**
   ```bash
   docker-compose -f deployments/docker-compose.yml up -d
   ```

3. **Check status**
   ```bash
   docker-compose -f deployments/docker-compose.yml ps
   ```

### Production Considerations

- Set `DEBUG=False` in production
- Use strong `SECRET_KEY`
- Configure proper `ALLOWED_HOSTS`
- Set up HTTPS with valid SSL certificates
- Configure `CSRF_TRUSTED_ORIGINS` with your domains
- Use environment-specific settings (see `core/settings/`)
- Set up monitoring and log aggregation
- Regular database backups
- Secure API keys and tokens

---

## 📈 Monitoring & Troubleshooting

### Logs

View logs from all services:
```bash
make logs
```

View logs from specific service:
```bash
docker-compose logs -f bot
docker-compose logs -f admin_panel
docker-compose logs -f celery_worker
```

### Health Checks

Check service status:
```bash
docker-compose ps
```

Check database connectivity:
```bash
docker-compose exec admin_panel python manage.py check --database default
```

### Common Issues

**Migration errors:**
```bash
# Reset migrations (development only!)
docker-compose exec admin_panel python manage.py migrate admin_panel zero
make migrate
```

**CSRF errors:**
- Ensure `CSRF_TRUSTED_ORIGINS` includes your domain with protocol (http:// or https://)
- Check `ALLOWED_HOSTS` includes your domain

**Celery tasks not running:**
- Check Redis connectivity
- Verify Celery worker is running
- Check Celery Beat for scheduled tasks

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow the existing code style
- Update documentation as needed
- Keep commits atomic and well-described

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Fyodor Lukashov**

- Telegram: [@technosexuall](https://t.me/technosexuall)
- GitHub: [@atljh](https://github.com/atljh)

---

## 🙏 Acknowledgments

- [Aiogram](https://aiogram.dev/) - Modern Telegram Bot framework
- [Django](https://www.djangoproject.com/) - Web framework
- [Celery](https://docs.celeryproject.org/) - Distributed task queue
- [OpenAI](https://openai.com/) - AI API

---


### Recent Updates

- ✅ **Transaction safety** for post creation
- ✅ **Race condition fixes** for duplicate prevention
- ✅ **Media validation** before post commits
- ✅ **Database indexes** for improved performance
- ✅ **CSRF configuration fix** for Django 4.0+
- ✅ **Improved error handling** and cleanup

---

## 🔮 Roadmap

- [ ] Web interface for content management
- [ ] Multi-channel cross-posting
- [ ] Advanced analytics dashboard
- [ ] A/B testing for post content
- [ ] Content calendar visualization
- [ ] Webhook support for external integrations
- [ ] Mobile app (iOS/Android)

---

