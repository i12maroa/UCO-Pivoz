from django.contrib import admin
from .models import Album, Imagen, Keyword, Video, Radio, RegularUser
from .forms import ImageForm, AdminCreationForm, AdminChangeForm, UserCreationForm, UserChangeForm, \
    RegularUserCreationForm
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from Galeria.models import RegularUser, AdminUser
from django.utils.text import slugify
from jet.admin import CompactInline
from django.urls import reverse
from django_google_maps import widgets as map_widgets
from django_google_maps import fields as map_fields
from Galeria.tasks import check_dictionary, add_keyword_to_dict, update_grammar




class MyAdmin(AdminSite):
    """Clase AdminSite. Permite modificar parámetros del sitio de administración de Django"""
    AdminSite.site_header = 'Administración de PiVoz'


class AdminUserAdmin(BaseUserAdmin):
    # Formularios para añadir y modificar instancias de Usuarios
    form = AdminChangeForm
    add_form = AdminCreationForm


    # Los campos que se usarán para mostrar los modelos del admin
    # Los campos declarados sobreescribirán las definiciones en la base AdminUserAdmin
    list_display = ('avatarPreview', 'username', 'email', 'user_actions')
    list_filter = ('last_login',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'descripcion', 'avatar', 'telefono',)}),
        ('Administración', {'fields': ('usuarios',)}),
    )
    # add_fieldsets is not a standard Modeladmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'telefono', 'password1', 'password2', 'usuarios')}
         ),
    )
    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = ('usuarios',)
    readonly_fields = ['avatarPreview', 'user_actions', ]

    def avatar(self, obj):
        """ Función que permite visualizar la imagen de perfil de los usuarios en la página de administración de Django"""
        return mark_safe('<img style="border-radius:80px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=100,
            heigth=100,
        )
        )

    def avatarPreview(self, obj):
        """ Función que permite visualizar la imagen de perfil de los usuarios en la página de administración de Django"""
        return mark_safe('<img style="border-radius:80px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=100,
            heigth=100,
        )
        )
    avatarPreview.short_description = "Imagen de Perfil"

    def get_queryset(self, request):
        """Filtramos los adminstradores de forma que cada administrador sólo pueda acceder a su perfil"""
        qs = super(AdminUserAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)

    def get_field_queryset(self, db, db_field, request):
        """ Filtramos los usuarios de los administradores. Los administradores sólo deben poder gestionar los usuarios
        que ellos mismos han creado"""
        if db_field.name == "usuarios":
            return RegularUser.objects.filter(adminuser=request.user)

    def user_actions(self, obj):
        """Permite añadir botones de acciones a la página de administración. Añadimos botones para modificar el perfil"""
        return format_html(
            '<a class="button" href="{}" style="color:#fff; background-color:#7c0caf;">Modificar mi perfil</a>',
            reverse('admin:Galeria_adminuser_change', args=[obj.pk])
            ,)
    user_actions.short_description = "Mi perfil"
    user_actions.allow_tags = True



class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'email', 'is_staff')
    list_filter = ('is_staff',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'descripcion', 'avatar', 'telefono',)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'telefono', 'password1', 'password2',)}
         ),
    )

    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = ()

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
        # return qs.filter(adminuser=request.user)




class ImagenInstanceInline(CompactInline):
    """ Clase inline para mostrar las imágenes en una pestaña en la interfaz de Administración"""
    form = ImageForm
    model = Imagen
    fields = ('image_tag', 'titulo', 'fichero_imagen', 'keyword')
    readonly_fields = ('image_tag',)
    extra = 0
    fk_name = 'album'


class VideoInstanceInline(CompactInline):
    """ Clase inline para mostrar los vídeos en una pestaña en la interfaz de Administración"""
    model = Video
    fields = ('titulo', 'fichero_video', 'keyword')
    extra = 0
    fk_name = 'album'


