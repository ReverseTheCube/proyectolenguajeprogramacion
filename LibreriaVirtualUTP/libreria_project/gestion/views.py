from django.shortcuts import render, redirect
from django.db import transaction  # Importante para transacciones
from django.contrib import messages # Para enviar mensajes de éxito/error
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required # Para proteger vistas
from .models import Cliente, Producto, PersonalDelivery, Pedido, DetallePedido, Categoria
from django.db.models import Q
from decimal import Decimal

# Esta es la función que definimos en urls.py
@login_required # Proteger esta vista
def home_view(request):
    """
    Vista para la página principal.
    Por ahora solo muestra el "esqueleto" (base.html).
    """
    # El formulario principal es el punto de acceso
    return render(request, 'gestion/home.html')

def login_view(request):
    """
    Controla el Formulario de Autenticación.
    """
    # Si el usuario ya está logueado, lo redirigimos al home
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        # 1. Obtener datos del formulario 
        usuario = request.POST.get('usuario')
        contrasena = request.POST.get('contrasena')
        
        # 2. Autenticar al usuario
        # 'authenticate' verifica si el usuario y contraseña son correctos
        # (Usa el "superuser" que creamos con 'manage.py createsuperuser')
        user = authenticate(request, username=usuario, password=contrasena)
        
        if user is not None:
            # 3. Si es correcto, iniciar sesión
            login(request, user)
            # Redirigir a la página principal
            return redirect('home')
        else:
            # 4. Si no es correcto, enviar error
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'gestion/login.html')
            
    # Si el método es GET (el usuario solo carga la página)
    return render(request, 'gestion/login.html')

def logout_view(request):
    """
    Cierra la sesión del usuario.
    """
    logout(request)
    # Redirigir a la página de login
    return redirect('login')

@login_required
def registrar_pedido_view(request):
    
    # Si el método es POST, significa que el usuario ENVIÓ el formulario
    if request.method == 'POST':
        try:
            # 1. Obtener datos de la cabecera 
            cliente_dni = request.POST.get('cliente_dni')
            personal_dni = request.POST.get('personal_dni')
            fecha_entrega = request.POST.get('fecha_entrega')
            observaciones = request.POST.get('observaciones', '')
            
            # 2. Obtener los productos 
            # (Esto es complejo, asumiremos que el frontend nos envía listas)
            series_productos = request.POST.getlist('producto_serie[]')
            cantidades = request.POST.getlist('cantidad[]')
            
            if not series_productos:
                messages.error(request, "No se añadieron productos al pedido.")
                return redirect('registrar_pedido')

            # --- INICIO DE LA TRANSACCIÓN ---
            # 'atomic' asegura que si algo falla, se revierte todo.
            with transaction.atomic():
                
                # 3. Buscar los objetos de Cliente y Personal
                cliente = Cliente.objects.get(dni=cliente_dni)
                personal = PersonalDelivery.objects.get(dni=personal_dni)
                
                # 4. Crear la cabecera del Pedido
                pedido = Pedido.objects.create(
                    cliente=cliente,
                    personal_delivery=personal,
                    fecha_entrega=fecha_entrega,
                    observaciones=observaciones,
                    estado_pedido='Pendiente'
                )
                
                subtotal_total = 0

                # 5. Iterar sobre los productos para crear detalles y restar stock
                for serie, cant_str in zip(series_productos, cantidades):
                    cantidad = int(cant_str)
                    producto = Producto.objects.get(numero_serie=serie)
                    
                    # 5a. Validar Stock
                    if producto.stock < cantidad:
                        # Esto causa un error y revierte la transacción
                        raise Exception(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")
                    
                    # 5b. Crear el detalle
                    precio_venta = producto.precio
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_venta
                    )
                    
                    # 5c. Actualizar Stock
                    producto.stock -= cantidad
                    producto.save()
                    
                    subtotal_total += (precio_venta * cantidad)
                
                # 6. Calcular Totales (Aquí puedes guardar el total en el pedido si quieres)
                igv = subtotal_total * Decimal('0.18') 
                total = subtotal_total + igv 

            # --- FIN DE LA TRANSACCIÓN ---
            
            messages.success(request, f"¡Pedido N° {pedido.numero_pedido} registrado exitosamente! Total: S/ {total:.2f}")
            return redirect('registrar_pedido') # Redirigir a la misma página

        except Exception as e:
            # Si algo falló (Stock, DNI no existe, etc.), mostrar error
            messages.error(request, f"Error al registrar el pedido: {e}")
            return redirect('registrar_pedido')

    # Si el método es GET, significa que el usuario ACABA DE ABRIR la página
    else:
        # 1. Obtenemos los datos para llenar los <select> del formulario
        clientes = Cliente.objects.all()
        productos = Producto.objects.filter(stock__gt=0) # Solo productos con stock
        personal = PersonalDelivery.objects.all()
        
        # 2. Creamos el "contexto" para enviar al HTML
        context = {
            'clientes': clientes,
            'productos': productos,
            'personal_delivery': personal,
        }
        # 3. Renderizamos la plantilla HTML
        return render(request, 'gestion/registrar_pedido.html', context)
    
    
