import flet as ft
from utils import States, DBManager
import random
import string

dbmanager = DBManager()
environments_grid = None
editing_env_name = False

############################################## Handlers ##############################################

def add_environment(e):
    random_name = "New_Environment" + ''.join(random.choices(string.digits, k=3))
    dbmanager.add_environment(States.current_project_id, random_name)
    States.current_project_environments = dbmanager.get_project_environments(States.current_project_id)
    cards_grid = populate_environments_grid()
    environments_grid.controls = cards_grid
    States.page.update()


def rename_environment(e: ft.ControlEvent):
    global editing_env_name
    editing_env_name = not editing_env_name

    env_id = e.control.data
    card_count = int(e.control.key.split("#")[0])
    card_index = int(e.control.key.split("#")[1])
    row_index = card_count // 2

    card_control: ft.Card = environments_grid.controls[row_index].controls[card_index]
    card_title: ft.ListTile = card_control.content.content.controls[0]
    card_title_field: ft.TextField = card_title.title

    # Make title field editable
    if editing_env_name:
        e.control.text = "Save"
        card_title_field.disabled = False
        card_title_field.border_width = 1
        card_title_field.bgcolor = "white"
        card_title_field.color = "black"
        card_title_field.focus = True
        card_title_field.autofocus = True
    else:
        e.control.text = "Rename"
        card_title_field.disabled = True
        card_title_field.border_width = 0
        card_title_field.bgcolor = "transparent"
        card_title_field.color = "black"
        card_title_field.focus = False
        card_title_field.autofocus = False

        # Save the new name
        new_env_name = card_title_field.value
        dbmanager.rename_environment(States.current_project_id, e.control.data, new_env_name)
        States.current_project_environments[env_id] = new_env_name
        # States.current_project_environments = dbmanager.get_project_environments(States.current_project_id)
        # cards_grid = populate_environments_grid()
        # environments_grid.controls = cards_grid
    
    States.page.update()


def delete_environment(e):
    env_id = e.control.data
    dbmanager.delete_environment(States.current_project_id, env_id)
    States.current_project_environments = dbmanager.get_project_environments(States.current_project_id)
    cards_grid = populate_environments_grid()
    environments_grid.controls = cards_grid
    States.page.update()



############################################## UI ##############################################


def populate_environments_grid():
    num_cards = 0
    card_index = 0
    cards_grid = [] # list of Rows

    cards_row = ft.Row(controls=[], wrap=True, spacing=80)
    for i, (env_id, env_name) in enumerate(States.current_project_environments.items()):
        card=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.ALBUM),
                                title=ft.TextField(key=env_id, value=env_name, disabled=True, border_width=0, color="black"),
                            ),
                            ft.Row(
                                [ft.TextButton("Rename" if not editing_env_name else "Save", 
                                               on_click=rename_environment,
                                               key= str(i) + "#" + str(card_index), # card_count#card_index
                                               data=env_id), 
                                 ft.TextButton("Delete",
                                               on_click=delete_environment,
                                               data=env_id),],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ]
                    ),
                    width=400,
                    padding=10,
                )
            )
        
        cards_row.controls.append(card)
        num_cards += 1
        card_index += 1

        if num_cards % 2 == 0:
            # Add the row to the grid
            cards_grid.append(cards_row)
            cards_row = ft.Row(controls=[], wrap=True, spacing=80)
            card_index = 0
        elif num_cards == len(States.current_project_environments):
            # Add the last row to the grid (in case the number of cards is odd)
            cards_grid.append(cards_row)
        
    return cards_grid
    


def init_environments_page():
    global dbmanager, environments_grid

    States.page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.ADD,
        on_click=add_environment,
        visible=False,
    )

    cards_grid = populate_environments_grid()

    environments_grid = ft.ListView(controls=cards_grid, auto_scroll=False)

    EnvironmentsPage = ft.Container(
        expand=True,
        content=environments_grid,
        alignment=ft.alignment.top_center,
        padding=ft.padding.only(left=160),
    )

    return EnvironmentsPage