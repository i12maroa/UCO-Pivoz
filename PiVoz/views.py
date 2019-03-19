from django.shortcuts import render_to_response, redirect, HttpResponseRedirect, reverse, render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from Galeria.SimpleMFRC522 import SimpleMFRC522
from django.views.decorators.csrf import csrf_protect


@login_required()
def index(request):
    return render_to_response('index.html', locals(), RequestContext(request))


@login_required()
def profile(request):
    return render_to_response("profile.html", locals(), RequestContext(request))

def rfid_login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    if request.method=='POST':
        rfid = request.POST.get('rfid_id')
        if rfid == "":
            messages.error(request, "Error en la lectura. Por favor, acerque la pulsera al lector")
            return HttpResponseRedirect(reverse('RFIDlogin'))
        user = authenticate(request, rfid=rfid)
        if user is not None:
            login(request, user)
            print("Logueado")
            return HttpResponseRedirect(reverse('home'))
        else:
            messages.error(request, "No existe ningún usuario con ese código. Asegúrese de que su usuario tiene un código RFID asociado e inténtelo de nuevo")
            return HttpResponseRedirect(reverse('RFIDlogin'))
    else:
        return render(request, 'registration/login.html', locals())



def rfid22_login(request):
    reader = SimpleMFRC522()
    try:
        import RPi.GPIO as GPIO
        rfid_id, rfid_txt = reader.read()
        #print(rfid_id)
        user = authenticate(request, rfid=rfid_id)
        if user is not None:
            login(request, user)
            return render_to_response('index.html', locals())
        else:
            return render_to_response('registration/login.html', {'error_message': "La pulsera asociada no existe." })
    except ImportError:
        return render_to_response('registration/login.html',
                                  {'error_message':'No se ha podido establecer comunicación con el lector.'})
    finally:
        GPIO.cleanup()

    #return render(request, 'registration/login.html')


# def my_login(request):
#     error = ""
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         user = authenticate(username=username, password=password)
#         if user is not None:
#             if user.is_active:
#                 login(request, user)
#                 if user.is_staff:
#                     return redirect(reverse('admin:index'))
#                 else:
#                     return redirect(reverse('home'))
#             else:
#                 error = "El usuario no está activo. Por favor, revise su correo electrónico y verifique su cuenta."
#         else:
#             error = "Nombre de usuario o contraseña no válidos"
#     return render_to_response('registration/login.html',  locals(), RequestContext(request))




# TODO: Login with RFID
# def myLogin(request):
#     reader = SimpleMFRC522()
#     if (request.POST['username'] != ""):
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         return HttpResponseRedirect(reverse('home'))
#     else:
#         try:
#             rfid_id, rfid_txt = reader.read()
#             user = RegularUser.objects.get(rfid=rfid_id)
#             user = authenticate(request, username=user.username, password=user.password)
#         except RegularUser.DoesNotExist:
#             errorMsg = "No existe ningún usuario asociado con ese RFID."
#             return render_to_response('registration/login.html', locals())
#         finally:
#             GPIO.cleanup()
#     if user is not None:
#         login(request, user)
#         return HttpResponseRedirect(reverse('home'))
#
#     else:
#         errorMsg = "El nombre de usuario y contraseña no coinciden. Por favor, intentalo de nuevo"
#         return render_to_response('registration/login.html', locals())
