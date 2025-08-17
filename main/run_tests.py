#!/usr/bin/env python
"""
Quick test runner for Rocktea Mall API
Usage: python run_tests.py [app_name]
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

def main():
    """Run tests with optional app filter"""
    
    # Default test command
    test_command = ['manage.py', 'run_comprehensive_tests']
    
    # Add app filter if provided
    if len(sys.argv) > 1:
        app_name = sys.argv[1]
        test_command.extend(['--app', app_name])
    
    # Add additional flags
    if '--coverage' in sys.argv:
        test_command.append('--coverage')
    
    if '--fast' in sys.argv:
        test_command.append('--fast')
    
    # Execute the test command
    execute_from_command_line(test_command)

if __name__ == '__main__':
    main()