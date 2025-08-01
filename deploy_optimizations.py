#!/usr/bin/env python
"""
Deployment script to apply all optimizations
"""
import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Deploying RockTea Mall Optimizations...")
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Please run this script from the Django project root directory")
        sys.exit(1)
    
    # Install requirements
    if not run_command("pip install -r requirements_optimized.txt", "Installing optimized requirements"):
        print("⚠️  Continuing with existing packages...")
    
    # Run migrations
    run_command("python manage.py makemigrations", "Creating migrations")
    run_command("python manage.py migrate", "Applying migrations")
    
    # Collect static files
    run_command("python manage.py collectstatic --noinput", "Collecting static files")
    
    # Clear cache
    run_command("python manage.py shell -c \"from django.core.cache import cache; cache.clear()\"", "Clearing cache")
    
    print("\n🎯 Optimization Deployment Complete!")
    print("\n📊 Performance Improvements Applied:")
    print("   ✅ Database connection pooling")
    print("   ✅ Redis caching with compression")
    print("   ✅ File upload validation (5MB limit)")
    print("   ✅ Optimized pagination")
    print("   ✅ Query optimization")
    print("   ✅ Cloudinary image optimization")
    print("   ✅ Performance monitoring")
    print("   ✅ Session optimization")
    print("\n🔧 Next Steps:")
    print("   1. Restart your Redis server")
    print("   2. Restart Celery workers: celery -A setup worker -l info")
    print("   3. Start Celery beat: celery -A setup beat -l info")
    print("   4. Monitor performance with new middleware")

if __name__ == "__main__":
    main()