@login_required
def cliente_list_view(request):
    """
    Controla el Mantenimiento de Clientes.
    Muestra la lista (Read) y maneja el registro (Create).
    """
    # Lógica de REGISTRAR (Create)
    if request.method == 'POST':
        try:
            Cliente.objects.create(
                dni=request.POST.get('dni'),
                nombres=request.POST.get('nombres'),
                apellidos=request.POST.get('apellidos'),
                direccion=request.POST.get('direccion'),
                distrito=request.POST.get('distrito'),
                correo=request.POST.get('correo'),
                celular=request.POST.get('celular'),
            )
            messages.success(request, "Cliente registrado exitosamente.")
        except Exception as e:
            # Manejar error de DNI/correo duplicado
            if 'UNIQUE constraint' in str(e) or 'Duplicate entry' in str(e):
                messages.error(request, "Error: El DNI o Correo ya existe.")
            else:
                messages.error(request, f"Error al registrar cliente: {e}")
        
        return redirect('cliente_list')

    # Lógica de LISTAR (Read)
    # Si es GET, solo muestra la página
    clientes = Cliente.objects.all() # Obtiene todos los clientes
    context = {
        'clientes': clientes
    }
    return render(request, 'gestion/clientes.html', context)

@login_required
def cliente_update_view(request, dni):
    """
    Controla la MODIFICACIÓN de un cliente (Update).
    """
    try:
        cliente = Cliente.objects.get(dni=dni)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado.")
        return redirect('cliente_list')

    if request.method == 'POST':
        try:
            # Actualiza los campos del cliente
            cliente.nombres = request.POST.get('nombres')
            cliente.apellidos = request.POST.get('apellidos')
            cliente.direccion = request.POST.get('direccion')
            cliente.distrito = request.POST.get('distrito')
            cliente.correo = request.POST.get('correo')
            cliente.celular = request.POST.get('celular')
            cliente.save() # Guarda los cambios
            
            messages.success(request, "Cliente modificado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al modificar cliente: {e}")
            
        return redirect('cliente_list')
    
    # Si es GET, muestra el formulario con los datos del cliente
    context = {
        'cliente': cliente
    }
    return render(request, 'gestion/cliente_update.html', context)

@login_required
def cliente_delete_view(request, dni):
    """
    Controla la ELIMINACIÓN de un cliente (Delete).
    """
    # Usamos POST para eliminar por seguridad
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(dni=dni)
            cliente.delete()
            messages.success(request, "Cliente eliminado exitosamente.")
        except Cliente.DoesNotExist:
            messages.error(request, "Cliente no encontrado.")
        except Exception as e:
            # Maneja error de clave foránea (cliente con pedidos)
            if 'FOREIGN KEY constraint' in str(e):
                messages.error(request, "Error: No se puede eliminar. El cliente tiene pedidos asociados.")
            else:
                messages.error(request, f"Error al eliminar cliente: {e}")
                
    return redirect('cliente_list')

