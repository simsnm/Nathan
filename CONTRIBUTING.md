# 🤝 Contributing to AI Mentor Platform

Thank you for your interest in contributing to AI Mentor Platform! This document provides guidelines and instructions for contributing.

## 🎯 Our Philosophy

- **Simplicity over complexity**: Every line of code should earn its place
- **User value first**: Features must solve real problems
- **Test everything**: If it's not tested, it's broken
- **Clear communication**: Code should be self-documenting when possible

## 🚀 Getting Started

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then:
   git clone https://github.com/YOUR_USERNAME/ai-mentor.git
   cd ai-mentor
   git remote add upstream https://github.com/original/ai-mentor.git
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Run Tests**
   ```bash
   pytest tests/
   ```

## 📝 How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Screenshots if applicable

**Template:**
```markdown
**Description:**
Brief description of the bug

**Steps to Reproduce:**
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- Browser: [if applicable]
```

### Suggesting Features

Feature requests are welcome! Please provide:

- Clear use case
- Expected behavior
- Why this would benefit users
- Possible implementation approach

### Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number
   ```

2. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation if needed
   - Keep commits focused and atomic

3. **Code Style Guidelines**

   **Python:**
   ```python
   # Good: Clear, simple, documented
   def calculate_cost(tokens: int, model: str) -> float:
       """Calculate API cost based on token count and model."""
       rates = {
           "gpt-3.5": 0.001,
           "gpt-4": 0.03,
           "claude": 0.01
       }
       return tokens * rates.get(model, 0.01) / 1000
   ```

   **Principles:**
   - Use type hints
   - Keep functions small (< 20 lines preferred)
   - Document complex logic
   - Prefer clarity over cleverness

4. **Test Your Changes**
   ```bash
   # Run all tests
   pytest tests/
   
   # Run specific test
   pytest tests/test_feature.py::test_specific
   
   # Check coverage
   pytest --cov=codechat tests/
   ```

5. **Commit Your Changes**
   ```bash
   # Use clear, conventional commit messages
   git commit -m "feat: add support for custom agents"
   git commit -m "fix: resolve API timeout issue #42"
   git commit -m "docs: update deployment guide"
   ```

   **Commit Message Format:**
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes
   - `refactor:` Code refactoring
   - `test:` Test additions/changes
   - `chore:` Maintenance tasks

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub with:
   - Clear description of changes
   - Link to related issue(s)
   - Screenshots/examples if applicable

## 🏗️ Project Structure

```
ai-mentor/
├── codechat.py           # Core CLI engine
├── demo_mode.py          # Demo responses
├── workflow.py           # Workflow automation
├── web_app/
│   ├── main.py          # FastAPI backend
│   ├── models.py        # Data models
│   ├── auth.py          # Authentication
│   └── database.py      # Database operations
├── web_frontend/
│   └── index.html       # Web interface
├── scripts/             # Deployment scripts
├── tests/              # Test suite
└── docs/              # Documentation
```

## ✅ Testing Requirements

All contributions must include appropriate tests:

```python
# Example test structure
def test_feature_normal_case():
    """Test normal operation."""
    result = my_function("input")
    assert result == "expected"

def test_feature_edge_case():
    """Test edge cases."""
    with pytest.raises(ValueError):
        my_function("")

def test_feature_error_handling():
    """Test error conditions."""
    result = my_function(None)
    assert result is None
```

## 🎨 Areas for Contribution

### Good First Issues
- Add more demo responses
- Improve error messages
- Add input validation
- Enhance documentation
- Write more tests

### Feature Ideas
- Custom agent creation
- Plugin system
- IDE integrations
- Additional language support
- Workflow templates

### Performance
- Query optimization
- Caching improvements
- Response streaming
- Batch processing

## 🚫 What We Won't Accept

- Features that significantly increase complexity without clear value
- Code without tests
- Breaking changes without migration path
- Dependencies with restrictive licenses
- Features that compromise security or privacy

## 📋 Review Process

1. Automated checks must pass (tests, linting)
2. Code review by maintainer
3. Discussion/iteration if needed
4. Merge when approved

**Review Criteria:**
- Code quality and style
- Test coverage
- Documentation
- Performance impact
- Security implications

## 💡 Development Tips

### Running Locally
```bash
# Start backend
python web_app/main.py

# In another terminal, test CLI
python codechat.py --demo "test message"

# Run specific agent
python codechat.py --role mentor --demo "explain closures"
```

### Debugging
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Processing: {data}")
```

### Performance Testing
```bash
# Profile code
python -m cProfile -s time codechat.py

# Memory profiling
python -m memory_profiler codechat.py
```

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🙋 Questions?

- Open a [Discussion](https://github.com/yourusername/ai-mentor/discussions)
- Check existing [Issues](https://github.com/yourusername/ai-mentor/issues)
- Read the [Documentation](docs/)

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in relevant documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to AI Mentor Platform! Together, we're building better tools for developers worldwide.** 🚀