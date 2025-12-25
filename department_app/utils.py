
from core_app.constants import DEPARTMENT_JSON
from department_app.models import DepartmentModel


def get_department_qs_common_method():
    qs = DepartmentModel.objects.all()
    if qs.count() == 0:
        for department in DEPARTMENT_JSON:
            DepartmentModel.objects.create(**department)
        
    return qs