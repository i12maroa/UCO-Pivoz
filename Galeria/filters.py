import django_filters
from Galeria.models import *

class AlbumFilter(django_filters.FilterSet):
    """Declara un uevo filtro para buscar álbumes por usuario"""
    class Meta:
        model = Album
        fields = ['id_album', 'titulo', 'descripcion', 'usuario','evento']

    @property
    def qs(self):
        parent = super(AlbumFilter, self).qs
        administrador = getattr(self.request, 'user', None)
        usuarios = administrador.usuarios.all()
        return parent.filter(usuario__in=usuarios)