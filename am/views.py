from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .forms import PerfilForm, PublicacionForm, ComentarioForm, BusquedaForm, ReporteForm
from .models import Perfil, Publicacion, Comentario, Reaccion, Amistad, Bloqueo, Reporte, TokenRecuperacion



def pagina_principal(request):
    return render(request, 'index.html')



def loadlogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('two_factor:login')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'login.html')



@login_required
def cerrar_sesion(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('two_factor:login')



def register(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        username = request.POST['userName']
        correo = request.POST['correo']
        telefono = request.POST.get('telefono', '')
        contrasena = request.POST['contrasena']

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'register.html')
        
        # Verificar si el email ya existe
        if User.objects.filter(email=correo).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'register.html')

        try:
            user = User.objects.create(
                username=username,
                first_name=nombre,
                last_name=apellido,
                email=correo,
                password=make_password(contrasena)
            )
            user.save()
            
            # Actualizar perfil con teléfono
            if telefono:
                user.perfil.telefono = telefono
                user.perfil.save()
            
            messages.success(request, 'Usuario registrado exitosamente. Ahora puedes iniciar sesión.')
            return redirect('two_factor:login')
        except Exception as e:
            messages.error(request, 'Error al crear el usuario. Inténtalo de nuevo.')
            return render(request, 'register.html')
    return render(request, 'register.html')



@login_required
def home(request):
    # Obtener todas las publicaciones de todos los usuarios, ordenadas por fecha
    publicaciones = Publicacion.objects.all().select_related('autor').prefetch_related('comentarios', 'reacciones').order_by('-fecha_creacion')
    

    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES)
        if form.is_valid():
            publicacion = form.save(commit=False)
            publicacion.autor = request.user
            publicacion.save()
            messages.success(request, 'Publicación creada exitosamente.')
            return redirect('home')
    else:
        form = PublicacionForm()
    

    paginator = Paginator(publicaciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'usuario': request.user,
        'form': form,
        'publicaciones': page_obj,
        'comentario_form': ComentarioForm(),
    }
    return render(request, 'home.html', context)



@login_required
def editar_perfil(request):
    perfil, created = Perfil.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('home')
    else:
        form = PerfilForm(instance=perfil)
    return render(request, 'Editar_perfil.html', {'form': form})


@login_required
def ver_perfil(request, username):
    usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Perfil, user=usuario)
    

    es_amigo = Amistad.objects.filter(
        Q(usuario_solicitante=request.user, usuario_receptor=usuario, estado='aceptada') |
        Q(usuario_solicitante=usuario, usuario_receptor=request.user, estado='aceptada')
    ).exists()
    
    # Contar amigos del usuario
    total_amigos = Amistad.objects.filter(
        Q(usuario_solicitante=usuario, estado='aceptada') |
        Q(usuario_receptor=usuario, estado='aceptada')
    ).count()
    
    solicitud_pendiente = Amistad.objects.filter(
        usuario_solicitante=request.user,
        usuario_receptor=usuario,
        estado='pendiente'
    ).exists()
    
    publicaciones = Publicacion.objects.filter(autor=usuario).select_related('autor').prefetch_related('comentarios', 'reacciones')
    
    print(f"DEBUG: Usuario: {usuario.username}, Total amigos: {total_amigos}")
    print(f"DEBUG: Total publicaciones: {publicaciones.count()}")
    if usuario != request.user:
        if perfil.privacidad == 'privado':
            publicaciones = Publicacion.objects.none()
        elif perfil.privacidad == 'amigos' and not es_amigo:
            publicaciones = Publicacion.objects.none()
    
    context = {
        'perfil_usuario': usuario,
        'perfil': perfil,
        'publicaciones': publicaciones,
        'es_amigo': es_amigo,
        'solicitud_pendiente': solicitud_pendiente,
        'es_propio_perfil': usuario == request.user,
        'total_amigos': total_amigos,
    }
    return render(request, 'perfil.html', context)


@login_required
def enviar_solicitud_amistad(request, username):
    usuario_receptor = get_object_or_404(User, username=username)
    
    if usuario_receptor == request.user:
        messages.error(request, 'No puedes enviarte una solicitud a ti mismo.')
        return redirect('ver_perfil', username=username)
    

    if Amistad.objects.filter(
        Q(usuario_solicitante=request.user, usuario_receptor=usuario_receptor) |
        Q(usuario_solicitante=usuario_receptor, usuario_receptor=request.user)
    ).exists():
        messages.error(request, 'Ya existe una solicitud de amistad.')
        return redirect('ver_perfil', username=username)
    
    Amistad.objects.create(
        usuario_solicitante=request.user,
        usuario_receptor=usuario_receptor
    )
    messages.success(request, f'Solicitud de amistad enviada a {usuario_receptor.username}.')
    return redirect('ver_perfil', username=username)

