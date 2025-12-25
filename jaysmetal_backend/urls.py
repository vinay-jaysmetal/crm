"""
URL configuration for jaysmetal_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
import socket
import sentry_sdk
import logging
logger = logging.getLogger(__name__)
from django.urls import include

from jaysmetal_backend import settings
from django.conf.urls.static import static


from django.http import JsonResponse
def health_check(request):
    return JsonResponse({"status": "ok"})

def debug_view(request):
    """
    Generate Traffic:
        Use ab (Apache Benchmark) to test:
        ab -n 1000 -c 10 http://your-server-ip/debug/
    """
    
    return JsonResponse({"host": socket.gethostname()})
    
def trigger_error(request):
    try:
        division_by_zero = 1 / 0
    except Exception as exc:
        logger.error("error occured +++- {}".format(str(exc)))


        # sentry_sdk.capture_exception("Excepction: "+str(exc))
        return JsonResponse({"error": str(exc)})
    

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('health-check/', health_check),
    path('debug/', debug_view),
    
    path('sentry-debug/', trigger_error),
    
    path('splash/', include('core_app.urls')),
    path('core/', include('core_app.urls')),
    path('user/', include('user_app.urls')),
    path('organization/', include('organization_app.urls')),
    
    path('department/', include('department_app.urls')),
    path('project/', include('project_app.urls')),
    path('fab-list/', include('fablist_app.urls')),
    path('notifications/', include('notification_app.urls')),
    path('settings/', include('settings_app.urls')),
    path('reports/', include('reports_app.urls')),
    path('crm/', include('crm_app.structural.urls')),
    path('crm/', include('crm_app.architectural.urls')),

    
]



if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_URL)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)