@login_required
def producto_list_view(request):
    """
    Controla el Mantenimiento de Productos.
    Muestra la lista (Read) y maneja el registro (Create).
    [cite: 204-207]
    """
    # Lógica de REGISTRAR (Create)
    if request.method == 'POST':
        try:
            # 1. Buscar la instancia de Categoría
            categoria_id = request.POST.get('categoria')
            categoria_obj = Categoria.objects.get(id=categoria_id)
            
            # 2. Crear el Producto
            Producto.objects.create(
                numero_serie=request.POST.get('numero_serie'),
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion'),
                precio=request.POST.get('precio'),
                stock=request.POST.get('stock'),
                categoria=categoria_obj, # Asignar el objeto Categoría
                color=request.POST.get('color'),
                dimensiones=request.POST.get('dimensiones'),
            )
            messages.success(request, "Producto registrado exitosamente.")
        except Exception as e:
            if 'UNIQUE constraint' in str(e) or 'Duplicate entry' in str(e):
                messages.error(request, "Error: El Número de Serie ya existe.")
            else:
                messages.error(request, f"Error al registrar producto: {e}")
        
        return redirect('producto_list')

    # Lógica de LISTAR (Read)
    # Si es GET, solo muestra la página
    productos = Producto.objects.all().select_related('categoria') # Optimización: trae la categoría en la misma consulta
    categorias = Categoria.objects.all() # Para el formulario
    
    context = {
        'productos': productos,
        'categorias': categorias # Enviamos las categorías al <select>
    }
    return render(request, 'gestion/productos.html', context)


@login_required
def producto_update_view(request, serie):
    """
    Controla la MODIFICACIÓN de un producto (Update).
    """
    try:
        # Usamos 'serie' (que es la 'numero_serie') para buscar
        producto = Producto.objects.get(numero_serie=serie)
    except Producto.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect('producto_list')

    if request.method == 'POST':
        try:
            # 1. Buscar la nueva categoría
            categoria_id = request.POST.get('categoria')
            categoria_obj = Categoria.objects.get(id=categoria_id)
            
            # 2. Actualizar los campos
            producto.nombre = request.POST.get('nombre')
            producto.descripcion = request.POST.get('descripcion')
            producto.precio = request.POST.get('precio')
            producto.stock = request.POST.get('stock')
            producto.categoria = categoria_obj # Asignar la nueva categoría
            producto.color = request.POST.get('color')
            producto.dimensiones = request.POST.get('dimensiones')
            producto.save() # Guarda los cambios
            
            messages.success(request, "Producto modificado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al modificar producto: {e}")
            
        return redirect('producto_list')
    
    # Si es GET, muestra el formulario con los datos del producto
    context = {
        'producto': producto,
        'categorias': Categoria.objects.all() # Para el <select>
    }
    return render(request, 'gestion/producto_update.html', context)

@login_required
def producto_delete_view(request, serie):
    """
    Controla la ELIMINACIÓN de un producto (Delete).
    """
    if request.method == 'POST':
        try:
            producto = Producto.objects.get(numero_serie=serie)
            producto.delete()
            messages.success(request, "Producto eliminado exitosamente.")
        except Producto.DoesNotExist:
            messages.error(request, "Producto no encontrado.")
        except Exception as e:
            if 'FOREIGN KEY constraint' in str(e):
                messages.error(request, "Error: No se puede eliminar. El producto está asociado a pedidos.")
            else:
                messages.error(request, f"Error al eliminar producto: {e}")
                
    return redirect('producto_list')

@login_required
def categoria_list_view(request):
    """
    Controla el Mantenimiento de Categorías.
    Muestra la lista (Read) y maneja el registro (Create).
    """
    # Lógica de REGISTRAR (Create)
    if request.method == 'POST':
        try:
            Categoria.objects.create(
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion'),
            )
            messages.success(request, "Categoría registrada exitosamente.")
        except Exception as e:
            if 'UNIQUE constraint' in str(e) or 'Duplicate entry' in str(e):
                messages.error(request, "Error: El nombre de la categoría ya existe.")
            else:
                messages.error(request, f"Error al registrar categoría: {e}")
        
        return redirect('categoria_list')

    # Lógica de LISTAR (Read)
    categorias = Categoria.objects.all()
    context = {
        'categorias': categorias
    }
    return render(request, 'gestion/categorias.html', context)

