# Browser Use Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. Build Fails During System Dependencies Installation

**Error**: `E: Package 'libnss3' has no installation candidate`

**Solution**: Sevalla environment might be using a different base image. Try this alternative in sevalla.yaml:

```yaml
build:
  commands:
    - "apt-get update && apt-get install -y curl wget"
    - "curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add -"
    - "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list"
    - "apt-get update && apt-get install -y google-chrome-stable"
    - "pip install -r requirements.txt"
    - "playwright install chromium --with-deps --verbose"
```

### 2. Browser Installation Succeeds but Launch Still Fails

**Check**: Environment variables are properly set in Sevalla dashboard:
- `PLAYWRIGHT_BROWSERS_PATH=/home/app/.cache/ms-playwright`
- `DISABLE_DEV_SHM_USAGE=true`
- `DEBUG=pw:browser`

### 3. Permission Issues

**Error**: `Permission denied` when accessing browser files

**Solution**: Add to sevalla.yaml build commands:
```yaml
- "chmod -R 755 /home/app/.cache/ms-playwright"
- "chown -R app:app /home/app/.cache/ms-playwright"
```

### 4. Memory Issues

**Error**: Browser crashes or `Out of memory`

**Solution**: 
1. Increase memory in sevalla.yaml to 4GB
2. Add `--single-process` to browser args in rappi_agent.py

### 5. Alternative: Use Chromium Binary Directly

If Playwright installation continues to fail, modify rappi_agent.py:

```python
# Alternative browser configuration
self.browser_profile = BrowserProfile(
    headless=headless_mode,
    viewport_size={"width": 1920, "height": 1080},
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    browser_args=browser_args,
    browser_type="chromium",
    executable_path="/usr/bin/google-chrome-stable"  # Use system chrome
)
```

### 6. Debug Commands

Run these in Sevalla console if available:

```bash
# Check browser installation
playwright --version
ls -la ~/.cache/ms-playwright/

# Test browser launch manually
python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright(); p.start(); browser = p.chromium.launch(headless=True); print('Success'); browser.close()"

# Check system dependencies
ldd /usr/bin/google-chrome-stable
```

### 7. Contact Sevalla Support

If none of the above work, contact Sevalla support with:

1. **Your sevalla.yaml configuration**
2. **Build logs showing browser installation**
3. **Runtime logs showing the FileNotFoundError**
4. **Request**: "Need help with browser automation deployment - chromium binary not found"

Sevalla may have specific recommendations for Browser Use / Playwright deployments.

## Success Indicators

You'll know it's working when you see:

```
✅ Extensions ready: 3 extensions loaded
✅ Spawning Chrome subprocess listening on CDP
✅ Browser launch test successful
✅ Browser test completed successfully
```

Instead of:

```
❌ Launching new local browser playwright:chromium failed!
FileNotFoundError [Errno 2] No such file or directory
```