@login_required
def responder_solicitud_amistad(request, solicitud_id, accion):
    solicitud = get_object_or_404(Amistad, id=solicitud_id, usuario_receptor=request.user)
    
    if accion == 'aceptar':
        solicitud.estado = 'aceptada'
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        messages.success(request, f'Ahora eres amigo de {solicitud.usuario_solicitante.username}.')
    elif accion == 'rechazar':
        solicitud.estado = 'rechazada'
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        messages.info(request, 'Solicitud de amistad rechazada.')
    
    return redirect('solicitudes_amistad')

@login_required
def solicitudes_amistad(request):
    solicitudes = Amistad.objects.filter(
        usuario_receptor=request.user,
        estado='pendiente'
    ).select_related('usuario_solicitante')
    
    return render(request, 'solicitudes_amistad.html', {'solicitudes': solicitudes})

@login_required
def mis_amigos(request):
    amistades = Amistad.objects.filter(
        Q(usuario_solicitante=request.user, estado='aceptada') |
        Q(usuario_receptor=request.user, estado='aceptada')
    ).select_related('usuario_solicitante', 'usuario_receptor')
    
    amigos = []
    for amistad in amistades:
        if amistad.usuario_solicitante == request.user:
            amigos.append(amistad.usuario_receptor)
        else:
            amigos.append(amistad.usuario_solicitante)
    
    return render(request, 'mis_amigos.html', {'amigos': amigos})


@login_required
def editar_publicacion(request, publicacion_id):
    publicacion = get_object_or_404(Publicacion, id=publicacion_id, autor=request.user)
    
    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES, instance=publicacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publicación actualizada exitosamente.')
            return redirect('home')
    else:
        form = PublicacionForm(instance=publicacion)
    
    return render(request, 'editar_publicacion.html', {'form': form, 'publicacion': publicacion})

@login_required
def eliminar_publicacion(request, publicacion_id):
    publicacion = get_object_or_404(Publicacion, id=publicacion_id, autor=request.user)
    
    if request.method == 'POST':
        publicacion.delete()
        messages.success(request, 'Publicación eliminada exitosamente.')
        return redirect('home')
    
    return render(request, 'confirmar_eliminacion.html', {'objeto': publicacion, 'tipo': 'publicación'})


@login_required
def agregar_comentario(request, publicacion_id):
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.publicacion = publicacion
            comentario.autor = request.user
            comentario.save()
            messages.success(request, 'Comentario agregado.')
    
    return redirect('home')


@login_required
def reaccionar_publicacion(request, publicacion_id):
    if request.method == 'POST':
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)
        
        reaccion = Reaccion.objects.filter(
            publicacion=publicacion,
            usuario=request.user
        ).first()
        
        if reaccion:
            reaccion.delete()
            liked = False
        else:
            Reaccion.objects.create(
                publicacion=publicacion,
                usuario=request.user,
                tipo='like'
            )
            liked = True
        
        total_likes = publicacion.reacciones.count()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'liked': liked,
                'total_likes': total_likes
            })
    
    return redirect('home')


@login_required
def buscar_usuarios(request):
    form = BusquedaForm()
    usuarios = []
    
    if request.method == 'GET' and 'query' in request.GET:
        form = BusquedaForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            usuarios = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            ).exclude(id=request.user.id)[:20]
    
    return render(request, 'buscar_usuarios.html', {'form': form, 'usuarios': usuarios})


@login_required
def bloquear_usuario(request, username):
    usuario_a_bloquear = get_object_or_404(User, username=username)
    
    if usuario_a_bloquear == request.user:
        messages.error(request, 'No puedes bloquearte a ti mismo.')
        return redirect('ver_perfil', username=username)
    
    bloqueo, created = Bloqueo.objects.get_or_create(
        usuario_bloqueador=request.user,
        usuario_bloqueado=usuario_a_bloquear
    )
    
    if created:
    
        Amistad.objects.filter(
            Q(usuario_solicitante=request.user, usuario_receptor=usuario_a_bloquear) |
            Q(usuario_solicitante=usuario_a_bloquear, usuario_receptor=request.user)
        ).delete()
        
        messages.success(request, f'Usuario {username} bloqueado exitosamente.')
    else:
        messages.info(request, f'El usuario {username} ya estaba bloqueado.')
    
    return redirect('home')

@login_required
def reportar_usuario(request, username):
    usuario_reportado = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        form = ReporteForm(request.POST)
        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.reportador = request.user
            reporte.usuario_reportado = usuario_reportado
            reporte.save()
            messages.success(request, 'Reporte enviado exitosamente.')
            return redirect('ver_perfil', username=username)
    else:
        form = ReporteForm()
    
    return render(request, 'reportar_usuario.html', {'form': form, 'usuario_reportado': usuario_reportado})

@login_required
def tendencias(request):
    # Publicaciones más populares (con más likes)
    publicaciones_populares = Publicacion.objects.annotate(
        total_likes=models.Count('reacciones')
    ).filter(total_likes__gt=0).order_by('-total_likes', '-fecha_creacion')[:10]
    
    context = {
        'publicaciones': publicaciones_populares,
    }
    return render(request, 'tendencias.html', context)

