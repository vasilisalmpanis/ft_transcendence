from math import log
from re import U
from channels.generic.websocket						import AsyncWebsocketConsumer, AsyncConsumer
from channels.db									import database_sync_to_async
from typing                                         import Dict, Any
from users.models                                   import user_model_to_dict
from pong.consumers                                 import SingletonMeta
from pong.models                                    import Pong, pong_model_to_dict
from users.models                                   import User
from .models                                        import Tournament
import asyncio
import json
import random
from asgiref.sync import sync_to_async


def create_game(user1, user2, tournament: Tournament):
    game = tournament.games.create(player1=user1, player2=user2)
    return game

def get_games_as_dict(tournament: Tournament):
    games = []
    for game in tournament.games.all():
        games.append(pong_model_to_dict(game))
    return games

def finish_tournament(tournamement_id: int, winner: User):
    tournament = Tournament.objects.get(id=tournamement_id)
    tournament.winner = winner
    tournament.status = 'closed'
    tournament.save()

def get_winner(game: Pong):
    if game.score1 > game.score2:
        return game.player1
    return game.player2

def update_status(tournament_id: int, status: str):
    tournament = Tournament.objects.get(id=tournament_id)
    tournament.status = status
    tournament.save()

def get_winners(games):
    winners = []
    ids = [game.id for game in games]
    games = Pong.objects.filter(id__in=ids).all()
    for game in games:
        # game.refresh_from_db()
        if game.status != 'finished':
            return None
        if game.score1 > game.score2:
            winners.append(game.player1)
        else:
            winners.append(game.player2)
    logger.warn(winners)
    return winners
class TournamentGroupManager(metaclass=SingletonMeta):
    _groups: Dict[str, Dict[Any, Any]] = {}

    def add(self, group: str, user: str):
        self._groups.setdefault(group, {})
        if "users" not in self._groups[group]:
            self._groups[group]["users"] = []
        self._groups[group]["users"].append(user)
        return self._groups[group]

    def group_size(self, group: str):
        if group not in self._groups:
            return 0
        logger.warn(self._groups[group]["users"])
        return len(self._groups[group]["users"])
    
    def remove(self, group: str, user: str):
        if group not in self._groups:
            return
        self._groups[group]["users"] = [user for user in self._groups[group]["users"] if user != user]
        if len(self._groups[group]["users"]) == 0:
            self._groups.pop(group)
    
    def get(self, group: str):
        if group not in self._groups:
            return {}
        instance = self._groups[group]
        return {
            'group': group,
            'users': [user_model_to_dict(user, avatar=False) for user in instance['users']]
        }
    
    def is_empty(self, group: str):
        if group not in self._groups:
            return True
        if self._groups[group] == []:
            return True
        return False

import logging

logger  = logging.getLogger(__name__)

