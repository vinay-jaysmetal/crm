


from department_app.utils import get_department_qs_common_method
from project_app.models import ProjectUserModel
from user_app.utils import get_user_qs_project_based

def update_fabrication_progress(fablist_obj):
    from fablist_app.models import FabricationStatusModel, FabricationListModel
    
    if not isinstance(fablist_obj,FabricationListModel):
        raise Exception("Update fabrication progress: Object must be FabricationListModel")
    
    print("Updating fabrication progress ",fablist_obj)
    
    # return
    fab_user_status_qs = FabricationStatusModel.objects.filter(fabrication_item=fablist_obj)
    department_list = get_department_qs_common_method().values_list("name", flat=True)
    
    
    any_completed = fab_user_status_qs.filter(is_completed=True).exists()
    print("any_completed ",any_completed)
    
    for dept in department_list:
        # total_kg = 0
        filter_key = f"{dept}_status"
        print("filter_key ",filter_key)
        any_completed = fablist_obj.filter(**{filter_key: True}).exists()
        
    # find any object where is_completed is True in each department
    for fab_user_status_obj in fab_user_status_qs:
        print(fab_user_status_obj.id," fab_user_status_obj ",fab_user_status_obj.department," dept - is_completed ",fab_user_status_obj.is_completed)
        fab_user_dept_name = fab_user_status_obj.department.name
        if fab_user_status_obj.is_completed:
            setattr(fablist_obj, f"{fab_user_dept_name}_progress_percentage", 100)
            setattr(fablist_obj, f"{fab_user_dept_name}_completed_at", fab_user_status_obj.completed_at)
        else:
            setattr(fablist_obj, f"{fab_user_dept_name}_progress_percentage", 0)
            setattr(fablist_obj, f"{fab_user_dept_name}_completed_at", None)
    
    
    # update {dept}_progress_percentage to 100 if any of FabricationStatusModel user in a department is completed
    
    # Calc total progress ie by summing each department progress and dividing by total number of departments
    total_progress = 0
    for dept in department_list:
        total_progress += getattr(fablist_obj, f"{dept}_progress_percentage", 0)
        
    count = len(department_list)
    fablist_obj.total_progress = round(total_progress / count, 1)
    
    print("fablist_obj.total_progress ",fablist_obj.total_progress) # total_progress
    # clerk_progress_percentage
    # shop_progress_percentage
    # cut_progress_percentage
    # fab_progress_percentage
    # delivery_progress_percentage
    # received_progress_percentage
    # erect_progress_percentage
    
    # clerk_status
    # shop_status
    # cut_status
    # fab_status
    # delivery_status
    # received_status
    # erect_status
    
    # clerk_completed_at
    # shop_completed_at
    # cut_completed_at
    # fab_completed_at
    # delivery_completed_at
    # received_completed_at
    # erect_completed_at
    
    # # Saving Progress on FabricationListModel
    # obj.save()
    

def xupdate_fabrication_progress(obj):
    from fablist_app.models import FabricationStatusModel, FabricationListModel
    
    if not isinstance(obj,FabricationListModel):
        raise Exception("Update fabrication progress: Object must be FabricationListModel")
    
    print("Updating fabrication progress ",obj)
    fab_status_qs = FabricationStatusModel.objects.filter(fabrication_item=obj ,is_completed=True)
    fabrication_qty = obj.qty
    fabrication_kg = obj.kg
    # total_kg = fabrication_qty * fabrication_kg
    # print(f"fabrication_qty {fabrication_qty} fabrication_kg {fabrication_kg} total_kg {total_kg}")
    
    project_users_qs = ProjectUserModel.objects.filter(project=obj.project)
    # Count project users department-wise
    project_user_dict = {}
    for project_user in project_users_qs:
        print(project_user.user," project_user ",project_user.department," -dept")
        project_user_dept_name = project_user.department.name
        if project_user_dept_name in project_user_dict.keys():
            
            project_user_dict[project_user_dept_name] += 1
        else:
            project_user_dict[project_user_dept_name] = 1
            
    print("project_user_dict ",project_user_dict)
    
    
    # each user is from different dept, so need to calc department wise progress
    fabrication_department_progress = {}
    for fab_status_obj in fab_status_qs:
        print(fab_status_obj.id," fab_status_obj ",fab_status_obj.department," dept - is_completed ",fab_status_obj.is_completed)
        fab_user_dept_name = fab_status_obj.department.name
        if fab_user_dept_name in fabrication_department_progress.keys():
            fabrication_department_progress[fab_user_dept_name] += 1
        else:
            fabrication_department_progress[fab_user_dept_name] = 1
            
    print("fabrication_department_progress ",fabrication_department_progress)
    
    # print("project_user_dict ",project_user_dict)
    
    fabrication_dept_percentange_progress = {}
    for key in fabrication_department_progress.keys():
        if key in project_user_dict.keys():
            fabrication_dept_percentange_progress[key] = (fabrication_department_progress[key] / project_user_dict[key]) * 100 # percentage calc by department user avg
            # fabrication_dept_percentange_progress[key] = (fabrication_department_progress[key]) * 100 # Scope changed so, if any 1 from dept is completed then mark it as completed 100%
    
    print("fabrication_dept_percentange_progress ",fabrication_dept_percentange_progress)
    # print(obj.clerk_progress_percentage)
    
    #Update it on FabricationListModel
    total_progress = 0
    for key in project_user_dict.keys():
        setattr(obj, f"{key}_progress_percentage", round(fabrication_dept_percentange_progress.get(key, 0),2))
        total_progress += fabrication_dept_percentange_progress.get(key, 0)
        print("Key ",key," fab_prog ",fabrication_dept_percentange_progress.get(key, 0),type(fabrication_dept_percentange_progress.get(key, 0)))
        if fabrication_dept_percentange_progress.get(key, 0) == 100:
            print("||||||||||||||||| Fab Completed ",key)
            setattr(obj, f"{key}_status", True)
            setattr(obj, f"{key}_completed_at", obj.updated_at)
        else:
            print("||||||||||||||||| Fab Not Completed ",key)
            setattr(obj, f"{key}_status", False)
            setattr(obj, f"{key}_completed_at", None)
        
    total_progress = round(total_progress/7,1) # scope changed if any 1 is completed then mark it as completed
    # total_progress = round(total_progress/len(fabrication_department_progress),1)
    setattr(obj, "total_progress", total_progress)
    # setattr(obj, "total_kg", total_kg)
        # print("setattr ",f"{key}_progress_percentage", fabrication_dept_percentange_progress.get(key, 0))
    
    # Saving Progress on FabricationListModel
    obj.save()
        
def trigger_notification_on_first_fablist(project_obj):
    from fablist_app.models import FabricationListModel
    print("trigger_notification_on_first_fablist")
    first_fab_list = FabricationListModel.objects.filter(project=project_obj).count()
    print("first_fab_list ",first_fab_list)
    if first_fab_list == 0:
        # Create first fabrication list
        users_qs = get_user_qs_project_based(project_obj)
        print("users_qs", users_qs)
        if users_qs:
            title = "Fab List Created"
            content = f"Fablist has been uploaded for the project {project_obj.name}"
            print(users_qs, title , content)
            from notification_app.utils import send_notification_to_users
            send_notification_to_users(users_qs, title , content)
            
        else:
            print("No users found for project ",project_obj.name)
    
    return True
    