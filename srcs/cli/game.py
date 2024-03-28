import client
from websockets.sync.client import connect
import asyncio
import curses
import json

class Game:
    def __init__(self, stdsrc, game_id: int) -> None:
        self.client = client.NetworkClient()
        self.game_id: int = game_id
        self.stdscr = stdsrc
        self.stdscr.clear()
        self.ball_x: int = 50
        self.ball_y: int = 50
        self.left_paddle_y: int = 40
        self.right_paddle_y: int = 40
        self.left_paddle_x: int = 2
        self.side = "left"
        self.score_x: int = 0
        self.score_y: int = 0
        self.update_dimensions()
        self.stdscr.addstr(1, self.sw // 2 - 18, "Game Starting As Soon As Possible...")
        self.stdscr.refresh()
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.key = None
        try:
            self.ws = connect("ws://c2s15d84.42wolfsburg.de:8000/ws", subprotocols=["Authorization", self.client.access_token])
            self.ws.send(json.dumps({"join": self.game_id}))
            # self.waiting_room()
        except Exception as e:
            self.stdscr.clear()
            self.stdscr.addstr(1, 1, str(e))
            self.stdscr.refresh()
            self.stdscr.getch()
            self.ws.close()
            self.running = False
            return
        self.running = True

    def waiting_room(self):
        global  cl
        while True:
            self.update_dimensions()
            self.stdscr.addstr(1, self.sw // 2 - 18, "Game Starting As Soon As Possible...")
            self.stdscr.refresh()
            try:
                data = self.ws.messages.get_nowait()
                if 'side' in data:
                    self.side = data['side']
                    break
            except asyncio.queues.QueueEmpty:
                pass
            self.key = self.stdscr.getch()
            if self.key == ord('q'):
                self.ws.close()
                self.client.request("DELETE", "/games", body={"game_id" : self.game_id})
                self.running = False
                raise Exception("Game Closed")

    def update_dimensions(self):
        self.sh = self.stdscr.getmaxyx()[0]
        self.sw = self.stdscr.getmaxyx()[1]
        self.paddle_height = self.sh // 5
        self.right_paddle_x = self.sw - 3


    def run(self):
        while self.running:
            self.update()
            self.render()

    def update(self, ):
        data = json.loads(self.ws.recv())
        if 'status' in data:
            if data['status'] == 'paused':
                return
            self.ws.close()
            self.running = False
            return
        if 'side' in data:
            self.side = data['side']
            return
        if 'error' in data or 'Problem' in data:
            self.running = False
            return
        if 'x' in data:
            self.ball_x = data['x']
            self.ball_y = data['y']
        if 'p1' in data:
            self.left_paddle_y = data['p1']
        if 'p2' in data:
            self.right_paddle_y = data['p2']
        if 's1' in data:
            self.score_x = data['s1']
            self.score_y = data['s2']
        self.key = self.stdscr.getch()
        if self.key == curses.KEY_UP:
            self.ws.send(json.dumps({"message": "up"}))
        elif self.key == curses.KEY_DOWN:
            self.ws.send(json.dumps({"message": "down"}))
        elif self.key == ord('q'):
            self.ws.close()
            self.running = False
        

    def render(self):
        self.stdscr.clear()
        self.update_dimensions()
        for i in range(self.paddle_height):
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
            self.stdscr.attron(curses.color_pair(1))
            self.stdscr.addch(int((self.sh + 1) / 100 * self.left_paddle_y) + i, self.left_paddle_x, '▍')
            self.stdscr.addch(int((self.sh + 1)/ 100 * self.right_paddle_y) + i, self.right_paddle_x, '▍')
            self.stdscr.attroff(curses.color_pair(1))
        self.stdscr.addch(int((self.sh - 1) / 100 * self.ball_y), int((self.ball_x / 100 ) * self.sw), '◯')
        self.stdscr.addstr(1, self.sw // 2, f"{self.score_x} - {self.score_y}")

        self.stdscr.refresh()