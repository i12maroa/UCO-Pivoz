from django.contrib import admin
from .models import Album, Imagen, Keyword, Video, Musica, Radio, RegularUser
from .forms import ImageForm, AdminCreationForm, AdminChangeForm, UserCreationForm, UserChangeForm, \
    RegularUserCreationForm
from django.contrib.admin import AdminSite
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from Galeria.models import RegularUser, AdminUser
from django.utils.text import slugify
from jet.admin import CompactInline
from django_admin_row_actions import AdminRowActionsMixin
from django.urls import reverse
from django_google_maps import widgets as map_widgets
from django_google_maps import fields as map_fields
from Galeria.tasks import check_dictionary, add_keyword_to_dict, update_grammar

# from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
# from django.contrib.contenttypes.models import ContentType
# from django.db.models.signals import pre_save
# from django.dispatch import receiver

import logging


class MyAdmin(AdminSite):
    AdminSite.site_header = 'Administración de PiVoz'


# Register your models here.


class AdminUserAdmin(BaseUserAdmin):
    # The forms to add and change admin instances
    form = AdminChangeForm
    add_form = AdminCreationForm

    # The fields to be used in displaying the Admin model.
    # These overrides the definitions on the base AdminUserAdmin
    # that reference specific fields on auth.User
    list_display = ('avatarPreview', 'username', 'email',)
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
    readonly_fields = ['avatarPreview', ]

    def avatar(self, obj):
        return mark_safe('<img style="border-radius:80px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=100,
            heigth=100,
        )
        )

    def avatarPreview(self, obj):
        return mark_safe('<img style="border-radius:80px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=100,
            heigth=100,
        )
        )

    def get_queryset(self, request):
        qs = super(AdminUserAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)

    def get_field_queryset(self, db, db_field, request):
        if db_field.name == "usuarios":
            return RegularUser.objects.filter(adminuser=request.user)


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
    form = ImageForm
    model = Imagen
    fields = ('image_tag', 'titulo', 'fichero_imagen', 'keyword')
    readonly_fields = ('image_tag',)
    extra = 0
    fk_name = 'album'


class VideoInstanceInline(CompactInline):
    model = Video
    fields = ('titulo', 'fichero_video', 'keyword')
    extra = 0
    fk_name = 'album'


class AlbumM2MInline(CompactInline):
    model = Album.usuario.through
    #fields = ('thumbnail_tag', 'titulo', 'evento', 'thumbnail', 'created_by',)
    extra = 0
    verbose_name = "Album del usuario"
    verbose_name_plural = "Albumes del usuario"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter()

    def get_field_queryset(self, db, db_field, request):
        qs = super().get_queryset(request)
        albums = Album.objects.filter(created_by=request.user)
        if request.user.is_superuser:
            return qs
        return albums

    # def formfield_for_manytomany(self, db_field, request, **kwargs):
    #     kwargs["queryset"] = RegularUser.objects.filter(usuario=)
    #     return super().formfield_for_manytomany(db_field, request, **kwargs)

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     if request.user.is_superuser:
    #         return qs
    #     return qs.filter(album__created_by=request.user)



# class AlbumInstanceInline(CompactInline):
#     model = Album
#     extra = 0
#     fields = ('thumbnail_tag', 'titulo', 'evento', 'thumbnail', 'created_by',)
#     #fields = ('thumbnail_tag', 'titulo', 'keywords', 'thumbnail')
#     readonly_fields = ('thumbnail_tag',)
#     extra = 0
#     verbose_name = "Album del usuario"
#     verbose_name_plural = "Albumes del usuario"
#     fk_name = 'usuario'


