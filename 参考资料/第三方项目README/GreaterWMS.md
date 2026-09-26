# SOURCE: GreaterWMS/GreaterWMS  branch=master file=README.md

<div align="center">
  <img src="static/img/logo.png" alt="GreaterWMS logo" width="200" height="auto" />
  <h1>GreaterWMS</h1>
  <p>Fully Open Source Warehouse Management System</p>
  
  <!-- CI/CD Status Badges -->
  <p>
    <img src="https://github.com/dev00amk/GreaterWMS-amk/workflows/CI%20Pipeline/badge.svg" alt="CI Pipeline" />
    <img src="https://github.com/dev00amk/GreaterWMS-amk/workflows/Security%20Scan/badge.svg" alt="Security Scan" />
    <img src="https://github.com/dev00amk/GreaterWMS-amk/workflows/Release%20Drafter/badge.svg" alt="Release Drafter" />
  </p>
  
  <!-- Quality Badges -->
  <p>
    <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/Django-4.1.2-green.svg" alt="Django Version" />
    <img src="https://img.shields.io/badge/Node.js-16+-brightgreen.svg" alt="Node.js Version" />
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License" />
  </p>
</div></div>

The original vision for this software was to make it a framework that would facilitate warehouse management software development for everyone. However, we later discovered that we had written it as a complete software system, which was not what we intended.

Therefore, we have rewritten the underlying layer using Rust and Python as the carrier, creating a new CLI underlying framework called [Bomiot](https://github.com/Bomiot/Bomiot). It offers high performance and more convenient development, fully leveraging Python's inherent language advantages.

The old version of GreaterWMS files can be found here:
[GreaterWMS v2.1.49](https://github.com/GreaterWMS/GreaterWMS/tree/V2.1.49)

GreaterWMS will also use [Bomiot](https://github.com/Bomiot/Bomiot) for its 3.0 reconstruction.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+ (for production)
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/dev00amk/GreaterWMS-amk.git
   cd GreaterWMS-amk
   ```

2. **Backend Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Run migrations
   python manage.py migrate

   # Create superuser
   python manage.py createsuperuser

   # Start development server
   python manage.py runserver
   ```

3. **Frontend Setup**
   ```bash
   cd templates
   npm install
   npm run dev  # or quasar dev
   ```

4. **Docker Setup (Alternative)**
   ```bash
   # Start all services
   docker-compose up -d

   # View logs
   docker-compose logs -f
   ```

## 🧪 Testing & Quality Assurance

### Running Tests Locally

**Backend Tests:**
```bash
# Run all Django tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Run specific app tests
python manage.py test asn.tests
```

**Frontend Tests:**
```bash
cd templates
npm test
npm run lint
```

**Security Scanning:**
```bash
# Python security checks
pip install safety bandit
safety check -r requirements.txt
bandit -r . --exclude=./venv,./migrations

# Frontend security audit
cd templates
npm audit
```

### CI/CD Pipeline

Our CI/CD pipeline automatically runs on every pull request and includes:

#### 🔍 **Quality Gates**
- ✅ Python code linting (flake8)
- ✅ Frontend code linting (ESLint)
- ✅ Django system checks
- ✅ Migration checks
- ✅ Unit tests (Django + Frontend)
- ✅ Integration tests
- ✅ Security vulnerability scanning
- ✅ Docker build tests

#### 🔒 **Security Scanning**
- **Dependency Scanning**: Safety, pip-audit, npm audit
- **Code Security**: Bandit, Semgrep
- **Secrets Detection**: TruffleHog
- **Docker Security**: Trivy (when applicable)

#### 📦 **Build Verification**
- Docker image builds
- Docker Compose configuration validation
- Static file collection
- Frontend build process

### Running CI Locally

**Using Docker Compose for CI:**
```bash
# Test the CI pipeline locally
docker-compose -f docker-compose.ci.yml up --build

# Run specific CI tests
docker-compose -f docker-compose.ci.yml run backend-test python manage.py test
docker-compose -f docker-compose.ci.yml run frontend-test npm test
```

**Manual CI Steps:**
```bash
# Backend CI steps
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
flake8 . --max-line-length=100 --exclude=migrations
python manage.py test

# Frontend CI steps
cd templates
npm ci
npm run lint
npm test
npm run build  # if build script exists
```

## 📋 Development Workflow

1. **Create a feature branch**: `git checkout -b feature/your-feature-name`
2. **Make your changes** following our [coding guidelines](docs/PR_GUIDELINES.md)
3. **Run tests locally**: Ensure all tests pass before pushing
4. **Commit changes**: Use [Conventional Commits](https://www.conventionalcommits.org/) format
5. **Push and create PR**: Use our [PR template](.github/PULL_REQUEST_TEMPLATE.md)
6. **Code review**: Address feedback and ensure CI passes
7. **Merge**: Once approved, PR will be merged using squash and merge

### Helper Scripts

Use our PR helper script to automate testing and PR creation:
```bash
# Run tests and create PR
./scripts/make_pr.sh

# With specific target branch
./scripts/make_pr.sh develop "feat: add new inventory feature"
```

## 🛠️ Development Tools

### Recommended IDE Setup
- **VS Code** with Python, Django, and Vue.js extensions
- **PyCharm Professional** for Django development
- **WebStorm** for frontend development

### Code Quality Tools
```bash
# Install development tools
pip install flake8 black isort pre-commit
npm install -g eslint prettier

# Set up pre-commit hooks
pre-commit install
```

## 📖 Documentation

- **[Contributing Guidelines](docs/PR_GUIDELINES.md)** - How to contribute to the project
- **[Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md)** - PR template and checklist
- **[Security Policy](SECURITY.md)** - Security reporting and best practices
- **[Changelog](CHANGELOG.md)** - Version history and release notes

## 🐛 Troubleshooting

### Common Issues

**Database Connection Issues:**
```bash
# Reset database
python manage.py flush
python manage.py migrate
```

**Frontend Build Issues:**
```bash
cd templates
rm -rf node_modules package-lock.json
npm install
```

**Docker Issues:**
```bash
# Reset Docker environment
docker-compose down -v
docker system prune -f
docker-compose up --build
```

### Getting Help

- 📖 Check our [documentation](docs/)
- 🐛 [Report bugs](https://github.com/dev00amk/GreaterWMS-amk/issues)
- 💬 [Discussions](https://github.com/dev00amk/GreaterWMS-amk/discussions)
- 📧 Contact: [maintainer@example.com](mailto:maintainer@example.com)