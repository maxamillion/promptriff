# Security Best Practices

## Overview

PromptRiff handles sensitive data including API keys, conversation history, and potentially confidential prompts. This guide outlines security best practices for using PromptRiff safely.

## API Key Security

### Storage Best Practices

1. **Use Environment Variables**
   ```bash
   # Preferred method
   export OPENAI_API_KEY="sk-..."
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

2. **Secure Configuration Files**
   ```bash
   # Set restrictive permissions
   chmod 600 ~/.config/promptriff/config.yaml
   
   # Verify permissions
   ls -la ~/.config/promptriff/config.yaml
   # Should show: -rw-------
   ```

3. **Never Commit Keys**
   - Add `.env` to `.gitignore`
   - Use `.env.example` for templates
   - Review commits before pushing

### Key Rotation

Regularly rotate API keys:
1. Generate new keys from provider dashboards
2. Update configuration
3. Revoke old keys
4. Test new keys work correctly

## Data Security

### Database Protection

1. **File Permissions**
   ```bash
   chmod 600 ~/.local/share/promptriff/promptriff.db
   ```

2. **Regular Backups**
   ```yaml
   database:
     backup_on_startup: true
   ```

3. **Encryption**
   - Use full-disk encryption
   - Consider SQLite encryption extensions
   - Encrypt backups separately

### Sensitive Conversations

1. **Clear Sensitive Data**
   - Use `Ctrl+N` to start new conversations
   - Manually delete sensitive records
   - Clear export files after use

2. **Export Security**
   - Be cautious with export locations
   - Encrypt exported files
   - Delete exports when no longer needed

## MCP Tool Security

### Tool Validation

1. **Verify Tool Sources**
   - Only install tools from trusted sources
   - Check tool signatures if available
   - Review tool documentation

2. **Restrict Tool Access**
   ```yaml
   mcp_tools:
     - name: filesystem
       config:
         allowed_directories:
           - ~/safe_directory  # Restrict to specific dirs
         forbidden_paths:
           - ~/.ssh
           - ~/.gnupg
   ```

3. **Disable Unused Tools**
   ```yaml
   mcp_tools:
     - name: dangerous_tool
       enabled: false  # Explicitly disable
   ```

### Tool Permissions

1. **Principle of Least Privilege**
   - Grant minimum necessary permissions
   - Avoid running tools as root
   - Use separate user accounts if needed

2. **Monitor Tool Activity**
   - Review tool logs regularly
   - Watch for unexpected behavior
   - Set up alerts for anomalies

## Network Security

### API Communication

1. **TLS/SSL Verification**
   - PromptRiff enforces SSL by default
   - Never disable certificate verification
   - Use custom CAs properly

2. **Proxy Configuration**
   ```bash
   export HTTPS_PROXY="https://proxy.company.com:8080"
   export SSL_CERT_FILE="/path/to/ca-bundle.crt"
   ```

3. **Firewall Rules**
   - Whitelist AI provider endpoints
   - Block unnecessary outbound traffic
   - Monitor connection logs

### Rate Limiting

Protect against accidental key exposure:
1. Set spending limits in provider dashboards
2. Monitor usage regularly
3. Configure alerts for unusual activity

## Input Validation

### Prompt Sanitization

PromptRiff automatically:
- Validates input length
- Prevents injection attacks
- Handles special characters safely

### File Path Security

When using file-related tools:
- Absolute paths are validated
- Path traversal is prevented
- Symlinks are resolved safely

## Logging and Monitoring

### Log Security

1. **Sensitive Data**
   - API keys are never logged
   - Responses are truncated in logs
   - User data is anonymized

2. **Log Rotation**
   ```bash
   # Configure log rotation
   logrotate /etc/logrotate.d/promptriff
   ```

3. **Log Access**
   ```bash
   chmod 640 ~/.local/share/promptriff/logs/*.log
   ```

### Monitoring

1. **Activity Monitoring**
   - Track API usage
   - Monitor error rates
   - Watch for suspicious patterns

2. **Alerts**
   - Set up usage alerts
   - Configure error notifications
   - Monitor security events

## Security Checklist

### Initial Setup
- [ ] Set restrictive file permissions on config
- [ ] Use environment variables for API keys
- [ ] Enable database backups
- [ ] Configure firewall rules
- [ ] Set up log rotation

### Regular Maintenance
- [ ] Rotate API keys quarterly
- [ ] Review tool permissions
- [ ] Audit conversation history
- [ ] Update dependencies
- [ ] Check for security updates

### Incident Response
- [ ] Revoke compromised keys immediately
- [ ] Change all related passwords
- [ ] Review logs for unauthorized access
- [ ] Report incidents to providers
- [ ] Document lessons learned

## Compliance Considerations

### Data Retention

1. **Automatic Cleanup**
   ```python
   # Configure retention policies
   retention_days = 90
   ```

2. **Manual Cleanup**
   - Regular database maintenance
   - Archive old conversations
   - Delete unnecessary exports

### Privacy

1. **User Data**
   - Minimize data collection
   - Anonymize where possible
   - Respect user preferences

2. **Third-Party Services**
   - Understand provider policies
   - Review data processing agreements
   - Ensure compliance with regulations

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do Not** create a public issue
2. **Email** security@promptriff.example.com
3. **Include**:
   - Description of the issue
   - Steps to reproduce
   - Potential impact
   - Suggested fixes

We aim to respond within 48 hours and provide fixes promptly.

## Additional Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
- Provider-specific security docs:
  - [OpenAI Security](https://openai.com/security)
  - [Anthropic Security](https://www.anthropic.com/security)
  - [Google AI Security](https://cloud.google.com/security)