# Security Policy

## Reporting Security Issues

**Do not open public issues for security vulnerabilities.**

If you discover a security vulnerability in NPersona, please email npersona.ai@gmail.com with:

1. **Description**: Clear explanation of the vulnerability
2. **Affected Components**: Which parts of the code are affected
3. **Impact**: Potential impact and severity
4. **Proof of Concept**: Steps to reproduce (if applicable)
5. **Suggested Fix**: Optional proposed solution

We will:
- Acknowledge receipt within 48 hours
- Provide an estimated timeline for fix
- Keep you updated on progress
- Credit you in the security advisory (if desired)

## Security Practices

### Code Security

- All code undergoes security review before merge
- Type checking enforced for type safety
- Input validation on all external data
- No secrets in version control
- Dependencies regularly audited

### Dependency Management

- Pin dependency versions in `requirements.txt`
- Regular updates for security patches
- Vulnerability scanning in CI/CD
- Minimal dependencies to reduce attack surface

### API Security

- HTTPS enforced for all external connections
- Certificate verification enabled
- No hardcoded credentials
- Secrets passed via environment variables
- OAuth2 token refresh with 60-second buffer
- Rate limiting and retry logic

### Data Handling

- Test data treated as sensitive
- Temporary files cleaned up
- No logging of authentication tokens
- Response sanitization
- Privacy-first design

## Security Testing

NPersona itself is built for security testing, therefore:

1. **Self-Testing**: Regularly test our own framework
2. **Penetration Testing**: Annual external security audits
3. **Dependency Scanning**: Automated vulnerability checks
4. **Code Analysis**: Static security analysis in CI/CD

## Secure Usage

When using NPersona, please:

1. **Protect Credentials**: Keep API keys and tokens secure
   - Use environment variables, not hardcoded values
   - Rotate credentials regularly
   - Use separate credentials for different environments

2. **Access Control**: Limit who can access security reports
   - Reports may contain sensitive findings
   - Restrict report distribution to authorized personnel
   - Use secure channels for sharing reports

3. **Data Retention**: Manage test data lifecycle
   - Securely delete old reports
   - Archive sensitive findings separately
   - Follow data retention policies

4. **Configuration**: Secure your configuration
   - Use HTTPS for all endpoints
   - Validate SSL certificates
   - Use authenticated endpoints only

## Known Limitations

1. **Rate Limiting**: API rate limits may affect large-scale testing
2. **Timeout Handling**: Network issues may cause test failures
3. **LLM Reliability**: LLM quality directly impacts test quality
4. **False Negatives**: Some vulnerabilities may not be detected
5. **False Positives**: Some tests may trigger on benign behaviors

## Responsible Disclosure

If you find vulnerabilities in systems tested with NPersona:

1. **Report Privately**: Contact the system owner directly
2. **Avoid Public Disclosure**: Don't post findings publicly
3. **Give Time**: Allow reasonable time for fixing (typically 90 days)
4. **Document Everything**: Keep detailed records of findings
5. **Follow Policy**: Comply with responsible disclosure practices

## Updates and Patches

- Security patches released immediately
- Regular version releases include security improvements
- Critical issues may trigger emergency releases
- Subscribe to security advisories at github.com/NPersona-AI/npersona/security/advisories

## Compliance

NPersona is designed to support:
- OWASP Security Standards
- NIST AI Security Framework
- ISO 27001 Information Security
- SOC 2 compliance requirements

## Contact

- **Security Issues**: npersona.ai@gmail.com
- **GitHub Issues**: https://github.com/NPersona-AI/npersona/issues
- **GitHub Discussions**: https://github.com/NPersona-AI/npersona/discussions

## Acknowledgments

We appreciate the security research community and thank those who responsibly report vulnerabilities.

---

**Last Updated**: 2026-04-12  
**Version**: 1.0.0
