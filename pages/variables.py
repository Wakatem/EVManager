import flet as ft
from utils import States, DBManager
import random
import string
import json

dbmanager = DBManager()
components_dropdown: ft.Dropdown = None
variables_list: ft.ListView = None
current_variable_text = None
variables_grid: ft.DataTable = None
variable_details_container: ft.Container = None
pick_files_dialog: ft.FilePicker = None

uploaded_files = {}
edit_mode = False


dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Model Dialog"),
        actions=[],
        actions_alignment=ft.MainAxisAlignment.END)

############################################## Utilities ##############################################

def set_current_variable_text_settings():
    global current_variable_text, edit_mode
    if edit_mode:
        current_variable_text.disabled = False
        current_variable_text.border_width = 1
        current_variable_text.bgcolor = "white"
        current_variable_text.color = "black"
    else:
        current_variable_text.disabled = True
        current_variable_text.border_width = 0
        current_variable_text.bgcolor = "transparent"
        current_variable_text.color = "black"
        current_variable_text.focus = False
        current_variable_text.autofocus = False

def populate_components_dropdown():
    global dbmanager
    current_project_components = dbmanager.get_project_components(States.current_project_id)

    States.components_dropdown_options.clear()
    for component_id, component_name in current_project_components:
        States.components_dropdown_options.append(ft.dropdown.Option(component_id, component_name))
    
    States.components_dropdown_options.append(ft.dropdown.Option(key="divider", content=ft.Divider(height=2), disabled=True))
    States.components_dropdown_options.append(ft.dropdown.Option(key="create", content=ft.Text("Create new component")))
    States.components_dropdown_options.append(ft.dropdown.Option(key="load", content=ft.Text("Load component from env file")))


def populate_variables_list(search_text=None):
    global dbmanager, variables_list

    variables_list.controls.clear()
    if States.current_component_id is not None:
        current_component_variables = dbmanager.get_component_variables(States.current_component_id, search_text)
        for var_id, var in current_component_variables.items():
            button = ft.TextButton(key=var_id, text=var["name"], width="100%", 
                              on_click=load_variable_details)
            
            if var_id == States.current_variable_id:
                button.style = ft.ButtonStyle(bgcolor=ft.colors.BLUE_GREY_100)
                variables_list.data = button
            else:
                button.style = ft.ButtonStyle(bgcolor='transparent')
            
            variables_list.controls.append(button)
                                                



def populate_variables_grid(env_values: dict):
    global dbmanager, variables_grid

    if States.current_project_environments is not None:
        variables_grid.rows.clear()
        for env_id, env_value in env_values.items():
            name = States.current_project_environments[env_id]
            value = env_value
            variables_grid.rows.append(
                ft.DataRow(
                    cells=[
                    ft.DataCell(content=ft.TextField(key=env_id, value=name, border_width=0, text_align=ft.TextAlign.CENTER, disabled=True, color="black")),
                    ft.DataCell(content=ft.TextField(key=env_id, value=value, border_width=0, text_align=ft.TextAlign.CENTER, disabled=True, color="black", on_focus=set_field_focus, on_blur=set_field_blur)),
                ]),
            )


def build_variable_details_container():
    global current_variable_text, variables_grid, variable_details_container, edit_mode

    new_content = None

    if States.current_component_id is None:
        new_content = ft.Text("No component is selected", size=30, color="grey", expand=True, text_align=ft.TextAlign.CENTER)
    elif States.current_variable_id is None:
        new_content = ft.Text("No variable is selected", size=30, color="grey", expand=True, text_align=ft.TextAlign.CENTER)
    elif len(States.current_project_environments) == 0:
        new_content = ft.Text("No environments found", size=30, color="grey", expand=True, text_align=ft.TextAlign.CENTER)
    else:
        new_content = ft.Column(
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(height=5),
                    current_variable_text,
                    ft.Container(height=5),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        width="100%",
                        controls=[
                            ft.OutlinedButton("Edit",
                                                width=90, height=22,
                                                on_click=toggle_edit_mode),
                            ft.OutlinedButton("Delete", 
                                            width=90, height=22,
                                            on_click=delete_variable),
                        ],
                    ),
                    ft.Container(height=10), # buffer
                    ft.ListView(expand=True, controls=[variables_grid]),
                ],
            )
        
    variable_details_container.content = new_content



