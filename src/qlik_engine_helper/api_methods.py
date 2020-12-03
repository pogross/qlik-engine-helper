from enum import Enum


class ApiMethods(Enum):
    create_app = "CreateApp"
    create_app_and_open = "CreateDocEx"
    get_app_list = "GetDocList"
    open_app = "OpenDoc"
    save_app_changes = "DoSave"
    delete_app = "DeleteApp"
    get_script = "GetScript"
    set_script = "SetScript"
