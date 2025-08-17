from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from order.models import StoreOrder
from datetime import datetime


class Command(BaseCommand):
    help = 'Test order completion email template'

    def add_arguments(self, parser):
        parser.add_argument('--order-id', type=str, help='Order ID to test email for')
        parser.add_argument('--preview', action='store_true', help='Preview email HTML')

    def handle(self, *args, **options):
        order_id = options.get('order_id')
        preview = options.get('preview', False)

        if order_id:
            try:
                order = StoreOrder.objects.get(id=order_id)
                self.stdout.write(f"Testing email for order: {order.order_sn}")
                
                # Get order items with proper pricing
                order_items = []
                subtotal = 0
                
                for item in order.items.all():
                    try:
                        from mall.models import StoreProductPricing
                        store_pricing = StoreProductPricing.objects.get(
                            product=item.product, 
                            store=order.store
                        )
                        item_price = float(store_pricing.retail_price) * item.quantity
                        subtotal += item_price
                        
                        order_items.append({
                            'product_name': item.product.name,
                            'variant_name': item.product_variant.name if item.product_variant else None,
                            'quantity': item.quantity,
                            'price': f"{item_price:.2f}"
                        })
                    except StoreProductPricing.DoesNotExist:
                        item_price = float(item.product_variant.wholesale_price) * item.quantity if item.product_variant else 0
                        subtotal += item_price
                        
                        order_items.append({
                            'product_name': item.product.name,
                            'variant_name': item.product_variant.name if item.product_variant else None,
                            'quantity': item.quantity,
                            'price': f"{item_price:.2f}"
                        })
                
                # Get delivery fee
                delivery_fee = 0
                if order.state:
                    delivery_fee = float(order.state.delivery_fee)
                elif order.shipping_fee:
                    delivery_fee = float(order.shipping_fee)
                
                context = {
                    'customer_name': f"{order.buyer.first_name} {order.buyer.last_name}".strip() or order.buyer.email,
                    'store_name': order.store.name,
                    'order_number': order.order_sn,
                    'order_date': order.created_at.strftime('%B %d, %Y') if order.created_at else datetime.now().strftime('%B %d, %Y'),
                    'order_status': order.status,
                    'subtotal': f"{subtotal:.2f}",
                    'delivery_fee': f"{delivery_fee:.2f}",
                    'total_amount': f"{float(order.total_price):.2f}" if order.total_price else "0.00",
                    'delivery_location': order.delivery_location,
                    'delivery_code': order.delivery_code,
                    'tracking_url': order.tracking_url,
                    'order_items': order_items,
                    'current_year': datetime.now().year
                }
                
            except StoreOrder.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Order {order_id} not found'))
                return
        else:
            # Use sample data
            context = {
                'customer_name': 'John Doe',
                'store_name': 'Sample Store',
                'order_number': 'ORD123',
                'order_date': datetime.now().strftime('%B %d, %Y'),
                'order_status': 'Completed',
                'subtotal': '23500.00',
                'delivery_fee': '1500.00',
                'total_amount': '25000.00',
                'delivery_location': '123 Sample Street, Lagos, Nigeria',
                'delivery_code': 'ABC123',
                'tracking_url': 'https://example.com/track/123',
                'order_items': [
                    {
                        'product_name': 'Sample Product 1',
                        'variant_name': 'Red - Large',
                        'quantity': 2,
                        'price': '15000.00'
                    },
                    {
                        'product_name': 'Sample Product 2',
                        'variant_name': 'Blue - Medium',
                        'quantity': 1,
                        'price': '8500.00'
                    }
                ],
                'current_year': datetime.now().year
            }

        try:
            html_content = render_to_string('emails/order_completion.html', context)
            
            if preview:
                # Save to file for preview
                with open('order_email_preview.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.stdout.write(self.style.SUCCESS('Email preview saved to order_email_preview.html'))
            else:
                self.stdout.write(self.style.SUCCESS('Email template rendered successfully'))
                self.stdout.write(f"Subject: Order Confirmed - #{context['order_number']} from {context['store_name']}")
                self.stdout.write(f"Recipient: {context['customer_name']}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error rendering template: {e}'))