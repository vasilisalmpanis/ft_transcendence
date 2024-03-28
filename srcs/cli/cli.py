from multiprocessing.connection import Client
from client                     import NetworkClient, Response
from typing                     import Tuple
import game                     as pong
import user
import curses
import utils
import time
class Menu:
    def __init__(self, stdscr, options):
        self.stdscr = stdscr
        self.options = options
        self.selected_option = 0

    def display(self):
        self.stdscr.clear()
        for i, option in enumerate(self.options):
            if i == self.selected_option:
                self.stdscr.addstr(i + 1, 1, f"> {option['label']}", curses.A_REVERSE)
            else:
                self.stdscr.addstr(i + 1, 1, f"  {option['label']}")
        self.stdscr.refresh()

    def navigate(self, key):
        if key == curses.KEY_UP and self.selected_option > 0:
            self.selected_option -= 1
        elif key == curses.KEY_DOWN and self.selected_option < len(self.options) - 1:
            self.selected_option += 1
        else:
            self.stdscr.clear()
            self.stdscr.addstr(4, 1, "Invalid input. Press any key to try again.")
            

    def execute_selected_action(self, stdscr, **kwargs):
        selected_action = self.options[self.selected_option]['action']
        selected_action(stdscr, **kwargs)
        return True

def main_menu(stdscr):
    status = utils.Singleton()
    curses.curs_set(0)
    try:
        while True:
            menu_options = [{"label": "Login", "action": authenticate},
                        {"label": "Create Account", "action": user.create_account},
                        {"label": "Exit", "action": user.exit}
                        ]
            menu = Menu(stdscr, menu_options)
            while not status.state:
                menu.display()
                key = stdscr.getch()
                if key == ord('\n'):
                    try:
                        menu.execute_selected_action(stdscr)
                    except Exception as e:
                        if str(e) == "Exit":
                            return
                        stdscr.clear()
                        stdscr.addstr(1, 1, str(e))
                        stdscr.refresh()
                        stdscr.getch()
                elif key in [curses.KEY_UP, curses.KEY_DOWN]:
                    menu.navigate(key)
                elif key == ord('q'):
                    break
            menu_options = [
                {"label": "Play Game", "action": play_game},
                # {"label": "Search for Users", "action": search_users},
                # {"label": "Manage Friends", "action": manage_friends},
                {"label": "Account Settings", "action": account_settings},
                {"label": "Logout", "action": logout}
            ]
            menu = Menu(stdscr, menu_options)
            while status.state == True:
                menu.display()
                key = stdscr.getch()
                if key == ord('\n'):
                    menu.execute_selected_action(stdscr)
                elif key in [curses.KEY_UP, curses.KEY_DOWN]:
                    menu.navigate(key)
                elif key == 27:
                    logout(stdscr)
                    break
    except Exception as e:
        return

def verify_2fa(stdscr) -> None:
    client = NetworkClient()
    status = utils.Singleton()
    stdscr.clear()
    code = utils.get_input(stdscr, "Enter your 2FA code: ")
    response = client.verify_2fa(code)
    if response.status != 200:
        stdscr.addstr(1, 1, "Invalid 2FA code. Press any key to try again.")
        stdscr.refresh()
        stdscr.getch()
        return
    status.state = utils.AUTHORIZED

def authenticate(stdscr) -> None:
    client = NetworkClient()
    status = utils.Singleton()
    while not status.state:
        stdscr.clear()
        stdscr.nodelay(0)
        username = utils.get_input(stdscr, "Enter your username: ")
        password = utils.get_input(stdscr, "Enter your password: ", password=True)
        response = client.authenticate(username, password)
        response = client.request("/users/me", "GET")
        status.state = response.status == 200
        if status.state != utils.AUTHORIZED:
            stdscr.clear()
            if response.status == 401:
                if response.body == {"Error" : "2FA Required"}:
                    while not status.state:
                        verify_2fa(stdscr)
                else:
                    stdscr.addstr(1, 1, "Invalid credentials. Press any key to try again.")
            else:
                stdscr.addstr(1, 1, f"{response.text}")
                stdscr.getch()
            stdscr.refresh()
        else:
            return

def start_game(stdcsr, game_id):
    game = pong.Game(stdcsr, game_id)
    game.run()
    stdcsr.nodelay(0)

def play_game(stdcsr):
    client = NetworkClient()
    response = client.request("/games?type=pending", "GET")
    if response.status != 200:
        stdcsr.clear()
        stdcsr.addstr(1, 1, "An error occurred. Return to the main menu")
        stdcsr.refresh()
        stdcsr.getch()
        return
    games = response.body
    if len(games) == 0:
        response = client.request("/games?type=paused&me=True", "GET")
        games = response.body
        if len(games) == 0:
            stdcsr.clear()
            stdcsr.addstr(1, 1, "No games available. Return to the main menu")
            stdcsr.refresh()
            stdcsr.getch()
            return
    game_ids = [game['id'] for game in games]
    menu_options = [{"label": f"Game {game_id}", "action": start_game} for game_id in game_ids]
    menu = Menu(stdcsr, menu_options)
    while True:
        menu.display()
        key = stdcsr.getch()
        if key == ord('\n'):
            menu.execute_selected_action(stdcsr, game_id=game_ids[menu.selected_option])
            break
        elif key in [curses.KEY_UP, curses.KEY_DOWN]:
            menu.navigate(key)
        elif key == ord('q'):
            break

def user_running_games(stdcsr, response):
    if response.status != 200:
        stdcsr.clear()
        stdcsr.addstr(1, 1, "An error occurred. Return to the main menu")
        stdcsr.refresh()
        stdcsr.getch()
        return
    game = response.body.get('game_id', None)
    return game



# def search_users():
#     print("Search for Users")
    
# import json
# def manage_friends(stdcsr, client):
#     response = client.request("/friends", "GET")
#     if response.status != 200:
#         stdcsr.clear()
#         stdcsr.addstr(1, 1, "An error occurred. Return to the main menu")
#         stdcsr.refresh()
#         stdcsr.getch()
#         return
#     friends = response.body
#     if 'status' in friends:
#         stdcsr.clear()
#         stdcsr.addstr(1, 1, "You have no friends. Return to the main menu")
#         stdcsr.refresh()
#         stdcsr.getch()
#         return
#     else:
#         # user = { User(friend) for friend in friends}
#         stdcsr.clear()
#         # stdcsr.addstr(1, 1, json.dumps(user))
#         stdcsr.refresh()
#         stdcsr.getch()
#         return
 
def account_settings(stdscr):
    status = utils.Singleton()
    menu_options = [
        {"label": "Change Username", "action": user.change_username},
        {"label": "Change Password", "action": user.change_password},
        {"label": "Change Email", "action": user.change_email},
        {"label": "Delete Account", "action": user.delete_account}
    ]
    menu = Menu(stdscr, menu_options)
    while status.state == utils.AUTHORIZED:
        menu.display()
        key = stdscr.getch()
        if key == ord('\n'):
            menu.execute_selected_action(stdscr)
        elif key == 27:
            break
        elif key in [curses.KEY_UP, curses.KEY_DOWN]:
            menu.navigate(key)

def logout(stdscr):
    try:
        client = NetworkClient()
        status = utils.Singleton()
        status.unauthorize()
        client.logout()
    except Exception as e:
        stdscr.clear()
        stdscr.addstr(1, 1, str(e))
        stdscr.refresh()
        stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main_menu)

