from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets
import string

class Perfil(models.Model):
    PRIVACIDAD_CHOICES = [
        ('publico', 'Público'),
        ('amigos', 'Solo amigos'),
        ('privado', 'Privado'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    biografia = models.TextField(blank=True, null=True)
    enlace = models.URLField(blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)
    privacidad = models.CharField(max_length=10, choices=PRIVACIDAD_CHOICES, default='publico')
    fecha_nacimiento = models.DateField(blank=True, null=True)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

class Amistad(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]
    
    usuario_solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    usuario_receptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_recibidas')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ('usuario_solicitante', 'usuario_receptor')
    
    def __str__(self):
        return f"{self.usuario_solicitante.username} -> {self.usuario_receptor.username} ({self.estado})"

class Publicacion(models.Model):
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='publicaciones')
    contenido = models.TextField()
    imagen = models.ImageField(upload_to='publicaciones/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    publicacion_compartida = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='compartidas')
    es_compartida = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.autor.username} - {self.contenido[:50]}..."

class Comentario(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f"{self.autor.username} en {self.publicacion.id}"

class Reaccion(models.Model):
    TIPO_CHOICES = [
        ('like', 'Me gusta'),
        ('love', 'Me encanta'),
        ('dislike', 'No me gusta'),
    ]
    
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='reacciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('publicacion', 'usuario')
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tipo} en {self.publicacion.id}"

class Reporte(models.Model):
    TIPO_CHOICES = [
        ('spam', 'Spam'),
        ('acoso', 'Acoso'),
        ('contenido_inapropiado', 'Contenido inapropiado'),
        ('otro', 'Otro'),
    ]
    
    reportador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes_hechos')
    usuario_reportado = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes_recibidos', blank=True, null=True)
    publicacion_reportada = models.ForeignKey(Publicacion, on_delete=models.CASCADE, blank=True, null=True)
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES)
    descripcion = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    resuelto = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reporte de {self.reportador.username} - {self.tipo}"

class Bloqueo(models.Model):
    usuario_bloqueador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuarios_bloqueados')
    usuario_bloqueado = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bloqueado_por')
    fecha_bloqueo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario_bloqueador', 'usuario_bloqueado')
    
    def __str__(self):
        return f"{self.usuario_bloqueador.username} bloqueó a {self.usuario_bloqueado.username}"

class TokenRecuperacion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    tipo = models.CharField(max_length=10, choices=[('email', 'Email'), ('sms', 'SMS')], default='email')
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        super().save(*args, **kwargs)
    
    def is_valid(self):
        from datetime import timedelta
        return not self.usado and (timezone.now() - self.fecha_creacion) < timedelta(hours=1)
    
    def __str__(self):
        return f"Token para {self.user.username} - {self.tipo}"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