@login_required
def categoria_update_view(request, id):
    """
    Controla la MODIFICACIÓN de una categoría (Update).
    """
    try:
        categoria = Categoria.objects.get(id=id)
    except Categoria.DoesNotExist:
        messages.error(request, "Categoría no encontrada.")
        return redirect('categoria_list')

    if request.method == 'POST':
        try:
            categoria.nombre = request.POST.get('nombre')
            categoria.descripcion = request.POST.get('descripcion')
            categoria.save()
            
            messages.success(request, "Categoría modificada exitosamente.")
        except Exception as e:
            if 'UNIQUE constraint' in str(e) or 'Duplicate entry' in str(e):
                messages.error(request, "Error: El nombre de la categoría ya existe.")
            else:
                messages.error(request, f"Error al modificar categoría: {e}")
            
        return redirect('categoria_list')
    
    # Si es GET, muestra el formulario con los datos
    context = {
        'categoria': categoria
    }
    return render(request, 'gestion/categoria_update.html', context)

@login_required
def categoria_delete_view(request, id):
    """
    Controla la ELIMINACIÓN de una categoría (Delete).
    """
    if request.method == 'POST':
        try:
            categoria = Categoria.objects.get(id=id)
            categoria.delete()
            messages.success(request, "Categoría eliminada exitosamente.")
        except Categoria.DoesNotExist:
            messages.error(request, "Categoría no encontrada.")
        except Exception as e:
            if 'FOREIGN KEY constraint' in str(e):
                messages.error(request, "Error: No se puede eliminar. La categoría está siendo usada por productos.")
            else:
                messages.error(request, f"Error al eliminar categoría: {e}")
                
    return redirect('categoria_list')

@login_required
def personal_list_view(request):
    """
    Controla el Mantenimiento de Personal Delivery.
    Muestra la lista (Read) y maneja el registro (Create).
    """
    # Lógica de REGISTRAR (Create)
    if request.method == 'POST':
        try:
            PersonalDelivery.objects.create(
                dni=request.POST.get('dni'),
                nombres=request.POST.get('nombres'),
                apellidos=request.POST.get('apellidos'),
                celular=request.POST.get('celular'),
            )
            messages.success(request, "Personal de delivery registrado exitosamente.")
        except Exception as e:
            if 'UNIQUE constraint' in str(e) or 'Duplicate entry' in str(e):
                messages.error(request, "Error: El DNI ya existe.")
            else:
                messages.error(request, f"Error al registrar personal: {e}")
        
        return redirect('personal_list')

    # Lógica de LISTAR (Read)
    personal = PersonalDelivery.objects.all()
    context = {
        'personal': personal
    }
    return render(request, 'gestion/personal.html', context)

@login_required
def personal_update_view(request, dni):
    """
    Controla la MODIFICACIÓN de un personal (Update).
    """
    try:
        personal = PersonalDelivery.objects.get(dni=dni)
    except PersonalDelivery.DoesNotExist:
        messages.error(request, "Personal no encontrado.")
        return redirect('personal_list')

    if request.method == 'POST':
        try:
            personal.nombres = request.POST.get('nombres')
            personal.apellidos = request.POST.get('apellidos')
            personal.celular = request.POST.get('celular')
            personal.save()
            
            messages.success(request, "Personal modificado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al modificar personal: {e}")
            
        return redirect('personal_list')
    
    # Si es GET, muestra el formulario con los datos
    context = {
        'personal': personal
    }
    return render(request, 'gestion/personal_update.html', context)

