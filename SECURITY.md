# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

Only the latest release version receives security updates. We recommend always running the most recent version.

## Reporting a Vulnerability

We take security seriously at BookSwipe. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **Do NOT open a public GitHub issue** for security vulnerabilities.
2. Email your findings to **security@bookswipe.example.com** (replace with your actual security contact).
3. Include the following in your report:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours.
- **Assessment**: We will investigate and validate the vulnerability within 5 business days.
- **Resolution**: We aim to release a fix within 30 days of validation, depending on complexity.
- **Disclosure**: We will coordinate with you on public disclosure timing after a fix is available.

### Safe Harbor

We consider security research conducted in accordance with this policy to be:
- Authorized under applicable anti-hacking laws
- Exempt from DMCA restrictions on circumvention
- Conducted in good faith

We will not pursue legal action against researchers who follow this policy.

## Security Best Practices for Deployment

### Environment Configuration

- **Never** commit `.env` files or secrets to version control.
- Use `.env.production.example` as a template; copy to `.env` and fill in real values.
- Generate strong, unique values for `SECRET_KEY` (minimum 32 characters, cryptographically random).
- Set `DEBUG=false` in production.

### Authentication and JWT

- Use short-lived access tokens (`ACCESS_TOKEN_EXPIRE_MINUTES=15` recommended).
- Rotate `SECRET_KEY` periodically and have a key rotation strategy.
- Use HTTPS exclusively in production to protect tokens in transit.

### Database

- Use PostgreSQL (not SQLite) in production.
- Use strong, unique database passwords.
- Restrict database network access to only the application server.
- Enable SSL/TLS for database connections.

### Docker and Container Security

- Use pinned, specific image versions (not `latest` tags).
- Run containers as non-root users.
- Scan images regularly for vulnerabilities (e.g., Trivy, Snyk).
- Use multi-stage builds to minimize final image size and attack surface.
- Do not store secrets in Docker images or Dockerfiles.

### Network and CORS

- Restrict `CORS_ORIGINS` to your specific domain(s) in production.
- Use a reverse proxy (e.g., nginx) with rate limiting.
- Enable HTTPS with valid TLS certificates (e.g., Let's Encrypt).
- Configure appropriate security headers (HSTS, CSP, X-Frame-Options).

### Rate Limiting

- Enable rate limiting on authentication endpoints to prevent brute-force attacks.
- Monitor and adjust rate limits based on traffic patterns.

### Monitoring and Logging

- Enable structured logging for security-relevant events.
- Monitor for unusual authentication patterns (failed logins, token reuse).
- Set up alerts for potential security incidents.
- Do not log sensitive data (passwords, tokens, API keys).

### Dependencies

- Regularly update dependencies to patch known vulnerabilities.
- Use `pip audit` or similar tools to scan for vulnerable packages.
- Pin dependency versions for reproducible builds.

## Contact

For security-related inquiries, contact:

- **Email**: security@bookswipe.example.com
- **Response Time**: Within 48 hours

Please replace the placeholder email addresses above with your actual security contact information before deploying.
