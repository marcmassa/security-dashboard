# Contributing to Security Dashboard

Thank you for your interest in contributing to the Security Dashboard project! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Git
- Basic knowledge of Flask, JavaScript, and security tools

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/security-dashboard.git
   cd security-dashboard
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Database**
   ```bash
   # Create PostgreSQL database
   createdb security_dashboard_dev
   
   # Set environment variables
   export DATABASE_URL="postgresql://user:password@localhost/security_dashboard_dev"
   export SESSION_SECRET="your-development-secret-key"
   ```

5. **Initialize Database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

6. **Run Development Server**
   ```bash
   python main.py
   ```

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise

### Frontend Guidelines
- Use Bootstrap 5 classes for styling
- Write semantic HTML
- Ensure responsive design
- Test across different browsers

### Security Considerations
- Validate all user inputs
- Use parameterized queries for database operations
- Implement proper authentication and authorization
- Follow OWASP security guidelines

## Contributing Process

### 1. Create an Issue
Before starting work, create an issue describing:
- The problem you're solving
- Your proposed solution
- Any breaking changes

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Make Changes
- Write clean, well-documented code
- Add tests for new functionality
- Update documentation as needed
- Ensure all existing tests pass

### 4. Test Your Changes
```bash
# Run tests (if available)
python -m pytest

# Test manually with different scenarios
# - Upload various report formats
# - Test API endpoints
# - Verify UI responsiveness
```

### 5. Commit Changes
Use clear, descriptive commit messages:
```bash
git commit -m "Add: Interactive security risk heatmap visualization"
git commit -m "Fix: Resolve footer positioning issue"
git commit -m "Update: Improve SonarQube API error handling"
```

### 6. Submit Pull Request
- Push your branch to your fork
- Create a pull request with:
  - Clear description of changes
  - Screenshots for UI changes
  - Testing instructions
  - Reference to related issues

## Types of Contributions

### 🐛 Bug Fixes
- Fix reported issues
- Improve error handling
- Resolve performance problems

### ✨ New Features
- Security analysis enhancements
- New visualization options
- API improvements
- Integration with additional tools

### 📚 Documentation
- Improve README
- Add code comments
- Create user guides
- Update API documentation

### 🎨 UI/UX Improvements
- Enhance user interface
- Improve accessibility
- Mobile responsiveness
- Visual design updates

### 🔧 Technical Improvements
- Code refactoring
- Performance optimization
- Security enhancements
- Test coverage

## Feature Requests

When proposing new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Explain the benefits** to users
4. **Consider implementation complexity**
5. **Provide mockups** for UI features

## Reporting Bugs

Include in your bug report:
- **Steps to reproduce** the issue
- **Expected behavior**
- **Actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, browser, Python version)
- **Error messages** or logs

## Security Vulnerabilities

For security issues:
- **Do not** create public issues
- Email security concerns privately
- Provide detailed reproduction steps
- Allow time for fixes before public disclosure

## Review Process

Pull requests are reviewed for:
- **Code quality** and style
- **Security implications**
- **Performance impact**
- **Documentation completeness**
- **Test coverage**
- **Backward compatibility**

## Getting Help

- **Issues**: General questions and problems
- **Discussions**: Feature ideas and architecture questions
- **Documentation**: Check existing docs first
- **Community**: Be respectful and constructive

## Recognition

Contributors are recognized through:
- Credits in release notes
- Contributor list in README
- GitHub contributor statistics

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make Security Dashboard better for everyone!