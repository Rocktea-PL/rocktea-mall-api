# mall/management/commands/seed_categories.py
from django.core.management.base import BaseCommand
from mall.models import Category

class Command(BaseCommand):
    # help = 'Seeds initial categories'

    # def handle(self, *args, **options):
    #     category_choices = Category.CHOICES
    #     self.stdout.write(self.style.NOTICE('Starting Category population...'))
        
    #     created_count = 0
    #     for name, display_name in category_choices:
    #         category, created = Category.objects.get_or_create(name=name)
    #         if created:
    #             self.stdout.write(self.style.SUCCESS(f'Created category: "{category.name}"'))
    #             created_count += 1
    #         else:
    #             self.stdout.write(self.style.WARNING(f'Category "{category.name}" already exists. Skipped.'))
        
    #     self.stdout.write(self.style.SUCCESS(
    #         f'Successfully seeded {created_count} new categories'
    #     ))

    help = 'Populates the Category model with predefined choices if they do not exist.'

    def handle(self, *args, **options):
        # Extract just the 'name' values from CHOICES
        category_names_to_create = [name for name, display_name in Category.CHOICES]
        
        self.stdout.write(self.style.NOTICE('Starting Category population...'))

        # Get existing category names to avoid trying to create them
        existing_category_names = set(Category.objects.filter(name__in=category_names_to_create).values_list('name', flat=True))

        # Prepare Category objects for bulk creation, only for those that don't exist
        categories_to_bulk_create = []
        for name in category_names_to_create:
            if name not in existing_category_names:
                categories_to_bulk_create.append(Category(name=name))
            else:
                self.stdout.write(self.style.WARNING(f'Category "{name}" already exists. Skipped.'))
        
        if categories_to_bulk_create:
            # Use bulk_create with ignore_conflicts=True for safety and efficiency
            # Note: ignore_conflicts requires Django 2.2+ and a database that supports it (most do).
            # It will silently skip objects whose unique fields conflict with existing ones.
            # It does not return the 'created' status for individual objects.
            Category.objects.bulk_create(categories_to_bulk_create, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created {len(categories_to_bulk_create)} new categories.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('No new categories to create.'))
        
        self.stdout.write(self.style.SUCCESS('Category population complete.'))