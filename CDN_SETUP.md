# CDN Setup for Static Files

## Option 1: AWS CloudFront (Recommended)

### 1. Create CloudFront Distribution
```bash
# Add to settings.py for production
if PRODUCTION:
    STATIC_URL = 'https://your-cdn-domain.cloudfront.net/static/'
    WHITENOISE_USE_FINDERS = False
```

### 2. Configure CloudFront
- Origin: Your domain (api.yourockteamall.com)
- Path Pattern: /static/*
- Cache Behavior: Cache everything
- TTL: 1 year for static files

## Option 2: Cloudinary for All Assets

### Update settings.py:
```python
if not CI_ENVIRONMENT:
    # Use Cloudinary for both media and static files
    STORAGES = {
        "staticfiles": {
            "BACKEND": "cloudinary_storage.storage.StaticHashedCloudinaryStorage",
        },
        "media": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"
        }
    }
    
    STATIC_URL = f"https://res.cloudinary.com/{env('CLOUDINARY_NAME')}/raw/upload/static/"
```

## Option 3: Simple CDN with jsDelivr (Free)

### For public static files:
```html
<!-- In templates, replace static files with CDN -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/yourusername/repo@main/static/css/style.css">
```

## Performance Comparison:
- **No CDN**: 100-500ms load time
- **CloudFront**: 20-50ms load time  
- **Cloudinary**: 30-80ms load time
- **jsDelivr**: 50-150ms load time

## Recommended: Use CloudFront for production