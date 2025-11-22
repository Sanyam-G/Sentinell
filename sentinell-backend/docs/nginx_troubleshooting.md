# Nginx Troubleshooting Guide

## Common Nginx Errors and Solutions

### 502 Bad Gateway

A 502 Bad Gateway error indicates that nginx cannot reach the upstream service.

**Common Causes:**
1. Syntax error in nginx.conf
2. Upstream service is down
3. Firewall blocking connection
4. Wrong upstream port configuration

**How to diagnose:**
- Run `nginx -t` to test configuration syntax
- Check nginx error logs: `/var/log/nginx/error.log`
- Verify upstream service is running: `curl http://upstream_host:port`
- Check nginx access logs for patterns

**How to fix:**
1. If syntax error:
   - Review nginx.conf for typos
   - Common mistakes: missing semicolons, wrong brackets
   - Fix the syntax error
   - Run `nginx -t` to verify
   - Reload: `nginx -s reload`

2. If upstream is down:
   - Restart the upstream service
   - Check service logs for errors
   - Verify network connectivity

### Configuration Syntax Errors

**Symptoms:**
- nginx fails to start or reload
- Error: "unexpected end of file"
- Error: "unknown directive"

**Common Syntax Errors:**
- Missing semicolon `;` at end of directives
- Unmatched curly braces `{}`
- Typos in directive names
- Invalid values for directives

**How to test config:**
```bash
nginx -t
```

This will show exactly which line has the error.

**How to fix:**
1. Locate the line number from `nginx -t` output
2. Open nginx.conf
3. Check for:
   - Missing semicolons
   - Typo in directive name
   - Unmatched brackets
4. Fix the error
5. Test again with `nginx -t`
6. Reload: `nginx -s reload`

### Memory Issues

**Symptoms:**
- Container gets OOM killed
- Slow response times
- High memory usage in stats

**How to diagnose:**
- Check container stats: `docker stats <container>`
- Look for memory leaks in application
- Check nginx worker_processes and worker_connections

**How to fix:**
1. Reduce worker_processes if too high
2. Set worker_rlimit_nofile appropriately
3. Check for memory leaks in upstream applications
4. Increase container memory limit if needed
5. Restart container to clear leaked memory

### Port Conflicts

**Symptoms:**
- nginx fails to start
- Error: "address already in use"
- Container repeatedly restarting

**How to diagnose:**
```bash
# Check what's using the port
lsof -i :80
netstat -tulpn | grep :80
```

**How to fix:**
1. Identify the conflicting process
2. Kill the rogue process: `kill <PID>`
3. Or change nginx to use different port
4. Restart nginx

### Service Not Starting

**Symptoms:**
- Container status shows "Exited"
- nginx process not running

**How to diagnose:**
- Check container logs: `docker logs <container>`
- Look for error messages
- Check if config file exists
- Verify file permissions

**Common causes:**
1. Configuration error - use `nginx -t`
2. Missing config file
3. Permission denied on log files
4. Port already in use

### Best Practices for Fixes

1. **Always test before applying:**
   - Use `nginx -t` to test config
   - Create backups before modifying

2. **Reload, don't restart:**
   - Use `nginx -s reload` for config changes
   - This maintains active connections

3. **Check logs first:**
   - error.log has detailed error messages
   - access.log shows request patterns

4. **Verify the fix:**
   - Test the endpoint after fixing
   - Monitor logs for recurring errors
   - Check metrics to confirm resolution

## Quick Reference Commands

```bash
# Test nginx config
nginx -t

# Reload nginx config
nginx -s reload

# Stop nginx
nginx -s stop

# View error logs
tail -f /var/log/nginx/error.log

# View access logs
tail -f /var/log/nginx/access.log

# Check nginx status
ps aux | grep nginx

# Find process using port
lsof -i :80
```
