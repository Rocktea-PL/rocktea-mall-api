from celery import shared_task
from .models import StoreOrder
from .shipbubble_service import ShipbubbleService
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_shipment_status():
    """Check and update shipment status for orders with tracking IDs"""
    shipbubble_service = ShipbubbleService()
    
    # Get orders with tracking IDs that are not delivered
    orders = StoreOrder.objects.filter(
        tracking_id__isnull=False,
        tracking_status__in=['pending', 'cancelled']
    ).exclude(tracking_id='')
    
    updated_count = 0
    
    for order in orders:
        try:
            # Get tracking status from Shipbubble
            response = shipbubble_service.track_shipping_status(order.tracking_id)
            
            if response.get('status') == 'success':
                data = response.get('data', {})
                new_status = data.get('status', '').lower()
                
                # Map Shipbubble status to our order status
                status_mapping = {
                    'pending': 'Pending',
                    'in_transit': 'Enroute',
                    'delivered': 'Delivered',
                    'cancelled': 'Returned'
                }
                
                mapped_status = status_mapping.get(new_status)
                
                if mapped_status and order.status != mapped_status:
                    order.tracking_status = new_status
                    order.save(update_fields=['tracking_status', 'tracking_status'])
                    updated_count += 1
                    logger.info(f"Updated order {order.id} status to {mapped_status}")
                    
        except Exception as e:
            logger.error(f"Error updating order {order.id}: {e}")
    
    logger.info(f"Updated {updated_count} orders")
    return f"Updated {updated_count} orders"