class RegularUserAdmin(AdminRowActionsMixin, BaseUserAdmin):
    add_form = RegularUserCreationForm
    form = UserChangeForm
    list_display = ('avatarPreview', 'username', 'email')
    list_filter = ('username',)
    fieldsets = (
        (None, {'fields': ('Avatar', 'username', 'email', 'password', 'rfid')}),
        ('Información Personal', {'fields': (('first_name', 'last_name'), 'telefono', 'descripcion', 'avatar')}),

    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'telefono', 'password1', 'password2', 'rfid')
        }),
    )
    inlines = [AlbumM2MInline]
    search_fields = ('username'),
    ordering = ('username',)
    readonly_fields = ['avatarPreview', 'Avatar', 'rfid']

    def get_row_actions(self, obj):
        row_actions = [
            {
                'label': 'Vincular Pulsera',
                'url': reverse('ReadRFID', args=[obj.id])
            },
        ]
        row_actions += super(RegularUserAdmin, self).get_row_actions(obj)
        return row_actions

    def avatarPreview(self, obj):
        return mark_safe('<img style="border-radius:120px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=75,
            heigth=75,
        )
        )

    def Avatar(self, obj):
        return mark_safe('<img style="border-radius:120px;" src="{url}" width="{width}" heigth={heigth} />'.format(
            url=obj.avatar.url,
            width=200,
            heigth=200,
        )
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        print (qs.filter(adminuser=request.user))
        if request.user.is_superuser:
            return qs
        return qs.filter(adminuser=request.user)
        #return qs.filter(adminuser=request.user)

    def save_related(self, request, form, formsets, change):
        obj = form.instance
        request.user.adminuser.usuarios.add(obj)
        form.save_m2m()
        super().save_related(request, form, formsets, change)

    def save_model(self, request, obj, form, change):
        if obj:
            super().save_model(request, obj, form, change)
            if not request.user.is_superuser:
                request.user.adminuser.usuarios.add(obj)

    # def save_formset(self, request, form, formset, change):
    #     logger = logging.getLogger(__name__)
    #     logger.debug('Guarda')
    #     if formset.model == Album:
    #         for f in formset.forms:
    #             if not f.instance.created_by:
    #                 f.instance.created_by = request.user.adminuser
    #                 f.instance.save()
    #         formset.save()
    #         formset.save_m2m()
    #     else:
    #         pass


@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    list_display = ('preview', 'titulo')
    exclude = ('path',)
    # fields = ('image_tag',)
    readonly_fields = ('vista_previa',)

    def vista_previa(self, obj):
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

    def get_queryset(self, request):
        qs = super(ImagenAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(album__created_by=request.user)

    def get_field_queryset(self, db, db_field, request):
        if db_field.name == 'album':
            return Album.objects.filter(created_by=request.user)



@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    fields = ['titulo', 'descripcion', 'thumbnail', 'keywords', 'address', 'geolocation', 'usuario', 'slug',
              'created_by']
    formfield_overrides = {
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},
    }
    # prepopulated_fields = {'slug': ('titulo',)}
    readonly_fields = ['slug', 'created_by' ]
    date_hierarchy = 'fecha_creacion'
    list_filter = ('fecha_creacion', 'usuario')
    list_display = ('Portada', 'titulo')
    inlines = [ImagenInstanceInline, VideoInstanceInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.adminuser
            obj.slug = slugify(obj.titulo)
        super().save_model(request, obj, form, change)

    # def save_related(self, request, form, formsets, change):
    #     obj = form.instance
    #     if request.user.is_superuser:
    #         obj.created_by = 1
    #
    #     obj.created_by = request.user.adminuser
    #     obj.slug = slugify(obj.titulo)
    #     super().save_related(request, form, formsets, change)

    def get_queryset(self, request):
        qs = super(AlbumAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def Portada(self, obj):
        return mark_safe('<img style="border-radius:25px;" src="{url}" width="{width}" height={height} />'.format(
            url=obj.thumbnail.url,
            width=75,
            height=75,
        )
        )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "usuario":
            kwargs["queryset"] = RegularUser.objects.filter(adminuser=request.user)
        if db_field.name == "album":
            kwargs["queryset"] = Album.objects.filter(created_by=request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    # def save_formset(self, request, form, formset, change):
    #     if formset.model == RegularUser:
    #         instances = formset.save(commit=False)
    #         for instance in instances:
    #             instance.created_by = request.user
    #             instance.save()
    #     else:
    #         formset.save()


# def get_queryset(self, request):
#     qs = super(AlbumAdmin, self).get_queryset(request)
#     if request.user.is_superuser:
#         return qs
#
#     album_ct = ContentType.objects.get_for_model(Album)
#     user_ct = ContentType.objects.get_for_model(RegularUser)
#     log_entries = LogEntry.objects.filter(
#         content_type__in=[album_ct, user_ct],
#         user=request.user,
#         action_flag__in=[ADDITION]
#     )
#     user_album_ids = [a.object_id for a in log_entries]
#     print(user_album_ids)
#     return qs.filter(id_album__in=user_album_ids)


# def save_formset(self, request, form, formset, change):
#     if formset.model == Album:
#         instances = formset.save(commit = False)
#         for instance in instances:
#             instance.user = request.user
#             instance.save()
#     else:
#         formset.save()


# def get_form(self, request, obj=None, change=False, **kwargs):
#     if request.user.is_superuser:
#         return super(AlbumAdmin, self).get_form(request, obj, **kwargs)
#
#     evento_ct = ContentType.objects.get_for_model(Evento)
#     log_entries = LogEntry.objects.filter(
#         content_type=evento_ct,
#         user=request.user,
#         action_flag=ADDITION
#     )
#     user_evento_ids = [a.object_id for a in log_entries]
#     form = super(AlbumAdmin, self).get_form(request, obj, **kwargs)
#     form.base_fields['usuario'].queryset = RegularUser.objects.filter(adminuser__usuarios__adminuser=request.user).distinct()
#     form.base_fields['evento'].queryset = Evento.objects.filter(id_evento__in=user_evento_ids).distinct()
#     return form

# def get_queryset(self, request):
#     qs = super(AlbumAdmin, self).get_queryset(request)
#     if request.user.is_superuser:
#         return qs
#     return qs.filter( = request.user)


# @admin.register(Evento)
# class EventoAdmin(admin.ModelAdmin):
#     list_display = ['nombre', 'ubicacion']
#
#     def get_queryset(self, request):
#         qs = super(EventoAdmin, self).get_queryset(request)
#         if request.user.is_superuser:
#             return qs
#
#         evento_ct = ContentType.objects.get_for_model(Evento)
#         log_entries = LogEntry.objects.filter(
#             content_type=evento_ct,
#             user=request.user,
#             action_flag=ADDITION
#         )
#         print ("Entra Evento")
#         user_evento_ids = [a.object_id for a in log_entries]
#         return qs.filter(id_evento__in=user_evento_ids)


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'usuario')
    ordering = ('keyword',)
    fields = ('keyword',)
    search_fields = ('keyword',)

    # Añade como usuario al usuario admin que creo la palabra clave
    def save_model(self, request, obj, form, change):
        obj.keyword = obj.keyword.lower()
        is_registered = check_dictionary.delay(obj.keyword)
        if is_registered:
            print("La palabra " + obj.keyword + " está registrada en el diccionario.")
            update_grammar.delay(obj.keyword)
            # super(Keyword, obj).save()
        else:
            add_keyword_to_dict.delay(obj.keyword)
            update_grammar.delay(obj.keyword)
            # super(Keyword, obj).save(*args, **kwargs)
        if request.user.is_superuser:
            obj.usuario = 1
        obj.usuario = request.user.adminuser
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(usuario=request.user)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo',)
    exclude = ('path',)

    def get_queryset(self, request):
        qs = super(VideoAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(album__created_by=request.user)


@admin.register(Musica)
class MusicaAdmin(admin.ModelAdmin):
    list_display = ('titulo',)
    exclude = ('descripcion', 'path', 'fecha_creacion',)


@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

    # Now register the new UserAdmin...


# admin.site.register(MyUser, UserAdmin)


admin.site.register(AdminUser, AdminUserAdmin)

admin.site.register(RegularUser, RegularUserAdmin)
