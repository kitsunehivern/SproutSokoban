import heapq
import time
import psutil


class UCS:
    class Node:
        playerPos = None
        stonesPos = None
        pathCost = 0
        prevStep = None

        def __init__(self, playerPos, stonesPos):
            self.playerPos = playerPos
            self.stonesPos = stonesPos

        def __lt__(self, other):
            return self.pathCost < other.pathCost

        def toState(self):
            return (self.playerPos, tuple(self.stonesPos))

    maze = None
    weights = None
    playerPos = None
    stonesPos = None
    frontier = None
    dx = [-1, 1, 0, 0]
    dy = [0, 0, -1, 1]
    stepChar = ["U", "D", "L", "R"]

    def __init__(self, weights, maze):
        self.maze = maze
        self.weights = weights
        self.switchsPos = []
        self.stonesPos = []
        for i in range(len(maze)):
            for j in range(len(maze[i])):
                if maze[i][j] == "$" or maze[i][j] == "*":
                    self.stonesPos.append((i, j))
                elif maze[i][j] == "@" or maze[i][j] == "+":
                    self.playerPos = (i, j)

    def isGoal(self, node):
        for pos in node.stonesPos:
            if (
                self.maze[pos[0]][pos[1]] != "."
                and self.maze[pos[0]][pos[1]] != "*"
                and self.maze[pos[0]][pos[1]] != "+"
            ):
                return False

        return True

    def inBound(self, x, y):
        return True  # The maze is always bounded by walls

    def getStoneIndex(self, node, pos):
        for i in range(len(node.stonesPos)):
            if node.stonesPos[i][:2] == pos:
                return i

        return None

    def getNewNode(self, node, idx):
        newPlayerPos = (
            node.playerPos[0] + self.dx[idx],
            node.playerPos[1] + self.dy[idx],
        )
        if (
            not self.inBound(newPlayerPos[0], newPlayerPos[1])
            or self.maze[newPlayerPos[0]][newPlayerPos[1]] == "#"
        ):
            return None

        newStonesPos = node.stonesPos.copy()

        stoneIdx = self.getStoneIndex(node, newPlayerPos)
        if stoneIdx is not None:
            newStonePos = (
                newPlayerPos[0] + self.dx[idx],
                newPlayerPos[1] + self.dy[idx],
            )
            if (
                not self.inBound(newStonePos[0], newStonePos[1])
                or self.maze[newStonePos[0]][newStonePos[1]] == "#"
                or self.getStoneIndex(node, newStonePos) is not None
            ):
                return None

            newStonesPos[stoneIdx] = newStonePos

        newNode = self.Node(newPlayerPos, newStonesPos)
        newNode.pathCost = (
            node.pathCost + 1 + (0 if stoneIdx is None else self.weights[stoneIdx])
        )
        newNode.prevStep = (
            node,
            (
                self.stepChar[idx].upper()
                if stoneIdx is not None
                else self.stepChar[idx].lower()
            ),
        )

        return newNode

    def tracePath(self, node):
        path = ""
        while node.prevStep is not None:
            path += node.prevStep[1]
            node = node.prevStep[0]

        return path[::-1]

    def solve(self):
        process = psutil.Process()
        startTime = time.time()
        startMemory = process.memory_info().rss / (1024 * 1024)

        initNode = self.Node(self.playerPos, self.stonesPos)
        self.frontier = []
        heapq.heappush(self.frontier, initNode)
        reached = {initNode.toState(): initNode.pathCost}

        while len(self.frontier):
            curNode = heapq.heappop(self.frontier)

            if self.isGoal(curNode):
                endTime = time.time()
                endMemory = process.memory_info().rss / (1024 * 1024)
                trace = self.tracePath(curNode)

                return (
                    len(trace),
                    curNode.pathCost - len(trace),
                    len(reached),
                    (endTime - startTime) * 1000,
                    max(endMemory - startMemory, 0.0),
                    self.tracePath(curNode),
                )

            for idx in range(4):
                newNode = self.getNewNode(curNode, idx)
                if newNode is None:
                    continue

                if (
                    newNode.toState() not in reached
                    or newNode.pathCost < reached[newNode.toState()]
                ):
                    reached[newNode.toState()] = newNode.pathCost
                    heapq.heappush(self.frontier, newNode)

        endTime = time.time()
        endMemory = process.memory_info().rss / (1024 * 1024)
        trace = self.tracePath(curNode)

        return None


def getOutput(weights, maze):
    ucs = UCS(weights, maze)
    return ucs.solve()
