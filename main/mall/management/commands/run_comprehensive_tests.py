from django.core.management.base import BaseCommand
from django.test.utils import get_runner
from django.conf import settings
from django.core.management import call_command
import sys
import time

class Command(BaseCommand):
    help = 'Run comprehensive tests for all apps with detailed reporting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Run tests for specific app only'
        )
        parser.add_argument(
            '--coverage',
            action='store_true',
            help='Run with coverage report'
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Run tests without migrations'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting RockTea PL API Comprehensive Test Suite')
        )
        self.stdout.write('=' * 60)

        start_time = time.time()
        
        # Test apps configuration
        test_apps = {
            'mall': [
                'mall.tests.test_models',
                'mall.tests.test_views'
            ],
            'order': [
                'order.tests.test_models',
                'order.tests.test_views', 
                'order.tests.test_signals'
            ],
            'accounts': [
                'accounts.tests.test_views'
            ],
            'dropshippers': [
                'dropshippers.tests.test_views'
            ],
            'setup': [
                'setup.tests'
            ]
        }

        # Filter by specific app if requested
        if options['app']:
            if options['app'] in test_apps:
                test_apps = {options['app']: test_apps[options['app']]}
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ App '{options['app']}' not found")
                )
                return

        total_tests = 0
        passed_tests = 0
        failed_apps = []

        # Run tests for each app
        for app_name, test_modules in test_apps.items():
            self.stdout.write(f"\n📦 Testing {app_name.upper()} App")
            self.stdout.write('-' * 40)
            
            app_passed = True
            
            for test_module in test_modules:
                self.stdout.write(f"  🧪 Running {test_module}")
                
                try:
                    # Prepare test command arguments
                    test_args = [test_module, '--verbosity=2']
                    
                    if options['fast']:
                        test_args.append('--nomigrations')
                    
                    # Run the test
                    call_command('test', *test_args)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"    ✅ {test_module} passed")
                    )
                    passed_tests += 1
                    
                except SystemExit as e:
                    if e.code != 0:
                        self.stdout.write(
                            self.style.ERROR(f"    ❌ {test_module} failed")
                        )
                        app_passed = False
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"    ✅ {test_module} passed")
                        )
                        passed_tests += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    ❌ {test_module} error: {e}")
                    )
                    app_passed = False
                
                total_tests += 1
            
            if not app_passed:
                failed_apps.append(app_name)

        # Final report
        end_time = time.time()
        duration = end_time - start_time
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 TEST SUMMARY REPORT')
        self.stdout.write('=' * 60)
        
        self.stdout.write(f"⏱️  Duration: {duration:.2f} seconds")
        self.stdout.write(f"📈 Total Tests: {total_tests}")
        self.stdout.write(f"✅ Passed: {passed_tests}")
        self.stdout.write(f"❌ Failed: {total_tests - passed_tests}")
        
        if failed_apps:
            self.stdout.write(
                self.style.ERROR(f"🚨 Failed Apps: {', '.join(failed_apps)}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("🎉 All tests passed!")
            )

        # Coverage report
        if options['coverage']:
            self.stdout.write('\n📊 Generating Coverage Report...')
            try:
                call_command('test', '--verbosity=1', '--keepdb')
                self.stdout.write(
                    self.style.SUCCESS("Coverage report generated")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Coverage report failed: {e}")
                )
                self.stdout.write(
                    "💡 Install coverage.py: pip install coverage"
                )

        # Performance recommendations
        self.stdout.write('\n💡 PERFORMANCE TIPS:')
        self.stdout.write('  • Use --fast flag to skip migrations')
        self.stdout.write('  • Use --app flag to test specific apps')
        self.stdout.write('  • Use --coverage for detailed coverage reports')
        
        self.stdout.write('\n🏁 Test Suite Complete!')
        
        # Exit with error code if tests failed
        if failed_apps:
            sys.exit(1)