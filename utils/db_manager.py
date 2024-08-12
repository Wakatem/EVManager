from tinydb import TinyDB, Query
from tinydb.table import Document
from datetime import datetime
import random
import string
import os
import flet as ft
from .states import States

def generate_id(prefix=None, length=6):
    if prefix:
        return prefix + "#" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class DBManager:

    # Create singleton instance of the class
    _instance = None
    init_done = False

    def __new__(cls, db_path="db.json", *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, db_path="db.json"):
        if not self.init_done:
            self.db_path = db_path
            self.db = TinyDB(db_path)
            self.projects = self.db.table("projects")
            self.components = self.db.table("components")
            self.init_done = True
    
    def create_new_project(self, project_name):
        project_id = generate_id(length=4)
        doucment_id = self.projects.insert({
            "project_id": project_id,
            "name": project_name, 
            "components": [], 
            "environments": {},
            "date_created": datetime.now().isoformat(),
            "date_updated": datetime.now().isoformat()})
        return project_id
    
    def get_default_project(self):
        projects = self.projects.all()
        if len(projects) == 0:
            return None
        return projects[0]["project_id"]
    
    def get_project_name(self, project_id):
        project = Query()
        project = self.projects.get(project.project_id == project_id)
        return project["name"]
    
    def add_environment(self, project_id, env_name):
        project = Query()

        # Add new environment to the project
        id = generate_id("env", length=4)
        self.projects.update(lambda doc: doc['environments'].update({id: env_name}),
            project.project_id == project_id)
        

        def append_env_to_vars(doc):
            variables = doc["variables"]
            for var_name in variables:
                var = variables[var_name]
                var["env_values"].update({id: "<EMPTY>"})
            return doc
        
        # Add the environment to all the components
        component_query = Query()
        components = self.components.search(project.project_id == project_id)
        for component in components:
            component_id = component["component_id"]
            self.components.update(append_env_to_vars, 
                component_query.component_id == component_id)

    
    def add_component(self, project_id, component_name):
        project = Query()
        component_id = generate_id()

        # Create new component document
        self.components.insert({
            "component_id": component_id,
            "project_id": project_id,
            "name": component_name,
            "variables": {},
        })

        # Add the component to the project
        self.projects.update(lambda doc: doc['components'].append(component_id),
                             project.project_id == project_id)
        return (component_id, component_name)
    

    def add_variable(self, project_id, component_id, variable_name, env_values=None):
        project = Query()
        component = Query()
        var_id = generate_id("var", 8)

        # Get all environments in the project
        project = self.projects.get(project.project_id == project_id)
        environments = project["environments"]

        # Add the variable to all the environments in the component
        if env_values is None:
            env_values = {}
            for env_id, env_name in environments.items():
                env_values[env_id] = "<EMPTY>"

        changes = self.components.update(lambda doc: doc['variables'].update(
            {var_id: {
                "name": variable_name,
                "env_values": env_values
            }}), 
            component.component_id == component_id)
        
        if len(changes) > 0:
            return var_id
        else:
            return None
    
    
    def get_project_environments(self, project_id):
        project = Query()
        project = self.projects.get(project.project_id == project_id)
        return project["environments"]
    

    def get_project_components(self, project_id):
        project = Query()
        components = self.components.search(project.project_id == project_id)

        # Extract names only
        ids_and_names = []
        for component in components:
            ids_and_names.append((component["component_id"], component["name"]))
        
        return ids_and_names


    
    def get_default_component(self, project_id):
        project = Query()
        project = self.projects.get(project.project_id == project_id)
        if len(project["components"]) == 0:
            return None
        return project["components"][0]
    

    def get_component_name(self, component_id):
        component = Query()
        component = self.components.get(component.component_id == component_id)
        return component["name"]
    
    def get_component_variables(self, component_id, search_text=None):
        component = Query()
        component = self.components.get(component.component_id == component_id)
        
        # Get variables that contain the search text (even if it is a substring)
        if search_text:
            variables = component["variables"]
            filtered_vars = {}
            for var_id in variables:
                var = variables[var_id]
                if search_text in var["name"]:
                    filtered_vars[var_id] = var
            return filtered_vars
        
        # Return all variables
        return component["variables"]
    

    def rename_component(self, component_id, new_name):
        component = Query()
        self.components.update(lambda doc: doc.update({"name": new_name}),
            component.component_id == component_id)
    

    def load_component_from_files(self, project_id, component_name, files: dict):
        project = Query()
        component = Query()
        component_id = generate_id()
        self.components.insert({
            "component_id": component_id,
            "project_id": project_id,
            "name": component_name,
            "variables": {},
        })

        self.projects.update(lambda doc: doc['components'].append(component_id),
                             project.project_id == project_id)

        # Group extracted variables by name, and link with every environment
        invalid_lines = []
        all_vars = {}
        for env_id, file_path in files.items():
            with open(file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            var_name, var_value = map(str.strip, line.split("=", 1))
                        except Exception as e:
                            print(f"Error reading line: {line}")
                            invalid_lines.append(line)
                        if var_name not in all_vars:
                            all_vars[var_name] = {}
                        all_vars[var_name][env_id] = var_value 
        
        if len(invalid_lines) > 0:
            # Concatenate all invalid lines
            error_message = "\n".join(invalid_lines)
            error_message = f"Could not extract variables from the following lines:\n{error_message}"
            States.page.snack_bar = ft.SnackBar(ft.Text(error_message), bgcolor=ft.colors.RED_700, duration=7000)
            States.page.snack_bar.open = True
            States.page.update()

        project_environments = self.get_project_environments(project_id)
        for var_name, env_values in all_vars.items():
            # Assign values to var-env pairs that are missing
            for env_id in project_environments:
                if env_id not in env_values:
                    env_values[env_id] = "<EMPTY>"

            self.add_variable(project_id, component_id, var_name, env_values) 
        
        return component_id

    def rename_environment(self, project_id, env_id, new_name):
        project = Query()
        self.projects.update(lambda doc: doc['environments'].update({env_id: new_name}),
            project.project_id == project_id)
            
    
    def delete_environment(self, project_id, env_id):
        project = Query()
        self.projects.update(lambda doc: doc['environments'].pop(env_id),
            project.project_id == project_id)
        

        def pop_env_entries(doc):
            variables = doc["variables"]
            for var_name in variables:
                var = variables[var_name]
                var["env_values"].pop(env_id)
            return doc
        
        # Delete the environment from all the components
        component_query = Query()
        components = self.components.search(component_query.project_id == project_id)
        for component in components:
            self.components.update(pop_env_entries,
                component_query.component_id == component["component_id"])
    

    def load_variable_details(self, component_id, var_id):
        component = Query()
        component = self.components.get(component.component_id == component_id)
        return component["variables"][var_id]
    
    def delete_component(self, project_id, component_id):
        project = Query()
        component = Query()

        def remove_component_id(doc):
            doc["components"].remove(component_id)
            return doc
        
        self.projects.update(remove_component_id,
            project.project_id == project_id)
        self.components.remove(component.component_id == component_id)
    

    def delete_variable(self, component_id, var_id):
        component = Query()

        def remove_var(doc):
            doc["variables"].pop(var_id)
            return doc
        
        self.components.update(remove_var,
            component.component_id == component_id)
    
    def save_variable_details(self, component_id, var_id, new_name, new_env_values):
        component = Query()

        def update_var_name(doc):
            variable = doc["variables"][var_id]
            variable["name"] = new_name
            variable["env_values"] = new_env_values

            doc["variables"][var_id] = variable
            return doc
        
        self.components.update(update_var_name,
            component.component_id == component_id)
    
    def export_component(self, project_id, component_id):

        component = Query()
        component = self.components.get(component.component_id == component_id)
        
        # Set path to User Documents folder
        export_path = os.path.expanduser("~/Documents") + "/EVManager"
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        # Create a file for each environment
        project_environments = self.get_project_environments(project_id)

        for env_id, env_name in project_environments.items():
            file_name = f"{component['name']}_{env_name}.env"
            full_file_path = os.path.join(export_path, file_name)
            
            with open(full_file_path, "w") as file:
                for var_id, var in component["variables"].items():
                    file.write(f"{var['name']}={var['env_values'][env_id]}\n")
        
        return export_path


manager = DBManager()
# manager.create_new_project("default")
# manager.add_component("9ASW", "API")
# manager.add_environment("9ASW", "Dev")
# manager.add_variable("9ASW", "QK1ZFT", "ABCD")