class TournamentRunner(AsyncConsumer):
    alias = 'tournament_runner'
    _tournaments: Dict[str, Any] = {}
    _tasks: Dict[str, asyncio.Task] = {}

    async def create_games(self, group_name, pairs):
        tournament = await database_sync_to_async(Tournament.objects.get)(id=int(group_name))
        games = []
        self._tournaments[group_name]['stragler'] = None
        for pair in pairs:
            if len(pair) == 1:
                logger.warn(f"Stragler: {pair[0]}")
                self._tournaments[group_name]['stragler'] = pair[0]
                continue
            games.append(await database_sync_to_async(create_game)(pair[0], pair[1], tournament))
        return games

    def get_users(self, user_array):
        users = []
        for user in user_array:
            users.append(User.objects.get(username=user['username']))
        return users


    async def start_tournament(self, event):
        group_name = str(event['name'])
        message = json.loads(event['data'])
        self._tournaments.setdefault(group_name, {})
        self._tournaments[group_name]['users'] = await database_sync_to_async(self.get_users)(message['users'])
        self._tournaments[group_name]['games'] = []
        self._tournaments[group_name]['next_games'] = []
        self._tournaments[group_name]['stragler'] = None
        shuffled_users = self._tournaments[group_name]['users']
        pairs = [shuffled_users[i:i+2] for i in range(0, len(shuffled_users), 2)]
        self._tournaments[group_name]['games'] = await self.create_games(group_name, pairs)
        await database_sync_to_async(update_status)(int(group_name),status='locked')
        await self.channel_layer.group_send(
            group_name,
            {
                'type': 'send_message',
                'status' : 'tournament_starts',
                'message': {'games': await database_sync_to_async(get_games_as_dict)(await database_sync_to_async(Tournament.objects.get)(id=int(group_name)))},
                'stragler' : user_model_to_dict(self._tournaments[group_name]['stragler']) if 'stragler' in self._tournaments[group_name] else None,
            }
        )


    async def game_finished(self, message):
        game_id = int(message['gid'])
        for group in self._tournaments:

            # If there is only one game in this round and no strangler its was the last round
            if len(self._tournaments[group]['games']) == 1 and self._tournaments[group]['stragler'] == None:
                winner = await database_sync_to_async(get_winner)(self._tournaments[group]['games'][0])
                await database_sync_to_async(finish_tournament)(int(group), winner)
                await self.channel_layer.group_send(
                    group,
                    {
                        'type': 'send_message',
                        'status' : 'tournament_ends',
                        'message': {'winner': await database_sync_to_async(user_model_to_dict)(winner)}
                    }
                )
                self._tournaments.pop(group)
                return
            
            # we go to the next round. Create new games and send them to the group
            all_users = await database_sync_to_async(get_winners)(self._tournaments[group]['games'])
            if all_users:
                if self._tournaments[group]['stragler']:
                    all_users.insert(0, self._tournaments[group]['stragler'])
                pairs = [all_users[i:i+2] for i in range(0, len(all_users), 2)]
                self._tournaments[group]['games'] = await self.create_games(group, pairs)
                await self.channel_layer.group_send(
                    group,
                    {
                        'type': 'send_message',
                        'status' : 'next_round',
                        'message': {'games': [pong_model_to_dict(game) for game in self._tournaments[group]['games']]},
                        'stragler' : user_model_to_dict(self._tournaments[group]['stragler']) if 'stragler' in self._tournaments[group] else None,
                    }
                )

    async def status_update(self, event):
        gid = event['gid']
        name = event['name']
        if gid in self._tournaments:
            await self.channel_layer.send(
                name,
                {
                    'type': 'send_message',
                    'status' : 'status_update',
                    'message': {'games': [pong_model_to_dict(game) for game in self._tournaments[gid]['games']]}
                }
            )



class TournamentConsumer(AsyncWebsocketConsumer):
    alias = 'tournament_connector'
    _groups = TournamentGroupManager()

    async def force_disconect(self):
        self.close()

    async def connect(self):
        await self.accept()

        # gets tournament and user from scope
        user = self.scope['user']
        tournament = self.scope['tournament']
        group_name = str(tournament.id)

        # if the group is full close the connection
        if self._groups.group_size(group_name) <= tournament.max_players:
            self._groups.add(group_name, user)
        else:
            await self.close()
            return
        
        # send a message to the group that a user has joined
        user_dict = user_model_to_dict(user, avatar=False)
        await self.channel_layer.group_send(
            group_name,
            {
                'type': 'send_message',
                'message': {'user_joined' : user_dict}
            }
        )
        await self.channel_layer.group_add(group_name, self.channel_name)
        group_data = self._groups.get(group_name)
        await self.send(json.dumps(group_data))
        await database_sync_to_async(tournament.refresh_from_db)()
        if tournament.status == 'open':
            if self._groups.group_size(group_name) == tournament.max_players:
                await self.channel_layer.send(
                    'tournament_runner',
                    {
                        'type': 'start.tournament',
                        'name': group_name,
                        'data' : json.dumps(group_data)
                    }
                )
        else:
            await self.channel_layer.send(
                'tournament_runner',
                {
                    'type': 'status.update',
                    'gid': group_name,
                    'name' : self.channel_name
                }
            )

    async def send_message(self, event):
        message = event
        logger.warn(f"Sending message: {message}")
        await self.send(json.dumps(event))

    async def receive(self, text_data):
        data = json.loads(text_data)

        if 'group' in data:
            self._groups.add(data['group'], self.scope['user'])
        await self.send(text_data)

    async def disconnect(self, close_code):
        user = self.scope['user']
        tournament = self.scope['tournament']
        group_name = str(tournament['id'])
        # self._groups.remove(group_name, user)
        user_dict = await database_sync_to_async(user_model_to_dict)(user, avatar=False)
        self._groups.remove(group_name, user)
        await self.channel_layer.group_discard(group_name, self.channel_name)
        await self.channel_layer.group_send(
            group_name,
            {
                'type': 'send_message',
                'message': {'user_left' : user_dict}
            }
        )
        await asyncio.sleep(0.000001)
        await self.close()


		