# from rest_framework.authentication import TokenAuthentication


# class CreateOrder(APIView):
#    def post(self, request):
#       # Extract data from request
#       collect = request.data
#       customer_id = self.request.query_params.get("buyer")

#       # Verify Customer Exists
#       customer = self.get_customer_or_raise(customer_id)
#       if customer is None:
#          return Response({"error": "Customer does not exist"}, status=status.HTTP_400_BAD_REQUEST)

#       # Collect Products
#       products = collect["products"]
#       total_price = Decimal('0.00')

#       # Get the affiliate based on the referral code
#       store_id = collect.get("store")
#       store = self.get_store(store_id)

#       # Create Order
#       order = self.create_order(customer_id, collect, store, total_price)

#       # Create Order Items
#       self.create_order_items(order, products, store)
#       order.save()

#       return Response({"message": "Order created successfully"}, status=status.HTTP_201_CREATED)

#    def get_store(self, store_id):
#       return get_object_or_404(Store, id=store_id)

#    def get_customer_or_raise(self, customer_id):
#       try:
#          return CustomUser.objects.get(id=customer_id)
#       except CustomUser.DoesNotExist:
#          logging.exception("An Unexpected Error Occurred")
#          return None

#    def create_order(self, customer_id, collect, store, total_price):
#       order_data = {
#          'buyer': customer_id,
#          'status': "Pending",
#          'shipping_address': collect["shipping_address"],
#          'store': store.id,
#          'total_price': total_price
#       }

#       order_serializer = OrderSerializer(data=order_data)

#       if order_serializer.is_valid():
#          order = order_serializer.save()
#          return order
#       else:
#          logging.error("Order not valid")
#          print(order_serializer.errors)
#          raise serializers.ValidationError("Invalid order data")


#    def create_order_items(self, order, products, store):
#       total_price = Decimal('0.00')
#       for product_data in products:
#          product = self.get_product(product_data["product"])
#          wholesale_price = self.get_wholesale_price(product_data["product"], product_data["variant"])
#          retail_price = self.get_retail_price(store, product_data["variant"])

#          price = None  # Initialize price outside the if block

#          if retail_price:
#                price = wholesale_price + retail_price

#          if price is not None:
#             item_total_price = Decimal(price) * Decimal(product_data["quantity"])
#             total_price += item_total_price

#             OrderItems.objects.create(
#                order=order,
#                product=product,
#                quantity=product_data["quantity"],
#             )
#             # Increment the sales count of the associated product
#             product.sales_count += product_data['quantity']
#             product.save()
#          else:
#             # Handle the case where the price is not available for the product
#             logging.error("Price not available for product with id: {}".format(product.id))

#       # Set the total_price attribute of the order before saving
#       order.total_price = total_price
#       order.save()

#       return total_price

#    def get_product(self, product_sn):
#       return get_object_or_404(Product, id=product_sn)


#    def get_wholesale_price(self, product_id, variant_id):
#       try:
#          variant = ProductVariant.objects.get(product=product_id, id=variant_id)
#          logging.info(variant.wholesale_price)
#          return variant.wholesale_price
#       except ProductVariant.DoesNotExist:
#          logging.error("No Product Variant")
#          return None


#    def get_retail_price(self, store, variant_id):
#       try:
#          store_variant = StoreProductPricing.objects.get(store=store, product_variant=variant_id)
#          return store_variant.retail_price
#       except StoreProductPricing.DoesNotExist:
#          logging.error("No Store Variant")
#       return None


# class OrderViewSet(ModelViewSet):
#    queryset = Order.objects.all().select_related('buyer', 'store')
#    serializer_class = OrderSerializer

#    def get_queryset(self):
#       store = self.request.query_params.get("store")
#       if store:
#          return Order.objects.filter(store=store).select_related('buyer', 'store')
#       return Order.objects.all().select_related('buyer', 'store')


# class CheckoutView(APIView):
#    def post(self, request, *args, **kwargs):
#       serializer = CheckoutSerializer(data=request.data)
#       serializer.is_valid(raise_exception=True)

#       cart = serializer.validated_data['cart_id']

#       # Create an order
#       # You might need to calculate the total amount
#       order = Order.objects.create(user=cart.user, total_amount=0)

#       # Create order items from cart items
#       for cart_item in cart.items.all():
#          OrderItem.objects.create(order=order, product=cart_item.product,
#                                     quantity=cart_item.quantity, price=cart_item.product.price)

#       # Update total_amount in the order (you need to calculate it based on order items)
#       order.total_amount = order.items.aggregate(total_amount=models.Sum(
#          models.F('quantity') * models.F('price')))['total_amount']
#       order.save()

#       # Clear the cart after checkout
#       cart.items.all().delete()
#       cart.save()

#       order_serializer = OrderSerializer(order)
#       return Response({"message": "Checkout successful", "order": order_serializer.data}, status=status.HTTP_200_OK)
