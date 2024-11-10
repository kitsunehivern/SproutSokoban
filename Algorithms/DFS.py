import time
import psutil

DIRECTIONS = {"u": (-1, 0), "d": (1, 0), "l": (0, -1), "r": (0, 1)}
PUSH_DIRECTIONS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
DEPTH_THRESHOLD = 1000


def getOutput(weights, maze):
    game = Sokoban(maze, weights)

    foundResult, elapsedTime, totalMemory = game.solve()

    if foundResult:
        return (
            game.result["steps"],
            game.result["weight"] - game.result["steps"],
            game.result["node"],
            elapsedTime * 1000,
            max(totalMemory, 0.0),
            game.result["trace"],
        )
    elif game.result["trace"] == "TLE":
        print("TLE")
        return None
    else:
        return None


class Sokoban:
    def __init__(self, maze, weights):
        self.maze = maze
        self.start_position = None
        self.stones = []
        stoneIter = iter(weights)
        for i in range(len(maze)):
            for j in range(len(maze[i])):
                if maze[i][j] == "@" or maze[i][j] == "+":
                    self.start_position = (i, j)

                if maze[i][j] == "$" or maze[i][j] == "*":
                    self.stones.append((i, j, next(stoneIter)))

        self.result = {"trace": "", "steps": 0, "weight": 0, "node": 0}

    def isGoal(self, state):
        stones = state[1:]
        for stone in stones:
            if (
                self.maze[stone[0]][stone[1]] != "."
                and self.maze[stone[0]][stone[1]] != "*"
                and self.maze[stone[0]][stone[1]] != "+"
            ):
                return False
        return True

    def isFreeSpace(self, pos, stones):
        if self.maze[pos[0]][pos[1]] == "#":
            return False

        for stone in stones:
            if stone[0] == pos[0] and stone[1] == pos[1]:
                return False

        return True

    def getNeighbors(self, player, stones):
        neighbors = []
        for move, direction in DIRECTIONS.items():
            nextPos = (player[0] + direction[0], player[1] + direction[1])
            if not self.isFreeSpace(nextPos, stones):
                continue

            state = (nextPos, *sorted(stones))
            neighbor = {"move": move, "state": state, "cost": 1}
            neighbors.append(neighbor)

        for move, direction in PUSH_DIRECTIONS.items():
            nextPos = (player[0] + direction[0], player[1] + direction[1])
            nextNextPos = (player[0] + 2 * direction[0], player[1] + 2 * direction[1])

            for stone in stones:
                if stone[0] == nextPos[0] and stone[1] == nextPos[1]:
                    if not self.isFreeSpace(nextNextPos, stones):
                        continue

                    newStones = [s for s in stones if s != stone]
                    newStones.append((nextNextPos[0], nextNextPos[1], stone[2]))
                    state = (nextPos, *sorted(newStones))

                    neighbor = {"move": move, "state": state, "cost": 1 + stone[2]}
                    neighbors.append(neighbor)
                    break

        return neighbors

    def solve(self):
        # if time.time() - self.start_time > 5:
        #     self.result['trace'] = "TLE"
        #     return False

        startTime = time.time()
        # tracemalloc.start()
        process = psutil.Process()
        startMemory = process.memory_info().rss / (1024 * 1024)

        visited = set()
        startState = (self.start_position, *sorted(self.stones))
        stateStack = [(startState, "", 0, 0, 0)]
        foundResult = self.isGoal(startState)

        while stateStack and not foundResult:
            state, path, totalStep, totalWeight, depth = stateStack.pop()
            visited.add(state)
            self.result["node"] += 1
            if depth > DEPTH_THRESHOLD:
                continue

            neighbors = self.getNeighbors(state[0], state[1:])
            for neighbor in neighbors:
                if self.isGoal(neighbor["state"]):
                    self.result["steps"] = totalStep + 1
                    self.result["weight"] = totalWeight + neighbor["cost"]
                    self.result["trace"] = path + neighbor["move"]
                    foundResult = True
                    break

            for neighbor in neighbors:
                if neighbor["state"] in visited:
                    continue
                stateStack.append(
                    (
                        neighbor["state"],
                        path + neighbor["move"],
                        totalStep + 1,
                        totalWeight + neighbor["cost"],
                        depth + 1,
                    )
                )

        elapsedTime = time.time() - startTime
        totalMemory = process.memory_info().rss / (1024 * 1024) - startMemory

        return foundResult, elapsedTime, totalMemory