class AlbumM2MInline(CompactInline):
    """ Clase inline para mostrar los álbumes del usuario en una pestaña en la interfaz de Administración"""
    model = Album.usuario.through
    extra = 0
    verbose_name = "Album del usuario"
    verbose_name_plural = "Albumes del usuario"

    def get_queryset(self, request):
        """ Filtramos el queryset inicial de videos. Muestra los videos creados por el administrador autenticado"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter()

    def get_field_queryset(self, db, db_field, request):
        """ Filtramos el campo Álbum del formulario de Albums. Muestra los álbumes creados por el administrador"""
        qs = super().get_queryset(request)
        albums = Album.objects.filter(created_by=request.user)
        if request.user.is_superuser:
            return qs
        return albums


class RegularUserAdmin(BaseUserAdmin):
    """Clase para gestionar usuarios regulares en la interfaz de administración."""
    add_form = RegularUserCreationForm
    form = UserChangeForm
    list_display = ('avatarPreview', 'username', 'email', 'rfid_vinculado', 'user_actions')
    list_filter = ('username',)
    # Campos del formulario
    fieldsets = (
        (None, {'fields': ('Avatar', 'username', 'email', 'password', 'rfid')}),
        ('Información Personal', {'fields': (('first_name', 'last_name'), 'telefono', 'descripcion', 'avatar')}),

    )
    # Campos del formulario de creación de usuario Regular
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'telefono', 'password1', 'password2', 'rfid')
        }),
    )
    # Modelos en línea. Permite agregar pestañas al panel de usuarios en la interfaz de administración
    inlines = [AlbumM2MInline]
    # Incluimos los campos de búsqueda
    search_fields = ('username'),
    ordering = ('username',)
    # Campos de sólo lectura
    readonly_fields = ['avatarPreview', 'Avatar', 'rfid','user_actions']


    def avatarPreview(self, obj):
        """ Permite visualizar una imagen en la interfaz de adminsitración de Django"""
        return mark_safe('<img style="border-radius:120px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=75,
            heigth=75,
        )
        )

    def Avatar(self, obj):
        """ Permite visualizar una imagen en la interfaz de adminsitración de Django"""
        return mark_safe('<img style="border-radius:120px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=200,
            heigth=200,
        )
        )

    def get_queryset(self, request):
        """ Filtramos el queryset inicial del modelo, de forma que solo se muestren los usuarios regulares del
        administrador autenticado"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(adminuser=request.user)

    def save_related(self, request, form, formsets, change):
        """Sobreescribimos el método save del modelo many_to_many. Esta función actualiza el usuario administrador que
        creó al usuario regular. Añade al usuario regular a la lista de usuarios del administrador."""
        obj = form.instance
        request.user.adminuser.usuarios.add(obj)
        form.save_m2m()
        super().save_related(request, form, formsets, change)

    def save_model(self, request, obj, form, change):
        """ Sobreescribimos el método save del modelo. Cada vez que se crea una instancia RegularUser, se actualizará
        la información del usuario"""
        if obj:
            super().save_model(request, obj, form, change)
            if not request.user.is_superuser:
                request.user.adminuser.usuarios.add(obj)

    def rfid_vinculado(self, obj):
        """ Indica si el usuario tiene un código RFID vinculado.
        True --> Usuario tiene código RFID
        False --> Usuario no tiene código RFID"""
        if obj.rfid != "":
            return True
        else:
            return False
    rfid_vinculado.boolean = True

    def user_actions(self, obj):
        """Permite añadir botones de acciones a la página de administración."""
        return format_html(
            '<a class="button" href="{}" style="color:#fff; background-color:#7c0caf;">Modificar Usuario</a>&nbsp;'
            '<a class="button" href="{}" style="color:#fff; background-color:#3da311;">Vincular pulsera</a>&nbsp;'
            '<a class="button" href="{}" style="color:#fff; background-color:#0e66cc;">Desvincular pulsera</a>&nbsp;'
            '<a class="button" href="{}" style="color:#fff; background-color:#0e66cc;">Compartir Usuario</a>',
            reverse('admin:Galeria_regularuser_change', args=[obj.pk]),
            reverse('ReadRFID', args=[obj.pk]),
            reverse('deleteRFID', args=[obj.pk]),
            reverse('shareUser', args=[obj.pk])
            ,)
    user_actions.short_description = "Acciones de Usuario Regular"
    user_actions.allow_tags = True



