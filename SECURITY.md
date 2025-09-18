# Security Policy

## Supported Versions

We actively support the latest version of GitHub Teams Fetcher with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. **DO NOT** create a public GitHub issue

Security vulnerabilities should not be reported through public GitHub issues.

### 2. Report privately

Please report security vulnerabilities through one of these methods:

- **Email**: Send details to [security@anthropic.com](mailto:security@anthropic.com)
- **GitHub Security Advisories**: Use the "Report a vulnerability" button in the Security tab

### 3. Include the following information

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### 4. Response timeline

- **Acknowledgment**: We'll acknowledge receipt within 24 hours
- **Initial assessment**: We'll provide an initial assessment within 72 hours
- **Regular updates**: We'll keep you informed of progress at least weekly
- **Resolution**: We aim to resolve critical security issues within 90 days

## Security Best Practices

### For Users

1. **Keep dependencies updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Secure your GitHub authentication**
   - Use GitHub CLI authentication (`gh auth login`)
   - Never commit GitHub tokens to version control
   - Regularly rotate access tokens

3. **Protect sensitive data**
   - Keep `config.yaml` private (already gitignored)
   - Be mindful that fetched data may contain personal information
   - Follow your organization's data handling policies

4. **Validate configuration**
   ```bash
   make config-check
   ```

### For Contributors

1. **Dependencies**
   - Only add dependencies that are actively maintained
   - Verify package authenticity before adding to requirements.txt
   - Run `pip-audit` or similar tools to check for known vulnerabilities

2. **Code practices**
   - Sanitize all external inputs
   - Use parameterized commands to prevent injection attacks
   - Follow the principle of least privilege

3. **Testing**
   - Include security test cases
   - Test with various input scenarios including edge cases
   - Validate error handling doesn't leak sensitive information

## Known Security Considerations

### 1. GitHub API Access

This tool requires GitHub API access through GitHub CLI. Users should:

- Ensure they have appropriate permissions for target organizations
- Be aware of API rate limits (5,000 requests/hour for authenticated users)
- Understand that some team information may not be accessible due to permissions

### 2. Data Privacy

- **Personal Information**: Team member data may include personal information
- **Data Storage**: All fetched data is stored locally in the `storage/` directory
- **Data Retention**: Users are responsible for managing data retention according to their policies

### 3. Network Security

- **HTTPS**: All GitHub API communications use HTTPS
- **Authentication**: GitHub CLI handles secure authentication
- **No credentials stored**: This tool does not store GitHub credentials

### 4. Local File Security

- **File permissions**: Ensure appropriate file system permissions on sensitive directories
- **Backup security**: If backing up data, ensure backups are secured appropriately
- **Cleanup**: Use `make clean` to remove cached data when no longer needed

## Security Features

### 1. Input Validation

- Configuration files are validated against expected schemas
- Organization names are sanitized before API calls
- File paths are validated to prevent directory traversal

### 2. Error Handling

- Sensitive information is not included in error messages
- Failed API calls are logged without exposing credentials
- Graceful degradation when permissions are insufficient

### 3. Dependency Management

- Minimal dependency footprint
- Regular dependency updates through Dependabot
- Security scanning in CI/CD pipeline

### 4. Data Protection

- No credentials stored in application code
- Configuration files excluded from version control
- Temporary files cleaned up appropriately

## Compliance

This tool is designed to be compliant with:

- **GDPR**: Personal data handling guidelines
- **SOC 2**: Security and availability standards
- **GitHub's Terms of Service**: API usage guidelines

## Security Checklist for Deployment

- [ ] GitHub CLI is authenticated and tokens are secured
- [ ] `config.yaml` contains only necessary organization names
- [ ] File system permissions are appropriately restrictive
- [ ] Regular updates are scheduled for dependencies
- [ ] Data retention policies are documented and followed
- [ ] Access to generated reports is controlled appropriately

## Contact

For security-related questions or concerns, please contact:

- **Email**: [security@anthropic.com](mailto:security@anthropic.com)
- **GitHub**: Use the Security tab in this repository

---

**Note**: This security policy is regularly reviewed and updated. Please check back periodically for the latest guidelines.