def load_component_from_files(new_component_name):
    global uploaded_files, dbmanager

    new_component_id = dbmanager.load_component_from_files(States.current_project_id, new_component_name, uploaded_files)
    uploaded_files.clear()

    populate_components_dropdown()
    States.current_component_id = new_component_id
    components_dropdown.value = new_component_id

    populate_variables_list()
    
    dlg_modal.open = False
    States.page.update()

############################################## Handlers ##############################################

def dropdown_option_handler(e: ft.ControlEvent):
    global components_dropdown, dbmanager, dlg_modal, pick_files_dialog, edit_mode

    edit_mode = not edit_mode

    if e.data == "create":
        # Create new component
        random_name = "Component" + ''.join(random.choices(string.digits, k=3))
        new_component_id, new_component_name = dbmanager.add_component(States.current_project_id, random_name)

        States.current_component_id = new_component_id
        States.current_variable_id = None
        populate_components_dropdown()
        build_variable_details_container()

        components_dropdown.value = new_component_id
        variables_list.controls.clear()

        States.page.update()
        

    elif e.data == "load":

        def close_modal(e: ft.ControlEvent):
            dlg_modal.open = False
            States.page.update()

        # Create load_variables row for every environment
        def create_load_variables_row(env_id, env_name):
            def open_picker(e):
                # Check if the file is already uploaded
                if env_id not in uploaded_files:
                    pick_files_dialog.data = {
                        "env_id": env_id,
                        "button": e.control
                    }
                    pick_files_dialog.pick_files()
                else:
                    # Remove the file
                    uploaded_files.pop(env_id)
                    e.control.text = "Select File"
                    States.page.update()

            return ft.Row(
                controls=[
                    ft.Text(env_name, expand=1),
                    ft.ElevatedButton("Select File", on_click=open_picker)
                    if env_id not in uploaded_files else ft.Text("File Uploaded", expand=1),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        
        load_vars_rows = []
        for env_id, env_name in States.current_project_environments.items():
            load_vars_rows.append(create_load_variables_row(env_id, env_name))

        dlg_modal.title = ft.Text("Load Component")
        dlg_modal.content = ft.Column(
            width=400,
            controls=[
                ft.TextField(label="Name", value="", width="100%"),
                ft.Divider(height=2),
                ft.Text("Environments", size=20, color="black"),
                ft.Container(height=1),
                ft.ListView(controls=load_vars_rows, auto_scroll=False, spacing=35),
                ft.Text("If uploaded files have mismatched variables, empty values will be added automatically", size=12, color="grey")
            ]
        )
        dlg_modal.actions.clear()
        dlg_modal.actions = [
            ft.TextButton("Load", on_click=lambda e: load_component_from_files(dlg_modal.content.controls[0].value)),
            ft.TextButton("Cancel", on_click=close_modal)
            ]
        
        dlg_modal.open = True
        States.page.update()

    else:
        States.current_component_id = e.data
        populate_variables_list()
        States.current_variable_id = None
        build_variable_details_container()        
        States.page.update()


def export_component(e: ft.ControlEvent):
    global dbmanager

    export_path = dbmanager.export_component(States.current_project_id, States.current_component_id)

    States.page.snack_bar = ft.SnackBar(ft.Text(f"Successfully exported env files to {export_path}"), bgcolor=ft.colors.GREEN_700, duration=10000)
    States.page.snack_bar.open = True
    States.page.update()

def rename_component(e: ft.ControlEvent):
    global dlg_modal

    def on_modal_submit(e: ft.ControlEvent):
        new_name = e.control.parent.content.value
        dbmanager.rename_component(States.current_component_id, new_name)
        
        populate_components_dropdown()
        dlg_modal.open = False
        States.page.update()
    
    def close_modal(e: ft.ControlEvent):
        dlg_modal.open = False
        States.page.update()


    component_name = dbmanager.get_component_name(States.current_component_id)

    dlg_modal.title = ft.Text("Rename Component")
    dlg_modal.content = ft.TextField(label="Name", value=component_name, expand=True, on_submit=lambda e: on_modal_submit)
    dlg_modal.actions.clear()
    dlg_modal.actions = [
        ft.TextButton("Update", on_click=on_modal_submit),
        ft.TextButton("Cancel", on_click=close_modal)]
    
    dlg_modal.open = True
    States.page.update()



def delete_component(e: ft.ControlEvent):
    dbmanager.delete_component(States.current_project_id, States.current_component_id)
    States.current_component_id = dbmanager.get_default_component(States.current_project_id)
    components_dropdown.value = States.current_component_id
    States.current_variable_id = None
    populate_components_dropdown()
    populate_variables_list()
    build_variable_details_container()
    States.page.update()


def add_variable(e: ft.ControlEvent):
    global variables_grid, variables_list
    random_name = "New_Variable" + ''.join(random.choices(string.digits, k=3))
    var_id = dbmanager.add_variable(States.current_project_id, States.current_component_id, random_name)

    if var_id:
        variables_list.controls.append(
            ft.TextButton(key=var_id, text=random_name, width="100%", 
                          on_click=load_variable_details,
                          style=ft.ButtonStyle(bgcolor='transparent')))
    
    States.page.update()


def search_variables(e: ft.ControlEvent):
    search_text = e.data
    populate_variables_list(search_text)
    States.page.update()


def load_variable_details(e: ft.ControlEvent):
    global dbmanager, current_variable_text, variables_grid, variable_details_container
    
    var_id = e.control.key

    if var_id != States.current_variable_id:
        # Unhighlight the previously selected variable
        if e.control.parent.data:
            e.control.parent.data.style.bgcolor = "transparent"
        
        # Highlight the selected variable
        States.current_variable_id = var_id
        e.control.style.bgcolor = ft.colors.BLUE_GREY_100
        
        # Update the current variable text
        var = dbmanager.load_variable_details(States.current_component_id, var_id)
        env_values = var["env_values"]
        current_variable_text.value = var["name"]

        # Load environment values for each variable
        populate_variables_grid(env_values)
        build_variable_details_container()
        
        e.control.parent.data = e.control
        
        States.page.update()


def delete_variable(e: ft.ControlEvent):
    global dbmanager
    dbmanager.delete_variable(States.current_component_id, States.current_variable_id)
    States.current_variable_id = None
    populate_variables_list()
    build_variable_details_container()
    States.page.update()
    
def toggle_edit_mode(e: ft.Control):
    global edit_mode
    edit_mode = not edit_mode
    if edit_mode:
        e.control.text = "Save"

        set_current_variable_text_settings()
        for row in variables_grid.rows:
            row.cells[1].content.disabled = False
            row.cells[1].content.bgcolor = "white"
    else:

        # Save the new values and name
        new_name = current_variable_text.value
        if new_name == "":
            States.page.snack_bar = ft.SnackBar(ft.Text("Variable name cannot be empty"), bgcolor=ft.colors.YELLOW_800, duration=4000)
            States.page.snack_bar.open = True
            States.page.update()
            return
        
        # Disable edit mode
        e.control.text = "Edit"

        set_current_variable_text_settings()
        for row in variables_grid.rows:
            row.cells[1].content.disabled = True
            row.cells[1].content.bgcolor = "transparent"

        
        new_env_values = {}

        for row in variables_grid.rows:
            env_id = row.cells[1].content.key
            new_value = row.cells[1].content.value
            if new_value == "":
                new_value = "<EMPTY>"
            new_env_values[env_id] = new_value
        
        dbmanager.save_variable_details(States.current_component_id, States.current_variable_id, new_name, new_env_values)
        populate_variables_list()
        populate_variables_grid(new_env_values)

    States.page.update()


def cache_file(file: ft.FilePickerResultEvent):
    global uploaded_files

    data = json.loads(file.data)
    file_path = data["files"][0]["path"]

    uploaded_files.update({file.control.data["env_id"]: file_path})
    file.control.data["button"].text = "Remove"
    States.page.update()

def set_field_focus(e: ft.ControlEvent):
    e.control.focus= True
    e.control.autofocus = True
    States.page.update()

def set_field_blur(e: ft.ControlEvent):
    e.control.focus= False
    e.control.autofocus = False
    States.page.update()


############################################## UI ##############################################


def init_variables_page():
    global dbmanager, variables_grid, components_dropdown, dlg_modal, variables_list, current_variable_text, variable_details_container, pick_files_dialog
    pick_files_dialog = ft.FilePicker(on_result=cache_file)
    States.page.overlay.append(pick_files_dialog)
    States.page.overlay.append(dlg_modal)

    current_variable_text = ft.TextField(key="a", value="", border_width=0,
                                            text_align=ft.TextAlign.CENTER, disabled=True,
                                            color="black", text_size=30,
                                            on_focus=set_field_focus, on_blur=set_field_blur)

    if States.current_component_id is None:
        States.components_dropdown_options = [
            ft.dropdown.Option(key="empty_message", content=ft.Text("No components found", color="grey", disabled=True)),
            ft.dropdown.Option(key="divider", content=ft.Divider(height=2), disabled=True),
            ft.dropdown.Option(key="create", content=ft.Text("Create new component")),
            ft.dropdown.Option(key="load", content=ft.Text("Load component from env file")),
        ]


    # Create and populate components dropdown
    components_dropdown = ft.Dropdown(
        label="Component",
        hint_text="Select Component",
        options=States.components_dropdown_options,
        autofocus=False,
        value=States.current_component_id,
        expand=7,
        on_change=dropdown_option_handler)
    populate_components_dropdown()
    

    # Create and populate variables list with values
    variables_list = ft.ListView(auto_scroll=False, expand=5, controls=[])
    populate_variables_list()


    # Create variable details table
    variables_grid = ft.DataTable(
        expand=True,
        horizontal_lines=ft.border.BorderSide(1, "black"),
        vertical_lines=ft.border.BorderSide(1, "black"),
        columns=[
            ft.DataColumn(label=ft.Text("Environment", width=400, text_align=ft.TextAlign.CENTER)),
            ft.DataColumn(label=ft.Text("Value", width=400, text_align=ft.TextAlign.CENTER))],
        heading_text_style=ft.TextStyle(size=20, color="black", weight=ft.FontWeight.BOLD))



    variable_details_container= ft.Container(
            border=ft.border.all(1.5, "black"),
            border_radius=ft.border_radius.all(5),
            alignment=ft.alignment.center,
            expand=3)
    build_variable_details_container()


    VariablesPage = ft.Container(
        expand=True,
        content=ft.Column(
                    controls=[
        ft.Container(
            border=ft.border.all(color="black", width=1.5),
            border_radius=ft.border_radius.all(5),
            content=ft.Row( ## Components Row
                    controls=[components_dropdown,
                        ft.Container(width=20),
                        ft.OutlinedButton("Export", expand=2, on_click=export_component),
                        ft.OutlinedButton("Rename", expand=2, on_click=rename_component),
                        ft.OutlinedButton("Delete", expand=2, on_click=delete_component),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.padding.all(10),
            ),

        ft.Container(
            expand=True,
            content=ft.Row( ## Variables Row
                    controls=[
                            ft.Container(
                                    border=ft.border.all(1.5, "black"),
                                    border_radius=ft.border_radius.all(5),
                                    expand=1,
                                    content=ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.START,
                                        controls=[
                                            ft.Container(height=1),
                                            ft.Row(
                                                controls=[
                                                    ft.Container(expand=5,
                                                                 alignment=ft.alignment.center,
                                                                 padding=ft.padding.only(left=10),
                                                                 content=ft.TextField(hint_text="Search variables", text_align=ft.TextAlign.CENTER, on_change=search_variables, height=40, width=250, text_size=12)),
                                                    ft.Container(
                                                                 alignment=ft.alignment.center,
                                                                 padding=ft.padding.only(right=10),
                                                                 content=ft.IconButton(ft.icons.ADD_ROUNDED, on_click=add_variable, expand=True)),
                                                    ]),
                                            ft.Container(content=ft.Divider(height=2)),
                                            variables_list,
                                                ]),
                                    ),
                            variable_details_container
                    ],
                ),
                
            ),
    ])
    )

    return VariablesPage