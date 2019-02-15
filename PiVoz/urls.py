"""PiVoz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from PiVoz import views
from .views import index, profile
from django.conf import settings
from django.conf.urls.static import static
from django_registration.backends.activation.views import RegistrationView
from Galeria.forms import AdminUserForm
from django.contrib.auth import views as auth_views

urlpatterns = [
                  path('jet/', include('jet.urls', 'jet')),
                  path('jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),
                  path('admin/', admin.site.urls),
                  path('galeria/', include('Galeria.urls')),
                  path('login/rfid/', views.rfid_login, name='RFIDlogin'),
                  # path('login/', views.my_login, name='myLogin'),
                  path('logout/', auth_views.LogoutView.as_view(), {'next_page': 'http://127.0.0.1:8000'}, name='logout'),
                  path('accounts/', include('django.contrib.auth.urls')),
                  path(
                      'accounts/register/',
                       RegistrationView.as_view(form_class=AdminUserForm),
                       name='django_registration_register'),
                  path('accounts/', include('django_registration.backends.activation.urls')),
                  # path('login/', myLogin, name='myLogin' ),
                  path('', index, name="home"),
                  path('profile/', profile, name='profile'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                                           document_root=settings.MEDIA_ROOT)
