from django.contrib import admin
from .models import Role,Utilisateur , TaskType, Task ,TaskHistory,  FichierExcel, HiddenTask

# Register your models here.

admin.site.register(Role)
admin.site.register(Utilisateur)
admin.site.register(TaskType)
admin.site.register(Task)
admin.site.register(TaskHistory)
admin.site.register(FichierExcel)
admin.site.register(HiddenTask)