@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    """ Clase para gestionar imágenes en la interfaz de administración"""
    # Campos que van a ser mostrados en la lista de Imágenes
    list_display = ('image_tag', 'titulo', 'image_actions')
    # Campos de sólo lectura
    readonly_fields = ('image_tag', 'image_actions', 'fecha_creacion')
    # Campos del formulario para crear y modificar imágenes
    fieldsets = (
        ('General', {
            'fields': ('fichero_imagen', 'titulo', 'keyword', 'descripcion', 'album', 'image_tag'),
        }),
        ('Opciones Avanzadas', {
            'classes': ('collapse',),
            'fields': ('image_width', 'image_height', 'fecha_creacion'),
        }),
    )

    def vista_previa(self, obj):
        """ Permite crear una previsualización de la imagen en la interfaz de administración"""
        return mark_safe('<img style= border-radius:25px;"  src="{url}" width="{width}" height={height} />'.format(
            url=obj.thumbnail.url,
            width=200,
            height=200,
        )
        )

    def preview(self, obj):
        return mark_safe('<img style="border-radius:5px;" src="{url}" width="{width}" height="{height}" />'.format(
            url=obj.thumbnail.url,
            width=100,
            height=100,
        )
        )
    preview.short_description = "Vista Previa"

    def get_queryset(self, request):
        """ Filtramos el queryset inicial del modelo, de forma que solo muestre las imágenes creadas por el administrador
        autenticado"""
        qs = super(ImagenAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(album__created_by=request.user)

    def get_field_queryset(self, db, db_field, request):
        """Filtramos el queryset del campo del formulario album para que muestre solo los albumes del administrador"""
        if db_field.name == 'album':
            return Album.objects.filter(created_by=request.user)

    def image_actions(self, obj):
        """Permite añadir botones de acciones a la página de administración."""
        return format_html(
            '<a class="button" href="{}" style="color:#fff; background-color:#7c0caf;">Modificar Imagen</a>&nbsp;'
            '<a class="button " href="{}" style="color:#fff; background-color:#c14747;">Eliminar Imagen </a>',
            reverse('admin:Galeria_imagen_change', args=[obj.pk]),
            reverse('admin:Galeria_imagen_delete', args=[obj.pk])
            ,)
    image_actions.short_description = "Administrar Imagen"
    image_actions.allow_tags = True



@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    """ Clase para gestionar albumes en la interfaz de administración"""
    # Campos del modelo que van a ser mostrados
    fields = ['titulo', 'descripcion', 'thumbnail', 'keywords', 'address', 'geolocation', 'usuario']
    # Widget de Google Maps
    formfield_overrides = {
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},
    }
    # Campos de solo lectura
    readonly_fields = ['slug', 'created_by', 'album_actions']
    # Ordenamos los álbumes por fecha de creación
    date_hierarchy = 'fecha_creacion'
    # Filtros de búsqueda de álbumes
    list_filter = ('fecha_creacion',)
    # Campos que serán mostrados en la lista de álbumes de la interfaz de administración
    list_display = ('Portada', 'titulo', 'get_n_elements', 'album_actions')
    inlines = [ImagenInstanceInline, VideoInstanceInline]

    def save_model(self, request, obj, form, change):
        """Sobreescribimos el método save del modelo. Indicamos el usuario que creo el album y creamos un slug
            que permita crear patrones URL agradables"""
        if not change:
            obj.created_by = request.user.adminuser
            obj.slug = slugify(obj.titulo)
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Filtramos el queryset inicial. Los administradores solo podran gestionar los álbumes que ha creado."""
        qs = super(AlbumAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def get_field_queryset(self, db, db_field, request):
        """Filtramos el queryset del campo usuario, de forma que solo pueda seleccionar entre los usuarios gestionados
        por el administrador"""
        if db_field.name == 'usuario':
            return RegularUser.objects.filter(adminuser=request.user)

    def Portada(self, obj):
        """Permite crear una visualización de la portada del álbum para mostrarla en la interfaz de administración de Django"""
        return mark_safe('<img style="border-radius:25px;" src="{url}" width="{width}" height={height} />'.format(
            url=obj.thumbnail.url,
            width=75,
            height=75,
        )
        )
    Portada.short_description = "Portada"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """ Filtramos el queryset de los formularios de los álbumes del usuario"""
        if db_field.name == "usuario":
            kwargs["queryset"] = RegularUser.objects.filter(adminuser=request.user)
        if db_field.name == "album":
            kwargs["queryset"] = Album.objects.filter(created_by=request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def album_actions(self, obj):
        """Permite añadir botones de acción a la interfaz de administración"""
        return format_html(
            '<a class="button" href="{}" style="color:#fff; background-color:#7c0caf;">Modificar Álbum</a>&nbsp;'
            '<a class="button " href="{}" style="color:#fff; background-color:#c14747;">Eliminar Álbum </a>',
            reverse('admin:Galeria_album_change', args=[obj.pk]),
            reverse('admin:Galeria_album_delete', args=[obj.pk])
            ,)
    album_actions.short_description = "Administrar Álbum"
    album_actions.allow_tags = True


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    """ Clase que permite gestionar palabras clave en la interfaz de administración"""
    # Campos mostrados en la lista de palabras clave
    list_display = ('keyword', 'usuario')
    ordering = ('keyword',)
    # Campos del formulario de creación y modificación de palabras clave
    fields = ('keyword',)
    # Campos de búsqueda de palabras clave
    search_fields = ('keyword',)

    def save_model(self, request, obj, form, change):
        """ Sobreescribimos el método save del modelo. Añade como usuario al usuario admin que creo la palabra clave y
        además registra las palabras clave en el diccionario y en el archivo de gramática"""
        obj.keyword = obj.keyword.lower()
        words = obj.keyword.split(" ")
        for word in words:
            is_registered = check_dictionary(word)
            if not is_registered:
                add_keyword_to_dict.delay(word)
        if len(words) > 1:
            update_grammar.delay('(' + obj.keyword + ')')
        else:
            update_grammar.delay(obj.keyword)
        if request.user.is_superuser:
            pass
        else:
            obj.usuario = request.user.adminuser
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(usuario=request.user)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """ Clase que permite gestionar los vídeos en la interfaz de administración de Django"""
    list_display = ('titulo', 'video_actions')

    def get_queryset(self, request):
        qs = super(VideoAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(album__created_by=request.user)

    def get_field_queryset(self, db, db_field, request):
        if db_field.name == 'album':
            return Album.objects.filter(created_by=request.user)

    def video_actions(self, obj):
        return format_html(
            '<a class="button" href="{}" style="color:#fff; background-color:#7c0caf;">Modificar Video</a>&nbsp;'
            '<a class="button " href="{}" style="color:#fff; background-color:#c14747;">Eliminar Video </a>',
            reverse('admin:Galeria_video_change', args=[obj.pk]),
            reverse('admin:Galeria_video_delete', args=[obj.pk])
            ,)
    video_actions.short_description = "Administrar Video"
    video_actions.allow_tags = True

@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    """ Clase que permite gestionar las emisoras de radio en la interfaz de administración de Django"""
    list_display = ('image_tag', 'nombre')



admin.site.register(AdminUser, AdminUserAdmin)

admin.site.register(RegularUser, RegularUserAdmin)
