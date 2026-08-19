from django.contrib import admin
from django.urls import path, include
from am import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),


    path('', views.pagina_principal, name='inicio'),


    path('register/', views.register, name='register'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('login-custom/', views.loadlogin, name='login_custom'),

    path('login/', include('two_factor.urls', namespace='two_factor')),


    path('home/', views.home, name='home'),
    

    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<str:username>/', views.ver_perfil, name='ver_perfil'),
    

    path('solicitud-amistad/<str:username>/', views.enviar_solicitud_amistad, name='enviar_solicitud_amistad'),
    path('responder-solicitud/<int:solicitud_id>/<str:accion>/', views.responder_solicitud_amistad, name='responder_solicitud_amistad'),
    path('solicitudes-amistad/', views.solicitudes_amistad, name='solicitudes_amistad'),
    path('mis-amigos/', views.mis_amigos, name='mis_amigos'),
    

    path('publicacion/editar/<int:publicacion_id>/', views.editar_publicacion, name='editar_publicacion'),
    path('publicacion/eliminar/<int:publicacion_id>/', views.eliminar_publicacion, name='eliminar_publicacion'),
    

    path('comentario/<int:publicacion_id>/', views.agregar_comentario, name='agregar_comentario'),
    path('reaccionar/<int:publicacion_id>/', views.reaccionar_publicacion, name='reaccionar_publicacion'),
    

    path('buscar/', views.buscar_usuarios, name='buscar_usuarios'),
    
    path('tendencias/', views.tendencias, name='tendencias'),
    

    path('bloquear/<str:username>/', views.bloquear_usuario, name='bloquear_usuario'),
    path('reportar/<str:username>/', views.reportar_usuario, name='reportar_usuario'),
    
    # Recuperación de contraseña
    path('recuperar-contrasena/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('restablecer-contrasena/<str:token>/', views.restablecer_contrasena, name='restablecer_contrasena'),
    
    # Compartir publicaciones
    path('compartir/<int:publicacion_id>/', views.compartir_publicacion, name='compartir_publicacion'),
    
    # Editar y eliminar comentarios
    path('comentario/editar/<int:comentario_id>/', views.editar_comentario, name='editar_comentario'),
    path('comentario/eliminar/<int:comentario_id>/', views.eliminar_comentario, name='eliminar_comentario'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
