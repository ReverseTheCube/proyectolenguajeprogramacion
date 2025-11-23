from django.db import models

# Modelo 1: Mantenimiento de las Categorías
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

# Modelo 2: Mantenimiento de Clientes
class Cliente(models.Model):
    dni = models.CharField(max_length=15, primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    distrito = models.CharField(max_length=100, blank=True, null=True)
    correo = models.EmailField(unique=True)
    celular = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.dni})"

# Modelo 3: Mantenimiento de Productos
class Producto(models.Model):
    numero_serie = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    # Relación: Un producto pertenece a UNA categoría.
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    dimensiones = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.numero_serie})"

# Modelo 4: Personal de Delivery
# (Implícito en los formularios de pedido y consulta) [cite_start][cite: 124, 159-166]
class PersonalDelivery(models.Model):
    dni = models.CharField(max_length=15, primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    celular = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.dni})"

# Modelo 5: Cabecera del Pedido
class Pedido(models.Model):
    # Usamos AutoField para que Django cree un ID numérico autoincremental
    numero_pedido = models.AutoField(primary_key=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
    ]
    estado_pedido = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='Pendiente')
    
    # Relaciones:
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    personal_delivery = models.ForeignKey(PersonalDelivery, on_delete=models.SET_NULL, blank=True, null=True)
    
    def __str__(self):
        return f"Pedido N° {self.numero_pedido} - {self.cliente.nombres}"

# Modelo 6: Detalle del Pedido
# (Para los "varios productos" de un pedido) [cite_start][cite: 130]
class DetallePedido(models.Model):
    # Relaciones:
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) # Guarda el precio al momento de la venta

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} @ S/ {self.precio_unitario}"