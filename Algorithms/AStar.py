import time
import psutil
import copy
from heapq import heappush, heappop
from enum import Enum


class Move(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)


class Direction(Enum):
    UP = "u"
    DOWN = "d"
    LEFT = "l"
    RIGHT = "r"


class Cell(Enum):
    WALL = "#"
    EMPTY = " "
    PLAYER = "@"
    STONE = "$"
    SWITCH = "."
    STONE_SWITCH = "*"
    PLAYER_SWITCH = "+"


MoveToDirection = {
    Move.UP: Direction.UP,
    Move.DOWN: Direction.DOWN,
    Move.LEFT: Direction.LEFT,
    Move.RIGHT: Direction.RIGHT,
}


class Node:
    def __init__(
        self,
        maze,
        player_pos,
        stones,
        switchs,
        g,
        h,
        parent,
        direction=None,
        is_pushing=False,
        cost=0,
    ):
        self.maze = tuple(maze)
        self.player_pos = tuple(player_pos)
        self.stones = tuple(stones)
        self.switchs = tuple(switchs)
        self.g = g
        self.h = h
        self.f = g + h
        self.parent = parent
        self.direction = direction
        self.is_pushing = is_pushing
        self.cost = cost

    def __lt__(self, other):
        return self.f < other.f


class AStar:
    def __init__(self):
        self.maze = []
        self.player = []
        self.weight = []
        self.stones = []
        self.switchs = []
        self.open_set = []
        self.closed_set = set()
        self.node = 1  # Number of nodes generated -- 1 for the initial state
        self.path = None
        self.total_cost = 0
        self.time = 0
        self.memory = 0

    def init_positions(self):
        for i in range(len(self.maze)):
            for j in range(len(self.maze[i])):
                if self.maze[i][j] == Cell.PLAYER.value:
                    self.player = [i, j]
                elif self.maze[i][j] == Cell.STONE.value:
                    self.stones.append([i, j])
                elif self.maze[i][j] == Cell.SWITCH.value:
                    self.switchs.append(
                        [i, j, 0]
                    )  # 0: nothing on switch, 1: stone on switch, 2: player on switch
                elif self.maze[i][j] == Cell.STONE_SWITCH.value:
                    self.stones.append([i, j])
                    self.switchs.append([i, j, 1])
                elif self.maze[i][j] == Cell.PLAYER_SWITCH.value:
                    self.player = [i, j]
                    self.switchs.append([i, j, 2])

    def assign_weights_to_stones(self):
        for i in range(len(self.stones)):
            self.stones[i].append(self.weight[i])

    # Get maze from input file:
    def input(self, weight, maze):
        self.weight = weight
        self.maze = maze
        self.init_positions()
        self.assign_weights_to_stones()

    def print_maze(self):
        for row in self.maze:
            print(row)

    def get_maze(self):
        return self.maze

    def get_weight(self):
        return self.weight

    def get_player_pos(self):
        return self.player

    def get_stones(self):
        return self.stones

    def get_switchs(self):
        return self.switchs

    def get_nodes(self):
        return self.node

    def get_path(self):
        return self.path

    def print_result(self):
        print("A*")
        print(
            f"Steps: {len(self.path)}, Cost: {self.total_cost}, Node: {self.node}, Time (ms): {self.time}, Memory (MB): {self.memory}"
        )
        if self.path:
            print(f"{self.path}\n")
        else:
            print("No path found!")

    def get_result(self):
        if self.path is None:
            return None

        return (
            len(self.path),
            self.total_cost - len(self.path),
            self.node,
            self.time,
            max(self.memory, 0.0),
            self.path,
        )

    def find_a_stone(self, stone_pos):
        stone_index = -1
        for i, stone in enumerate(self.stones):
            if stone[0] == stone_pos[0] and stone[1] == stone_pos[1]:
                stone_index = i
                break
        return stone_index

    def find_a_switch(self, switch_pos):
        switch_index = -1
        for i, switch in enumerate(self.switchs):
            if switch[0] == switch_pos[0] and switch[1] == switch_pos[1]:
                switch_index = i
                break
        return switch_index

    def is_position_switch(self, pos):
        if self.maze[pos[0]][pos[1]] in [
            Cell.SWITCH.value,
            Cell.PLAYER_SWITCH.value,
            Cell.STONE_SWITCH.value,
        ]:
            return True
        return False

    def is_victory(self):
        for switch in self.switchs:
            if switch[2] != 1:
                return False
        return True

    def is_victory_state(self, node):
        self.stones = node.stones
        for switch in self.switchs:
            if switch[2] != 1:
                return False
        # self.print_maze()
        return True

    # Transition state
    def transition(self, move):
        next_pos = [self.player[0] + move.value[0], self.player[1] + move.value[1]]

        # If next move is the Wall -> Do nothing
        if self.maze[next_pos[0]][next_pos[1]] == Cell.WALL.value:
            return

        # If next move is the Stone -> Check the following position
        elif (
            self.maze[next_pos[0]][next_pos[1]] == Cell.STONE.value
            or self.maze[next_pos[0]][next_pos[1]] == Cell.STONE_SWITCH.value
        ):

            # Find which stone it is:
            stone_index = self.find_a_stone([next_pos[0], next_pos[1]])
            next_stone_pos = [next_pos[0] + move.value[0], next_pos[1] + move.value[1]]

            # Stone heading Wall or another Stone -> Do nothing
            if self.maze[next_stone_pos[0]][next_stone_pos[1]] in [
                Cell.WALL.value,
                Cell.STONE.value,
                Cell.STONE_SWITCH.value,
            ]:
                return

            # Stone heading Switch -> Push the stone to the switch
            elif self.maze[next_stone_pos[0]][next_stone_pos[1]] == Cell.SWITCH.value:
                self.maze[next_stone_pos[0]][
                    next_stone_pos[1]
                ] = Cell.STONE_SWITCH.value
                switch_index = self.find_a_switch(
                    [next_stone_pos[0], next_stone_pos[1]]
                )
                self.switchs[switch_index][2] = 1

            # Stone heading Empty Space
            elif self.maze[next_stone_pos[0]][next_stone_pos[1]] == Cell.EMPTY.value:
                self.maze[next_stone_pos[0]][next_stone_pos[1]] = Cell.STONE.value

            # Update stone position
            self.stones[stone_index][:2] = next_stone_pos

            if self.is_position_switch(next_pos):
                self.maze[next_pos[0]][next_pos[1]] = Cell.PLAYER_SWITCH.value
                switch_index = self.find_a_switch([next_pos[0], next_pos[1]])
                self.switchs[switch_index][2] = 2
            else:
                self.maze[next_pos[0]][next_pos[1]] = Cell.PLAYER.value

        # If next move is the Switch
        elif self.maze[next_pos[0]][next_pos[1]] == Cell.SWITCH.value:
            self.maze[next_pos[0]][next_pos[1]] = Cell.PLAYER_SWITCH.value
            switch_index = self.find_a_switch([next_pos[0], next_pos[1]])
            self.switchs[switch_index][2] = 2

        # If next move is the Empty Space
        elif self.maze[next_pos[0]][next_pos[1]] == Cell.EMPTY.value:
            self.maze[next_pos[0]][next_pos[1]] = Cell.PLAYER.value

        # Update the previous position
        # If player was on the switch -> Update the switch
        if self.maze[self.player[0]][self.player[1]] == Cell.PLAYER_SWITCH.value:
            switch_index = self.find_a_switch([self.player[0], self.player[1]])
            self.maze[self.player[0]][self.player[1]] = Cell.SWITCH.value
            self.switchs[switch_index][2] = 0

        else:
            self.maze[self.player[0]][self.player[1]] = Cell.EMPTY.value

        self.player = next_pos  # Update player position
        # print(self.get_player_pos())
        # print(self.get_stones())
        # print(self.get_switchs())
        # self.print_maze()

    # Calculate Manhattan Distance
    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def is_deadlock_position(self, stone_pos):
        x, y = stone_pos[:2]
        maze = self.get_maze()

        # 1. Corner Deadlock Check (box against two walls, and no goal in the corner)
        if (
            (maze[x - 1][y] == "#" and maze[x][y - 1] == "#")
            or (maze[x - 1][y] == "#" and maze[x][y + 1] == "#")
            or (maze[x + 1][y] == "#" and maze[x][y - 1] == "#")
            or (maze[x + 1][y] == "#" and maze[x][y + 1] == "#")
        ):
            if maze[x][y] not in [Cell.STONE_SWITCH.value, Cell.SWITCH.value]:
                return True

        # 2. Wall Deadlock Check (two boxes in a row along the wall):
        # Check if two boxes are horizontally or vertically adjacent along a wall
        if maze[x - 1][y] == "#" or maze[x + 1][y] == "#":
            if (
                maze[x][y + 1] == "$"
                and maze[x][y + 1] not in [Cell.STONE_SWITCH.value, Cell.SWITCH.value]
                and (maze[x - 1][y + 1] == "#" or maze[x + 1][y + 1] == "#")
            ) or (
                maze[x][y - 1] == "$"
                and maze[x][y - 1] not in [Cell.STONE_SWITCH.value, Cell.SWITCH.value]
                and (maze[x - 1][y - 1] == "#" or maze[x + 1][y - 1] == "#")
            ):
                return True  # Horizontal wall deadlock

        if maze[x][y - 1] == "#" or maze[x][y + 1] == "#":
            if (
                maze[x + 1][y] == "$"
                and maze[x + 1][y] not in [Cell.STONE_SWITCH.value, Cell.SWITCH.value]
                and (maze[x + 1][y - 1] == "#" or maze[x + 1][y + 1] == "#")
            ) or (
                maze[x - 1][y] == "$"
                and maze[x - 1][y] not in [Cell.STONE_SWITCH.value, Cell.SWITCH.value]
                and (maze[x - 1][y - 1] == "#" or maze[x - 1][y + 1] == "#")
            ):
                return True  # Vertical wall deadlock

        return False

    def heuristic_function(self):
        player_pos = self.get_player_pos()
        stones = self.get_stones()
        switches = self.get_switchs()

        if self.is_victory():
            return 0

        # Check for deadlock -> If yes -> +10000000
        for stone in stones:
            if self.is_deadlock_position(stone):
                return 10000000

        # Calculate the minimum distance from player to any stone
        min_player_to_stone = min(
            self.manhattan_distance(player_pos, stone[:2]) for stone in stones
        )

        # Calculate the sum of weighted distances from each stone to the nearest switch
        total_weighted_distance = 0
        for stone in stones:
            stone_pos = stone[:2]
            stone_weight = stone[2]
            min_stone_to_switch = float("inf")
            for switch in switches:
                if switch[2] == 1:
                    continue
                else:
                    min_stone_to_switch = min(
                        self.manhattan_distance(stone_pos, switch[:2])
                        for switch in switches
                    )
            total_weighted_distance += min_stone_to_switch * stone_weight

        return min_player_to_stone + total_weighted_distance

    def state_to_tuple(self, node):
        return (tuple(node.player_pos), tuple(tuple(stone) for stone in node.stones))

    def reconstruct_path(self, node):
        self.path = ""
        while node.parent is not None:
            self.path += (
                MoveToDirection[node.direction].value.upper()
                if node.is_pushing
                else MoveToDirection[node.direction].value
            )
            self.total_cost += node.cost
            node = node.parent

        self.path = self.path[::-1]
        return None

    def is_pushing_stone(self, player_pos, move, temp_maze):
        next_pos = [player_pos[0] + move.value[0], player_pos[1] + move.value[1]]
        return temp_maze[next_pos[0]][next_pos[1]] in [
            Cell.STONE.value,
            Cell.STONE_SWITCH.value,
        ]

    def get_neighbor(self, current_node, move):

        temp_maze = copy.deepcopy(self.get_maze())
        temp_player = copy.deepcopy(self.get_player_pos())
        temp_stones = copy.deepcopy(self.get_stones())
        temp_switchs = copy.deepcopy(self.get_switchs())

        self.transition(move)

        new_maze = self.maze
        new_player_pos = self.player
        new_stones = self.stones
        new_switchs = self.switchs

        if self.state_to_tuple(current_node) == self.state_to_tuple(
            Node(new_maze, new_player_pos, new_stones, new_switchs, 0, 0, None)
        ):
            return None  # Invalid move

        # Calculating g(n), h(n):
        g = current_node.g + 1
        h = copy.deepcopy(self.heuristic_function())

        # Calculate cost of the move:
        # If pushing a stone, cost = 1 + weight of the stone
        # If NOT pushing a stone, cost = 1
        cost = 0
        if self.is_pushing_stone(current_node.player_pos, move, temp_maze):
            new_stone_pos = [
                new_player_pos[0] + move.value[0],
                new_player_pos[1] + move.value[1],
            ]
            stone_index = self.find_a_stone(new_stone_pos)
            cost = 1 + self.stones[stone_index][2]  # Add weight of the stone
        else:
            cost = 1

        neighbor = Node(
            new_maze,
            new_player_pos,
            new_stones,
            new_switchs,
            g,
            h,
            current_node,
            move,
            self.is_pushing_stone(current_node.player_pos, move, temp_maze),
            cost,
        )

        self.maze = temp_maze
        self.player = temp_player
        self.stones = temp_stones
        self.switchs = temp_switchs

        self.node += 1
        # print(f'{self.node}. -- G(n): {g} -- H(n): {h} -- F(n): {g + h}')
        return neighbor

    def a_star_search(self):
        # Measure start time and memory
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)

        initial_maze = self.get_maze()
        initial_player_pos = self.get_player_pos()
        initial_stones = self.get_stones()
        inital_switchs = self.get_switchs()
        initial_heuristic = self.heuristic_function()

        start_node = Node(
            initial_maze,
            initial_player_pos,
            initial_stones,
            inital_switchs,
            0,
            initial_heuristic,
            None,
            None,
            False,
            0,
        )
        heappush(self.open_set, start_node)

        while self.open_set:
            current_node = heappop(self.open_set)
            self.maze = current_node.maze
            self.player = current_node.player_pos
            self.stones = current_node.stones
            self.switchs = current_node.switchs

            if self.is_victory_state(current_node):
                # Measure end time and memory
                end_time = time.time()
                end_memory = process.memory_info().rss / (1024 * 1024)  # in MB
                self.time = (end_time - start_time) * 1000  # in ms
                self.memory = end_memory - start_memory
                return self.reconstruct_path(current_node)

            self.closed_set.add(self.state_to_tuple(current_node))

            for move in Move:
                neighbor = self.get_neighbor(current_node, move)
                if neighbor is None:
                    continue

                neighbor_tuple = self.state_to_tuple(neighbor)
                if neighbor_tuple in self.closed_set:
                    continue

                # Check if the neighbor already exists in the open set

                existing_neighbor = None
                for open_node in self.open_set:
                    if self.state_to_tuple(open_node) == neighbor_tuple:
                        existing_neighbor = open_node
                        break

                # If the neighbor is not in the open set or has a better f score, update
                if existing_neighbor is None:
                    # New neighbor, push it onto the heap
                    heappush(self.open_set, neighbor)
                elif neighbor.f < existing_neighbor.f:
                    # Better path found, update the existing neighbor
                    self.open_set.remove(existing_neighbor)
                    heappush(self.open_set, neighbor)

        # Measure end time and memory
        end_time = time.time()
        end_memory = process.memory_info().rss / (1024 * 1024)
        self.time = (end_time - start_time) * 1000
        self.memory = end_memory - start_memory
        return None


def getOutput(weights, maze):
    astar = AStar()
    astar.input(weights, maze)
    astar.a_star_search()
    return astar.get_result()
