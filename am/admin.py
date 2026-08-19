from django.contrib import admin
from .models import Perfil, Publicacion, Comentario, Reaccion, Amistad, Bloqueo, Reporte

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'privacidad', 'ubicacion']
    list_filter = ['privacidad']
    search_fields = ['user__username', 'user__email']

@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ['autor', 'contenido', 'fecha_creacion']
    list_filter = ['fecha_creacion']
    search_fields = ['autor__username', 'contenido']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['autor', 'publicacion', 'contenido', 'fecha_creacion']
    list_filter = ['fecha_creacion']
    search_fields = ['autor__username', 'contenido']

@admin.register(Reaccion)
class ReaccionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'publicacion', 'tipo', 'fecha_creacion']
    list_filter = ['tipo', 'fecha_creacion']
    search_fields = ['usuario__username']

@admin.register(Amistad)
class AmistadAdmin(admin.ModelAdmin):
    list_display = ['usuario_solicitante', 'usuario_receptor', 'estado', 'fecha_solicitud']
    list_filter = ['estado', 'fecha_solicitud']
    search_fields = ['usuario_solicitante__username', 'usuario_receptor__username']

@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ['usuario_bloqueador', 'usuario_bloqueado', 'fecha_bloqueo']
    list_filter = ['fecha_bloqueo']
    search_fields = ['usuario_bloqueador__username', 'usuario_bloqueado__username']

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['reportador', 'usuario_reportado', 'tipo', 'resuelto', 'fecha_reporte']
    list_filter = ['tipo', 'resuelto', 'fecha_reporte']
    search_fields = ['reportador__username', 'usuario_reportado__username']
    actions = ['marcar_como_resuelto']
    
    def marcar_como_resuelto(self, request, queryset):
        queryset.update(resuelto=True)
    marcar_como_resuelto.short_description = "Marcar reportes seleccionados como resueltos"
