import flet as ft

class States():
    # Create singleton instance of the class
    _instance = None
    init_done = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(States, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if not self.init_done:
            self.init_done = True
    
    # State variables
    selected_tab = 1
    page: ft.Page = None
    current_project_id = None
    current_component_id = None
    current_variable_id = None
    current_project_environments = {}
    components_dropdown_options = []
