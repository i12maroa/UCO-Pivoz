from django.shortcuts import render_to_response, redirect, HttpResponseRedirect, reverse, render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from Galeria.models import RegularUser, RFIDMiddleware, AdminUser
from ipware import get_client_ip
from django.http import JsonResponse



import secrets


# Vista de menu principal
@login_required()
def index(request):
    return render_to_response('index.html', locals(), RequestContext(request))

# Vista de página de perfil
@login_required()
def profile(request):
    usuario = RegularUser.objects.get(pk=request.user)
    admins = usuario.get_admin_user()
    return render_to_response("profile.html", locals(), RequestContext(request))


def recibir_rfid(request):
    """ Función para recibir el código RFID y generar el Token de acceso a la aplicación

                            Parameters
                            ----------
                            request:
                                Objeto HTTPRequest

                            Returns
                            ------
                            string
                                Token de acceso

                    """
    if request.method == 'POST':
        rfid_id = request.POST.get('rfid_id')
        try:
            user = RegularUser.objects.get(rfid=rfid_id)
            token = secrets.token_hex(20)
            rfid_object = RFIDMiddleware()
            rfid_object.user = user
            rfid_object.token = token
            rfid_object.rfid_id = rfid_id
            rfid_object.save()
            return JsonResponse({'token': token})
        except RegularUser.DoesNotExist:
            token = 0
            rfid_object = RFIDMiddleware()
            rfid_object.rfid_id = rfid_id
            rfid_object.token = token
            rfid_object.save()
            return JsonResponse({'token': token})
    else:
        client_ip, is_routable = get_client_ip(request)
        return render(request, 'registration/login.html', {'cliente': client_ip})


def rfid_login(request, access_token):
    """ Vista de inicio de sesión mediante RFID. Autentica al usuario mediante código RFID haciendo uso del backend
    RFIDBackend.

                            Parameters
                            ----------
                            request: HTTPRequest
                                petición del usuario

                            Returns
                            ------
                            request
                                Redirige al usuario al menú principal de Pivoz

                    """
    # TODO: Mostrar el mensaje de error en caso de que haya un usuario autenticado y otro distinto intente iniciar sesión
    if request.user.is_authenticated:
        try:
            act = RFIDMiddleware.objects.get(token=access_token)
            rfid = act.rfid_id
            act.delete()
            if request.user.is_staff:
                messages.warning(request, "El código que estás intentando usar ya está asociado a un usuario."
                                          " Por favor, inténtelo de nuevo con otro código distinto.")
                return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))
            else:
                usuario = RegularUser.objects.get(rfid=rfid)
                if request.user.pk == usuario.pk:
                    logout(request)
                    return HttpResponseRedirect(reverse("logout"))
                messages.warning(request, "Ya hay una sesión iniciada. Por favor, cierra sesión e inténtelo de nuevo.")
                return HttpResponseRedirect(reverse('home'))
        except RFIDMiddleware.DoesNotExist:
            return HttpResponseRedirect(reverse('home'))

    else:
        try:
            usuario = RFIDMiddleware.objects.get(token=access_token)
            print (usuario.user.username)
            rfid_id = usuario.rfid_id
            usuario.delete()
            print (rfid_id)
            user = authenticate(request, rfid=rfid_id)
            print (user is not None)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('home'))
            else:
                messages.error(request,
                               "No existe ningún usuario con ese código. Asegúrese de que su usuario tiene un código "
                               "RFID asociado e inténtelo de nuevo")
                return HttpResponseRedirect(reverse('login'))
        except usuario.DoesNotExist:
            return HttpResponseRedirect(reverse('home'))


def my_login(request):
    """ Función de login. Permite autenticar un usuario mediante nombre de usuario y contraseña

                            Parameters
                            ----------
                            request: HTTTPRequest Object
                                Petición del usuario

                            Returns
                            ------
                            request
                                Redirige al usuario al menú principal de Pivoz

                    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                if user.is_superuser or user.is_staff:
                    return HttpResponseRedirect(reverse('admin:index'))
                else:
                    return HttpResponseRedirect(reverse('home'))
            else:
                messages.warning(request, "Tu cuenta no está activada. Por favor revisa tu correo electrónico antes de"
                                          " iniciar sesión.")
        else:
            messages.error(request, "El nombre de usuario o contraseña son incorrectos")
            return HttpResponseRedirect(reverse('home'))
    else:
        return render(request, 'registration/login.html')