@login_required
def personal_delete_view(request, dni):
    """
    Controla la ELIMINACIÓN de un personal (Delete).
    """
    if request.method == 'POST':
        try:
            personal = PersonalDelivery.objects.get(dni=dni)
            personal.delete()
            messages.success(request, "Personal eliminado exitosamente.")
        except PersonalDelivery.DoesNotExist:
            messages.error(request, "Personal no encontrado.")
        except Exception as e:
            if 'FOREIGN KEY constraint' in str(e):
                messages.error(request, "Error: No se puede eliminar. El personal está asociado a pedidos.")
            else:
                messages.error(request, f"Error al eliminar personal: {e}")
                
    return redirect('personal_list')

@login_required
def registrar_entrega_view(request):
    """
    Controla el Formulario para Registrar Entrega de Pedido.
    Maneja la búsqueda de pedidos pendientes y el registro de la entrega.
    
    """
    context = {}
    
    # --- Lógica de BÚSQUEDA (GET) ---
    # Si el usuario usó el formulario de búsqueda
    if 'buscar' in request.GET:
        tipo_busqueda = request.GET.get('tipo_busqueda')
        valor = request.GET.get('valor_busqueda')
        pedidos_pendientes = []

        if not valor:
            messages.error(request, "Debe ingresar un valor para la búsqueda.")
        else:
            try:
                if tipo_busqueda == 'dni_cliente':
                    # [cite: 137]
                    pedidos_pendientes = Pedido.objects.filter(
                        cliente__dni=valor, 
                        estado_pedido='Pendiente'
                    ).select_related('cliente', 'personal_delivery')
                elif tipo_busqueda == 'dni_personal':
                    # [cite: 141]
                    pedidos_pendientes = Pedido.objects.filter(
                        personal_delivery__dni=valor, 
                        estado_pedido='Pendiente'
                    ).select_related('cliente', 'personal_delivery')
                
                if not pedidos_pendientes:
                    messages.info(request, "No se encontraron pedidos pendientes para ese criterio.")
                
                context['pedidos'] = pedidos_pendientes
            except Exception as e:
                messages.error(request, f"Error en la búsqueda: {e}")
        
        context['valor_buscado'] = valor
        context['tipo_buscado'] = tipo_busqueda
        
    # --- Lógica de REGISTRO DE ENTREGA (POST) ---
    # Si el usuario presionó "Registrar Entrega" en un pedido
    if 'registrar' in request.POST:
        try:
            pedido_id = request.POST.get('pedido_id')
            pedido = Pedido.objects.get(numero_pedido=pedido_id, estado_pedido='Pendiente')
            
            # 
            fecha_entrega = request.POST.get('fecha_entrega')
            observaciones = request.POST.get('observaciones_entrega', '')
            
            # Actualizamos el pedido
            pedido.estado_pedido = 'Entregado'
            pedido.fecha_entrega = fecha_entrega
            # Añadimos las observaciones de entrega a las existentes
            obs_original = pedido.observaciones if pedido.observaciones else ""
            pedido.observaciones = f"{obs_original}\n[ENTREGA {fecha_entrega}]: {observaciones}".strip()
            
            pedido.save()
            messages.success(request, f"Entrega registrada exitosamente para el Pedido N° {pedido_id}.")
            
        except Pedido.DoesNotExist:
            messages.error(request, "Error: El pedido no se encontró o ya fue entregado.")
        except Exception as e:
            messages.error(request, f"Error al registrar la entrega: {e}")
        
        # Redirigimos a la misma página para limpiar todo
        return redirect('registrar_entrega')

    # Si es un GET normal (solo carga la página), context estará vacío
    return render(request, 'gestion/registrar_entrega.html', context)

