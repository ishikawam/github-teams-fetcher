# Contributing Guide

Thank you for considering contributing to the GitHub Teams Fetcher project!

## 🌟 How to Contribute

### 1. Reporting Issues
If you have bugs or improvement suggestions, first check [Issues](https://github.com/your-username/github-accounts/issues).

#### Bug Reports
Please include the following information:
- **Environment**: OS, Python version, GitHub CLI version
- **Reproduction Steps**: Specific steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Error Messages**: Related error messages or logs

#### Feature Requests
Please include the following information:
- **Background**: Why this feature is needed
- **Detailed Specification**: What kind of functionality you expect
- **Use Cases**: Specific usage scenarios

### 2. Code Contributions

#### Development Environment Setup

```bash
# 1. Fork the repository
# Please fork the repository on GitHub

# 2. Clone locally
git clone https://github.com/your-username/github-accounts.git
cd github-accounts

# 3. Add upstream repository
git remote add upstream https://github.com/original-username/github-accounts.git

# 4. Setup development environment
make install-gh
make install

# 5. Create configuration file (for testing)
make setup
```

#### Branching Strategy

- `main` branch is the stable version
- Feature additions use `feature/feature-name` branches
- Bug fixes use `fix/bug-description` branches
- Documentation updates use `docs/update-content` branches

```bash
# Branch creation examples
git checkout -b feature/add-new-export-format
git checkout -b fix/memory-leak-in-data-processing
git checkout -b docs/update-installation-guide
```

#### Coding Standards

##### Python Code
- Follow [PEP 8](https://pep8.org/) style guide
- Write docstrings for functions and classes
- Use type hints (Python 3.7+)
- Line length limit: 120 characters

```python
def fetch_team_members(org: str, team: str) -> List[Dict[str, Any]]:
    """Fetch team members for the specified organization.
    
    Args:
        org: GitHub organization name
        team: Team name
        
    Returns:
        List of member information
        
    Raises:
        APIError: When GitHub API error occurs
    """
    # Implementation...
```

##### Makefile
- Use tab indentation
- Explain the purpose of each target with comments
- Implement proper error handling

##### YAML Configuration Files
- Use 2-space indentation
- Explain configuration items with comments

#### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_config_loader.py -v

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

#### New Feature Addition Process

1. **Create Issue**: Discuss new features
2. **Create Branch**: Create branch with appropriate naming
3. **Implementation**: Follow coding standards
4. **Add Tests**: Add test cases for new features
5. **Update Documentation**: Update README or configuration examples
6. **Pull Request**: Create PR with detailed description

### 3. Documentation Improvements

Documentation improvements are also important contributions:

- README.md improvements
- Configuration examples additions
- Troubleshooting information additions
- Usage examples additions

## 📋 Pull Request Guidelines

### PR Creation Checklist

- [ ] Rebased to latest `main` branch
- [ ] All tests pass
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] Appropriate commit messages

### PR Description

Include the following information:

```markdown
## Summary
<!-- Briefly describe what was changed -->

## Reason for Changes
<!-- Explain why this change is necessary -->

## Testing Method
<!-- Explain how you tested this change -->

## Related Issues
<!-- Related issue numbers (e.g., Closes #123) -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] Added/updated tests
- [ ] Updated documentation
- [ ] Updated CHANGELOG.md (if applicable)
```

### Review Process

1. **Automated Checks**: Test execution via GitHub Actions
2. **Code Review**: Code verification by maintainers
3. **Address Feedback**: Make fixes as needed
4. **Merge**: Merge after approval

## 🤝 Community Guidelines

### Code of Conduct

- **Respect**: Respect other contributors and provide constructive feedback
- **Inclusion**: Welcome all contributors regardless of technical level
- **Collaboration**: Work collaboratively toward problem resolution
- **Learning**: Learn from mistakes and continue improving

### Communication

- **Issue Discussion**: Discuss major changes in Issues before implementation
- **Clear Explanations**: Be specific and clear in technical explanations
- **Prompt Response**: Provide feedback as quickly as possible

## 🎯 High Priority Contribution Areas

We especially welcome contributions in the following areas:

### 🔧 Technical Improvements
- **Performance Optimization**: Improve execution speed for large organizations
- **Error Handling**: More robust error processing
- **Parallel Processing**: Efficiency within GitHub API rate limits

### 📊 Feature Extensions
- **New Output Formats**: Support for Excel, PDF, etc.
- **Filtering Features**: Conditional specification for teams and members
- **Statistical Analysis**: More detailed analysis features

### 📚 Documentation
- **Usage Examples**: Real-world usage scenarios
- **Troubleshooting**: Solutions for common problems
- **Internationalization**: Create English version documentation

### 🧪 Testing
- **Integration Tests**: Tests using actual GitHub API
- **Edge Cases**: Add test cases for edge cases
- **Performance Tests**: Operation verification with large datasets

## 🏷️ Label Guide

We use the following labels for Issues and PRs:

| Label | Description |
|-------|-------------|
| `bug` | Bug reports |
| `enhancement` | New features or improvement suggestions |
| `documentation` | Documentation-related |
| `good first issue` | Issues suitable for beginners |
| `help wanted` | Issues seeking help |
| `question` | Questions or discussions |
| `wontfix` | Issues that won't be fixed |

## ❓ Questions and Support

- **General Questions**: [Discussions](https://github.com/your-username/github-accounts/discussions)
- **Bug Reports**: [Issues](https://github.com/your-username/github-accounts/issues)
- **Security**: For security-related issues, contact maintainers directly instead of using Issues

---

If you have any questions about contributing, feel free to create an Issue or ask in existing Discussions. We look forward to your participation! 🚀