def recuperar_contrasena(request):
    if request.method == 'POST':
        identificador = request.POST.get('identificador')
        tipo_recuperacion = request.POST.get('tipo')
        
        print(f"DEBUG: Identificador: {identificador}, Tipo: {tipo_recuperacion}")
        
        user = None
        if '@' in identificador:
            user = User.objects.filter(email=identificador).first()
            print(f"DEBUG: Buscando por email, usuario encontrado: {user}")
        else:
            perfil = Perfil.objects.filter(telefono=identificador).first()
            if perfil:
                user = perfil.user
            print(f"DEBUG: Buscando por teléfono, usuario encontrado: {user}")
        
        if user:
            token = TokenRecuperacion.objects.create(
                user=user,
                tipo=tipo_recuperacion
            )
            print(f"DEBUG: Token creado: {token.token}")
            
            if tipo_recuperacion == 'email':
                try:
                    enviar_email_recuperacion(user, token)
                    print("DEBUG: Email enviado exitosamente")
                    messages.success(request, f'Se ha enviado un enlace de recuperación a {user.email}. Revisa la consola del servidor.')
                except Exception as e:
                    print(f"DEBUG: Error enviando email: {e}")
                    messages.error(request, f'Error enviando email: {e}')
            else:
                enviar_sms_recuperacion(user, token)
                messages.success(request, f'Código SMS (simulado): {token.token[:6]}')
        else:
            messages.error(request, 'No se encontró ningún usuario con ese correo o teléfono.')
    
    return render(request, 'recuperar_contrasena.html')

def restablecer_contrasena(request, token):
    token_obj = get_object_or_404(TokenRecuperacion, token=token)
    
    if not token_obj.is_valid():
        messages.error(request, 'El enlace de recuperación ha expirado o ya fue usado.')
        return redirect('recuperar_contrasena')
    
    if request.method == 'POST':
        nueva_contrasena = request.POST.get('nueva_contrasena')
        confirmar_contrasena = request.POST.get('confirmar_contrasena')
        
        if nueva_contrasena != confirmar_contrasena:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif len(nueva_contrasena) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
        else:
            user = token_obj.user
            user.password = make_password(nueva_contrasena)
            user.save()
            
            token_obj.usado = True
            token_obj.save()
            
            messages.success(request, 'Contraseña restablecida exitosamente. Ahora puedes iniciar sesión.')
            return redirect('two_factor:login')
    
    return render(request, 'restablecer_contrasena.html', {'token': token})

def enviar_email_recuperacion(user, token):
    asunto = 'Recuperación de contraseña - AM Media'
    enlace = f'http://localhost:8000/restablecer-contrasena/{token.token}/'
    
    mensaje_texto = f"""
Hola {user.first_name},

Recibimos una solicitud para restablecer tu contraseña en AM Media.

Haz clic en este enlace para crear una nueva contraseña:
{enlace}

Este enlace expira en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Saludos,
Equipo AM Media
"""
    
    print(f"\n=== EMAIL DE RECUPERACIÓN ===")
    print(f"Para: {user.email}")
    print(f"Asunto: {asunto}")
    print(f"ENLACE DE RECUPERACIÓN: {enlace}")
    print(f"================================\n")
    
    send_mail(
        asunto,
        mensaje_texto,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def enviar_sms_recuperacion(user, token):
    # Simulación de envío de SMS
    # En producción, integrar con servicio como Twilio
    print(f"SMS enviado a {user.perfil.telefono}: Tu código de recuperación es: {token.token[:6]}")
    # En producción, aquí iría la lógica real de envío de SMS

@login_required
def compartir_publicacion(request, publicacion_id):
    publicacion_original = get_object_or_404(Publicacion, id=publicacion_id)
    
    if publicacion_original.autor == request.user:
        messages.error(request, 'No puedes compartir tu propia publicación.')
        return redirect('home')
    
    # Verificar si ya compartió esta publicación
    ya_compartida = Publicacion.objects.filter(
        autor=request.user,
        publicacion_compartida=publicacion_original,
        es_compartida=True
    ).exists()
    
    if ya_compartida:
        messages.error(request, 'Ya has compartido esta publicación.')
        return redirect('home')
    
    if request.method == 'POST':
        comentario = request.POST.get('comentario', '')
        
        Publicacion.objects.create(
            autor=request.user,
            contenido=comentario,
            publicacion_compartida=publicacion_original,
            es_compartida=True
        )
        
        messages.success(request, 'Publicación compartida exitosamente.')
        return redirect('home')
    
    return render(request, 'compartir_publicacion.html', {'publicacion': publicacion_original})

@login_required
def editar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id, autor=request.user)
    
    if request.method == 'POST':
        nuevo_contenido = request.POST.get('contenido')
        if nuevo_contenido:
            comentario.contenido = nuevo_contenido
            comentario.save()
            messages.success(request, 'Comentario actualizado.')
        return redirect('home')
    
    return render(request, 'editar_comentario.html', {'comentario': comentario})

@login_required
def eliminar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id, autor=request.user)
    
    if request.method == 'POST':
        comentario.delete()
        messages.success(request, 'Comentario eliminado.')
        return redirect('home')
    
    return render(request, 'confirmar_eliminacion.html', {'objeto': comentario, 'tipo': 'comentario'})