@login_required
def buscar_pedidos_view(request):
    """
    Controla el Formulario para Búsqueda de Pedidos.
    Filtra por nombre/apellido de cliente o rango de fechas.
    
    """
    pedidos_encontrados = []
    
    # Valores para mantener en el formulario después de la búsqueda
    nombre_b = request.GET.get('nombre_cliente', '')
    apellido_b = request.GET.get('apellido_cliente', '')
    fecha_desde_b = request.GET.get('fecha_desde', '')
    fecha_hasta_b = request.GET.get('fecha_hasta', '')

    # Iniciamos la consulta base (todos los pedidos)
    # .select_related() optimiza la consulta trayendo los datos
    # de Cliente y PersonalDelivery en un solo viaje a la BD.
    queryset = Pedido.objects.all().select_related('cliente', 'personal_delivery')

    if 'buscar' in request.GET:
        # Filtro 1: Por Nombre o Apellido [cite: 154-155]
        if nombre_b or apellido_b:
            # Usamos Q() para búsquedas flexibles
            # __icontains es como "LIKE %valor%" (ignora mayúsculas/minúsculas)
            query_nombre = Q()
            if nombre_b:
                query_nombre |= Q(cliente__nombres__icontains=nombre_b)
            
            if apellido_b:
                query_nombre |= Q(cliente__apellidos__icontains=apellido_b)
                
            queryset = queryset.filter(query_nombre)

        # Filtro 2: Por Rango de Fechas [cite: 156]
        if fecha_desde_b and fecha_hasta_b:
            # __range es como "BETWEEN fecha1 AND fecha2"
            try:
                queryset = queryset.filter(fecha_pedido__date__range=[fecha_desde_b, fecha_hasta_b])
            except Exception as e:
                messages.error(request, "Formato de fechas incorrecto.")

        pedidos_encontrados = queryset.order_by('-fecha_pedido') # Mostrar los más nuevos primero
        
        if not pedidos_encontrados:
            messages.info(request, "No se encontraron pedidos con esos criterios.")

    context = {
        'pedidos': pedidos_encontrados,
        # Devolvemos los valores buscados para rellenar el formulario
        'valores_busqueda': {
            'nombre': nombre_b,
            'apellido': apellido_b,
            'desde': fecha_desde_b,
            'hasta': fecha_hasta_b,
        }
    }
    return render(request, 'gestion/buscar_pedidos.html', context)

@login_required
def consultar_delivery_view(request):
    """
    Controla el Formulario para Consultar los Pedidos entregados por el Personal.
    Busca al personal y luego lista sus pedidos entregados.
    
    """
    personal_encontrado = None
    pedidos_entregados = []
    
    # Valores para mantener en el formulario
    dni_b = request.GET.get('dni_personal', '')
    nombres_b = request.GET.get('nombres_personal', '')
    apellidos_b = request.GET.get('apellidos_personal', '')

    if 'buscar' in request.GET:
        # 1. Buscar al Personal de Delivery 
        try:
            query_personal = Q()
            if dni_b:
                query_personal &= Q(dni=dni_b)
            if nombres_b:
                query_personal &= Q(nombres__icontains=nombres_b)
            if apellidos_b:
                query_personal &= Q(apellidos__icontains=apellidos_b)
            
            # Si no hay criterios, no buscar
            if not query_personal:
                messages.error(request, "Debe ingresar al menos un criterio de búsqueda.")
            else:
                personal_encontrado = PersonalDelivery.objects.filter(query_personal).first()
            
            if personal_encontrado:
                # 2. Si se encuentra, buscar sus pedidos ENTREGADOS 
                messages.success(request, f"Mostrando pedidos entregados por: {personal_encontrado.nombres} {personal_encontrado.apellidos}")
                pedidos_entregados = Pedido.objects.filter(
                    personal_delivery=personal_encontrado,
                    estado_pedido='Entregado'
                ).select_related('cliente').order_by('-fecha_entrega')
                
                if not pedidos_entregados:
                    messages.info(request, "Este personal no tiene pedidos entregados registrados.")
            elif query_personal:
                messages.error(request, "No se encontró personal de delivery con esos criterios.")
                
        except Exception as e:
            messages.error(request, f"Error en la búsqueda: {e}")

    context = {
        'pedidos': pedidos_entregados,
        'personal': personal_encontrado,
        # Devolvemos los valores buscados
        'valores_busqueda': {
            'dni': dni_b,
            'nombres': nombres_b,
            'apellidos': apellidos_b,
        }
    }
    return render(request, 'gestion/consultar_delivery.html', context)