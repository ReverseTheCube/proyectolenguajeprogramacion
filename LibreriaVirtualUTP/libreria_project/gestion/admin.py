from django.contrib import admin
# Importamos todos los modelos que creamos en models.py
from .models import Categoria, Cliente, Producto, PersonalDelivery, Pedido, DetallePedido

# Le decimos a Django que registre estos modelos en el panel de admin

# Mantenimiento de Categorías 
admin.site.register(Categoria)

# Mantenimiento de Clientes 
admin.site.register(Cliente)

# Mantenimiento de Productos 
admin.site.register(Producto)

# Mantenimiento de Personal (Implícito)
admin.site.register(PersonalDelivery)

# Formularios de Pedidos
admin.site.register(Pedido)
admin.site.register(DetallePedido)