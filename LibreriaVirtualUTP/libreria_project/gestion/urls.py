from django.urls import path
from . import views  # Importa las vistas (lógica) de la app 'gestion'

urlpatterns = [
    # Página de inicio (será nuestro menú principal)
    path('', views.home_view, name='home'),
    # Página de Login [cite: 209]
    path('login/', views.login_view, name='login'),
    # Acción de Logout
    path('logout/', views.logout_view, name='logout'),
    # Esta será la URL para nuestro formulario de registrar pedido:
    # Ej: http://127.0.0.1:8000/pedidos/nuevo/
    path('pedidos/nuevo/', views.registrar_pedido_view, name='registrar_pedido'),
    
    path('clientes/', views.cliente_list_view, name='cliente_list'),
    path('clientes/modificar/<str:dni>/', views.cliente_update_view, name='cliente_update'),
    path('clientes/eliminar/<str:dni>/', views.cliente_delete_view, name='cliente_delete'),
    path('productos/', views.producto_list_view, name='producto_list'),
    path('productos/modificar/<str:serie>/', views.producto_update_view, name='producto_update'),
    path('productos/eliminar/<str:serie>/', views.producto_delete_view, name='producto_delete'),
    path('categorias/', views.categoria_list_view, name='categoria_list'),
    path('categorias/modificar/<int:id>/', views.categoria_update_view, name='categoria_update'),
    path('categorias/eliminar/<int:id>/', views.categoria_delete_view, name='categoria_delete'),
    
    path('personal/', views.personal_list_view, name='personal_list'),
    path('personal/modificar/<str:dni>/', views.personal_update_view, name='personal_update'),
    path('personal/eliminar/<str:dni>/', views.personal_delete_view, name='personal_delete'),
    
    path('pedidos/registrar-entrega/', views.registrar_entrega_view, name='registrar_entrega'),
    
    path('pedidos/buscar/', views.buscar_pedidos_view, name='buscar_pedidos'),
    path('pedidos/consultar-delivery/', views.consultar_delivery_view, name='consultar_delivery'),
]