import flet as ft
from pages import init_variables_page, init_environments_page
from utils import States, DBManager


def main(page: ft.Page):
    States.page = page
    States.page.window.center()
    States.page.window.resizable = False

    dbmanager = DBManager()
    States.current_project_id = dbmanager.get_default_project()
    if States.current_project_id is None:
        States.current_project_id = dbmanager.create_new_project("Default")

    States.current_component_id = dbmanager.get_default_component(States.current_project_id)
    States.current_project_environments = dbmanager.get_project_environments(States.current_project_id)
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def handle_dismissal(e):
        pass

    def handle_change(e: ft.ControlEvent):
        nonlocal page_content, VariablesPage, EnvironmentPage
        if int(e.data) == 0:
            drawer.selected_index = States.selected_tab
        else:
            States.selected_tab = int(e.data)
            if States.selected_tab == 1:
                States.page.floating_action_button.visible = False
                States.page.remove(page_content)
                page_content = VariablesPage
                States.page.add(page_content)
            
            elif States.selected_tab == 2:
                States.page.floating_action_button.visible = True
                States.page.remove(page_content)
                page_content = EnvironmentPage
                States.page.add(page_content)

        page.update()
        page.close(drawer)

    drawer = ft.NavigationDrawer(
        on_dismiss=handle_dismissal,
        on_change=handle_change,
        selected_index=States.selected_tab,
        controls=[
            ft.Container(height=12),
            ft.NavigationDrawerDestination(
                label=dbmanager.get_project_name(States.current_project_id),
                icon=ft.icons.DOOR_BACK_DOOR_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.DOOR_BACK_DOOR),
            ),
            ft.Divider(thickness=2),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.PASSWORD_OUTLINED),
                label="Variables",
                selected_icon=ft.icons.PASSWORD,
            ),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.LAYERS_OUTLINED),
                label="Environments",
                selected_icon=ft.icons.LAYERS,
            ),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.SETTINGS_OUTLINED),
                label="Project Settings",
                selected_icon=ft.icons.SETTINGS,
            ),
            ft.Divider(thickness=2),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.LOGOUT_OUTLINED, scale=ft.transform.Scale(scale_x=-1, scale_y=1)),
                label="Close",
                selected_icon=ft.icons.LOGOUT, 
            ),
        ],
    )

    page.add(ft.Row(
        height=56,
        controls=[
            ft.IconButton(ft.icons.MENU, expand=1, on_click=lambda e: page.open(drawer), offset=ft.Offset(0.1, 0)),
            ft.Container(content=ft.ElevatedButton(dbmanager.get_project_name(States.current_project_id), disabled=True, width=100), expand=18),
            ft.Tooltip(ft.IconButton(ft.icons.INFO, on_click=lambda e: None), message="Project Info"),

        ]
    ))
    
    VariablesPage = init_variables_page()
    EnvironmentPage = init_environments_page()
    
    page_content = VariablesPage
    States.page.add(page_content)

if __name__ == "__main__":
    ft.app(target=main)