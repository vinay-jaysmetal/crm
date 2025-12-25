from department_app.utils import get_department_qs_common_method
from project_app.models import ProjectModel, ProjectUserModel
import os
from django.utils.text import slugify
from django.db.models import Sum, F, ExpressionWrapper, FloatField

def project_gallery_upload_path(instance, filename):
    # Slugify project name to make it filesystem-safe
    project_name = slugify(instance.project.name)
    # Optionally prefix with ID
    folder_name = f"{instance.project.id:02}_{project_name}"
    return os.path.join("project_gallery", folder_name, filename)


def create_bulk_project_users(model_obj,user_qs):
    """
    Create a bulk fabrication list from the request data.
    
    """
    try:
        
        # Use bulk_create for efficiency
        project_users_objects = []
        for user_obj in user_qs:
            project_users_objects.append(
                ProjectUserModel(
                    project=model_obj,
                    organization=user_obj.organization,
                    department=user_obj.department,
                    is_active=True,
                    
                    # UserSnapshotMixin fields
                    user=user_obj,
                    user_first_name=user_obj.first_name,
                    user_email=user_obj.email,
                    user_mobile=user_obj.mobile,
                    user_id_value=user_obj.id,
                )
            )
            print("Project users objects",project_users_objects)
        ProjectUserModel.objects.bulk_create(project_users_objects)
        return True, "Data created","Bulk User list created successfully"
    except Exception as e:
        msg = f"Error creating bulk User list: {e}"
        print(msg)
        return False,"Data not created", msg
        
def xupdate_project_progress(obj):
    from fablist_app.models import FabricationListModel
    
    print("Updating project progress ",obj)
    project = obj
    if not project:
        return
    if not isinstance(project, ProjectModel):
        raise Exception("Update project progress: Object must be ProjectModel")

    # Get all fabrication lists under this project
    fab_lists = project.fablist_project.all()
    # print("Fab lists ",fab_lists)

    # For each department, compute average progress and total qty/kg
    departments = get_department_qs_common_method().filter(is_active=True).values_list("name", flat=True)

    for dept in departments:
        total_progress = 0
        
        for fab in fab_lists: # Scope change so commented
            total_progress += getattr(fab, f"{dept}_progress_percentage", 0)
            # print("fab ",fab, f"{dept}_progress_percentage", getattr(fab, f"{dept}_progress_percentage", 0))
        count = fab_lists.count() or 1  # avoid division by zero
        setattr(project, f"total_{dept}_progress_percentage", round(total_progress / count, 2))
        
        

    totals = fab_lists.aggregate(
        total_kg=Sum(ExpressionWrapper(F('kg') * F('qty'), output_field=FloatField())),
        total_project_progress=Sum('total_progress')/len(fab_lists)
    )
    print("totals 1 ",totals)

    project.total_kg = totals['total_kg'] or 0
    print("project.total_kg ",project.total_kg )
    project.total_project_progress = round(totals['total_project_progress'],2) or 0
    
    total_used = (project.total_project_progress * project.total_kg) / 100
    project.total_unused_kg = project.total_kg - total_used

    project.save()
    print("Updated project progress ............")
    
def update_project_progress(obj):
    from fablist_app.models import FabricationListModel

    print("Updating project progress", obj)
    project = obj
    if not project:
        return
    if not isinstance(project, ProjectModel):
        raise Exception("Update project progress: Object must be ProjectModel")

    fab_lists = project.fablist_project.all()

    departments = get_department_qs_common_method().filter(is_active=True).values_list("name", flat=True)

    for dept in departments:
        total_progress = 0
        for fab in fab_lists:
            total_progress += getattr(fab, f"{dept}_progress_percentage", 0)
        count = fab_lists.count() or 1
        setattr(project, f"total_{dept}_progress_percentage", round(total_progress / count, 2))

    # Compute total_kg across all fabrication items
    total_kg = 0
    total_used_kg = 0

    for fab in fab_lists:
        item_kg = (fab.kg or 0) * (fab.qty or 0)
        total_kg += item_kg

        item_progress = getattr(fab, 'total_progress', 0) or 0  # default to 0 if missing
        used_kg = (item_kg * item_progress) / 100
        total_used_kg += used_kg

    total_project_progress = (total_used_kg / total_kg * 100) if total_kg else 0
    total_unused_kg = total_kg - total_used_kg

    # Update the project
    project.total_kg = round(total_kg,2)
    project.total_project_progress = round(total_project_progress, 2)
    project.total_unused_kg = round(total_unused_kg, 2)
    project.save()
    

    print("Updated project progress. ------------------------------------------------------------")
