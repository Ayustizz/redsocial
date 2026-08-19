from django import forms
from django.contrib.auth.models import User
from .models import Perfil, Publicacion, Comentario, Reporte

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['biografia', 'enlace', 'foto', 'privacidad', 'fecha_nacimiento', 'ubicacion']
        widgets = {
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enlace': forms.URLInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'privacidad': forms.Select(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PublicacionForm(forms.ModelForm):
    class Meta:
        model = Publicacion
        fields = ['contenido', 'imagen']
        widgets = {
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '¿Qué estás pensando?'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escribe un comentario...'}),
        }

class BusquedaForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar usuarios...',
        })
    )

class ReporteForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ['tipo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
