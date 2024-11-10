import pygame
import pygame_gui
import os
import json
import random
import traceback
from collections import deque

from BitmaskReferences import BitmaskReferences
import MazeGenerator
import StoppableThread

from Algorithms import BFS, DFS, UCS, AStar


class Visualizer:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    MAZE_SIZE = 600
    MAZE_CELL = 20
    NOTI_TIME = 3.0

    assets = {}
    bf = BitmaskReferences()

    mazeDatas = []
    fileToIndex = {}

    choosenMaze = None
    choosenAlgorithm = None

    newMaze = None
    isEditing = False
    isMouseDown = False
    isGenerating = False
    choosenObject = None
    choosenMazeSize = 10
    choosenNumStones = 1

    playerDirection = 0
    countSteps = 0
    totalWeight = 0

    allSpeeds = [1, 2, 5, 10, 20, 50, 100]
    spinSpeed = allSpeeds[2]
    spinClock = None
    isRunning = False
    visualizeClock = None
    visualizeSpeed = None
    notiClock = None

    grassPosition = None
    hasWon = False

    def __init__(self):
        self.loadMaze()
        self.loadAssets()
        self.loadSettings()

        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Sprout Sokoban")
        pygame.display.set_icon(self.assets["icon"].subsurface((2, 2, 28, 28)))
        self.clock = pygame.time.Clock()
        print(os.getcwd())
        self.manager = pygame_gui.UIManager(
            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            theme_path="Assets/CustomTheme.json",
        )

        self.font = pygame.font.Font("Assets/Fonts/SproutLands.ttf", 14)
        self.manager.add_font_paths("SproutLands", "Assets/Fonts/SproutLands.ttf")
        self.manager.preload_fonts(
            [{"name": "SproutLands", "point_size": 14, "style": "regular"}]
        )

        self.mazeText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 20), (180, 30)),
            text="Choose maze",
            manager=self.manager,
            object_id="#maze_label",
        )

        self.mazeDropdownMenu = pygame_gui.elements.UIDropDownMenu(
            options_list=[f"{mazeData[2]}" for mazeData in self.mazeDatas],
            starting_option=f"{self.mazeDatas[self.choosenMaze][2]}",
            relative_rect=pygame.Rect((10, 50), (180, 30)),
            manager=self.manager,
            object_id="#maze_dropdown_menu",
        )

        self.algorithmText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 90), (180, 30)),
            text="Choose algorithm",
            manager=self.manager,
            object_id="#maze_label",
        )

        self.algorithmDropDownMenu = pygame_gui.elements.UIDropDownMenu(
            options_list=["Manual", "BFS", "DFS", "UCS", "A*"],
            starting_option=self.choosenAlgorithm,
            relative_rect=pygame.Rect((10, 120), (180, 30)),
            manager=self.manager,
            object_id="#algorithm_dropdown_menu",
        )

        self.visualizeText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 160), (180, 30)),
            text="Visualize",
            manager=self.manager,
            object_id="#visualize_label",
        )

        self.speedSlider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((10, 190), (180, 30)),
            start_value=1,
            value_range=(1, 100),
            manager=self.manager,
            object_id="#speed_slider",
        )
        self.speedSlider.sliding_button.hide()

        self.speedText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 190), (180, 30)),
            text=f"Speed: {self.visualizeSpeed}x",
            manager=self.manager,
            object_id="#speed_text",
        )

        self.runButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 230), (180, 30)),
            text="Run",
            manager=self.manager,
            object_id="#run_button",
        )
        if self.choosenAlgorithm == "Manual":
            self.runButton.disable()

        self.resetButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 270), (180, 30)),
            text="Reset",
            manager=self.manager,
            object_id="#reset_button",
        )

        self.statText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 310), (180, 30)),
            text="Statistics",
            manager=self.manager,
            object_id="#stat_label",
        )

        self.statBox = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((10, 340), (180, 90)),
            html_text="",
            manager=self.manager,
            object_id="#stat_box",
        )

        self.stepText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 340), (180, 30)),
            text="",
            manager=self.manager,
            object_id="#step_label",
        )

        self.weightText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 370), (180, 30)),
            text="",
            manager=self.manager,
            object_id="#weight_label",
        )

        self.costText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 400), (180, 30)),
            text="",
            manager=self.manager,
            object_id="#cost_label",
        )

        self.cancelButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 510), (180, 30)),
            text="Cancel",
            manager=self.manager,
            object_id="#cancel_button",
        )
        self.cancelButton.hide()

        self.editButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 510), (180, 30)),
            text="Edit",
            manager=self.manager,
            object_id="#edit_button",
        )

        self.createButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 550), (180, 30)),
            text="Create",
            manager=self.manager,
            object_id="#create_button",
        )

        self.objectText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 20), (180, 30)),
            text="Choose object",
            manager=self.manager,
            object_id="#object_label",
        )
        self.objectText.hide()

        self.objectDropdownMenu = pygame_gui.elements.UIDropDownMenu(
            options_list=["Hill", "Land", "Stone", "Switch", "Player"],
            starting_option="Hill",
            relative_rect=pygame.Rect((10, 50), (180, 30)),
            manager=self.manager,
            object_id="#object_dropdown_menu",
        )
        self.objectDropdownMenu.hide()

        self.generateText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 90), (180, 30)),
            text="Generate maze",
            manager=self.manager,
            object_id="#generate_label",
        )
        self.generateText.hide()

        self.mazeSizeSlider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((10, 120), (180, 30)),
            start_value=10,
            value_range=(10, 20),
            manager=self.manager,
            object_id="#maze_size_slider",
        )
        self.mazeSizeSlider.hide()

        self.mazeSizeText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 120), (180, 30)),
            text="Maze size: 10x10",
            manager=self.manager,
            object_id="#maze_side_text",
        )
        self.mazeSizeText.hide()

        self.numStonesSlider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((10, 160), (180, 30)),
            start_value=1,
            value_range=(1, 10),
            manager=self.manager,
            object_id="#num_stones_slider",
        )
        self.numStonesSlider.hide()

        self.numStonesText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 160), (180, 30)),
            text="No. stones: 1",
            manager=self.manager,
            object_id="#num_stones_text",
        )
        self.numStonesText.hide()

        self.randomButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 200), (180, 30)),
            text="Random",
            manager=self.manager,
            object_id="#random_button",
        )
        self.randomButton.hide()

        self.clearButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 240), (180, 30)),
            text="Empty",
            manager=self.manager,
            object_id="#clear_button",
        )
        self.clearButton.hide()

        self.notiBox = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((300, 560), (400, 30)),
            html_text="",
            manager=self.manager,
            object_id="#noti_box",
        )
        self.notiBox.hide()

        self.notiText = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((300, 560), (400, 30)),
            text="",
            manager=self.manager,
            object_id="#noti_text",
        )
        self.notiText.hide()

        self.choosenObject = "Hill"
        self.chooseMaze(self.choosenMaze)
        self.chooseAlgorithm(self.choosenAlgorithm)

    def __del__(self):
        self.saveSettings()

    def run(self):
        isFilenameWindowOpen = False
        while True:
            deltaTime = self.clock.tick(60) / 1000.0
            self.manager.update(deltaTime)
            if self.visualizeClock is not None:
                self.visualizeClock += deltaTime
                while (
                    self.visualizeClock is not None
                    and self.visualizeClock >= 1 / self.visualizeSpeed
                ):
                    self.visualizeClock -= 1 / self.visualizeSpeed
                    self.visualizeAlgorithm()

            if self.spinClock is not None:
                self.spinClock += deltaTime
                while (
                    self.spinClock is not None and self.spinClock >= 1 / self.spinSpeed
                ):
                    self.spinClock -= 1 / self.spinSpeed
                    match self.playerDirection:
                        case 0:
                            self.playerDirection = 2
                        case 1:
                            self.playerDirection = 3
                        case 2:
                            self.playerDirection = 1
                        case 3:
                            self.playerDirection = 0

            if self.notiClock is not None:
                self.notiClock += deltaTime
                if self.notiClock >= self.NOTI_TIME:
                    self.notiClock = None
                    self.notiBox.hide()
                    self.notiText.hide()

            self.screen.fill((232, 207, 166))

            self.drawMaze()
            self.manager.draw_ui(self.screen)

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                self.manager.process_events(event)

                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                        if event.ui_object_id == "#maze_dropdown_menu":
                            self.chooseMaze(self.fileToIndex[event.text])
                        elif event.ui_object_id == "#algorithm_dropdown_menu":
                            if event.text == "Manual":
                                self.runButton.disable()
                            else:
                                self.runButton.enable()
                            self.chooseAlgorithm(event.text)

                        elif event.ui_object_id == "#object_dropdown_menu":
                            if self.isEditing and not isFilenameWindowOpen:
                                self.choosenObject = event.text

                    elif event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_object_id == "#run_button":
                            if not self.isRunning:
                                thread = StoppableThread.StoppableThread(
                                    target=self.runAlgorithm
                                )
                                thread.start()
                            else:
                                thread.stop()
                                self.playerDirection = 0
                                self.spinClock = None
                                self.visualizeClock = 0.0
                                self.isRunning = False
                                self.notify("Algorithm stopped")
                        elif event.ui_object_id == "#reset_button":
                            self.chooseMaze(self.choosenMaze)
                            self.notify("Maze reset")
                        elif event.ui_object_id == "#edit_button":
                            self.createMaze(edit=True)
                        elif event.ui_object_id == "#create_button":
                            if not self.isEditing:
                                self.createMaze()
                            elif not isFilenameWindowOpen:
                                self.savedWeights = []
                                self.savedMaze = [
                                    [""] * self.MAZE_CELL for _ in range(self.MAZE_CELL)
                                ]
                                for i in range(self.MAZE_CELL):
                                    for j in range(self.MAZE_CELL):
                                        if (
                                            self.newMaze[i][j][0] == "$"
                                            or self.newMaze[i][j][0] == "*"
                                        ):
                                            self.savedWeights.append(
                                                int(self.newMaze[i][j][1:])
                                            )
                                        self.savedMaze[i][j] = self.newMaze[i][j][0]

                                if self.validateMaze(
                                    (self.savedWeights, self.savedMaze, "input-##.txt")
                                ):
                                    fileNameWindow = pygame_gui.elements.UIWindow(
                                        rect=pygame.Rect(
                                            (
                                                (self.SCREEN_WIDTH - 300) / 2,
                                                (self.SCREEN_HEIGHT - 120) / 2,
                                            ),
                                            (300, 120),
                                        ),
                                        manager=self.manager,
                                        window_display_title="Enter File Name",
                                        object_id="#file_name_window",
                                    )

                                    fileNameEntry = pygame_gui.elements.UITextEntryLine(
                                        relative_rect=pygame.Rect((10, 10), (280, 30)),
                                        manager=self.manager,
                                        container=fileNameWindow,
                                    )
                                    fileNameEntry.set_text("")
                                    fileNameEntry.focus()

                                    pygame_gui.elements.UIButton(
                                        relative_rect=pygame.Rect((10, 50), (280, 30)),
                                        text="Confirm",
                                        manager=self.manager,
                                        container=fileNameWindow,
                                        object_id="#confirm_button",
                                    )

                                    isFilenameWindowOpen = True
                        elif event.ui_object_id == "#cancel_button":
                            if not isFilenameWindowOpen:
                                self.cancelCreate()
                        elif event.ui_object_id == "#clear_button":
                            if not isFilenameWindowOpen:
                                self.newMaze = [
                                    [
                                        (
                                            "#"
                                            if i == 0
                                            or i == self.MAZE_CELL - 1
                                            or j == 0
                                            or j == self.MAZE_CELL - 1
                                            else " "
                                        )
                                        for j in range(self.MAZE_CELL)
                                    ]
                                    for i in range(self.MAZE_CELL)
                                ]
                        elif event.ui_object_id == "#random_button":
                            if not isFilenameWindowOpen:
                                thread = StoppableThread.StoppableThread(
                                    target=self.generateMaze
                                )
                                thread.start()
                        elif event.ui_object_id == "#file_name_window.#confirm_button":
                            self.saveMaze(
                                (
                                    "-".join(
                                        "".join(
                                            c if c.isalnum() else " "
                                            for c in fileNameEntry.get_text()
                                        ).split()
                                    )
                                ).lower()
                            )
                            isFilenameWindowOpen = False
                            fileNameWindow.hide()
                            self.notify("Maze saved")
                        elif (
                            event.ui_object_id == "#maze_size_slider.#left_button"
                            or event.ui_object_id == "#maze_size_slider.#right_button"
                        ):
                            if not isFilenameWindowOpen:
                                if (
                                    event.ui_object_id
                                    == "#maze_size_slider.#left_button"
                                ):
                                    self.choosenMazeSize = max(
                                        self.choosenMazeSize - 1,
                                        self.mazeSizeSlider.value_range[0],
                                    )
                                else:
                                    self.choosenMazeSize = min(
                                        self.choosenMazeSize + 1,
                                        self.mazeSizeSlider.value_range[1],
                                    )
                                self.mazeSizeText.set_text(
                                    f"Maze size: {self.choosenMazeSize}x{self.choosenMazeSize}"
                                )
                        elif (
                            event.ui_object_id == "#num_stones_slider.#left_button"
                            or event.ui_object_id == "#num_stones_slider.#right_button"
                        ):
                            if not isFilenameWindowOpen:
                                if (
                                    event.ui_object_id
                                    == "#num_stones_slider.#left_button"
                                ):
                                    self.choosenNumStones = max(
                                        self.choosenNumStones - 1,
                                        self.numStonesSlider.value_range[0],
                                    )
                                else:
                                    self.choosenNumStones = min(
                                        self.choosenNumStones + 1,
                                        self.numStonesSlider.value_range[1],
                                    )
                                self.numStonesText.set_text(
                                    f"No. stones: {self.choosenNumStones}"
                                )
                        elif (
                            event.ui_object_id == "#speed_slider.#left_button"
                            or event.ui_object_id == "#speed_slider.#right_button"
                        ):
                            if event.ui_object_id == "#speed_slider.#left_button":
                                self.visualizeSpeed = self.allSpeeds[
                                    max(
                                        0, self.allSpeeds.index(self.visualizeSpeed) - 1
                                    )
                                ]
                            else:
                                self.visualizeSpeed = self.allSpeeds[
                                    min(
                                        len(self.allSpeeds) - 1,
                                        self.allSpeeds.index(self.visualizeSpeed) + 1,
                                    )
                                ]
                            self.speedText.set_text(f"Speed: {self.visualizeSpeed}x")
                    elif event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                        if event.ui_object_id == "#file_name_window":
                            isFilenameWindowOpen = False
                            fileNameWindow.hide()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.isMouseDown = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.isMouseDown = False
                elif event.type == pygame.KEYDOWN:
                    if not self.isEditing and self.choosenAlgorithm == "Manual":
                        match event.key:
                            case pygame.K_UP:
                                self.movePlayer(-1, 0)
                            case pygame.K_w:
                                self.movePlayer(-1, 0)
                            case pygame.K_DOWN:
                                self.movePlayer(1, 0)
                            case pygame.K_s:
                                self.movePlayer(1, 0)
                            case pygame.K_LEFT:
                                self.movePlayer(0, -1)
                            case pygame.K_a:
                                self.movePlayer(0, -1)
                            case pygame.K_RIGHT:
                                self.movePlayer(0, 1)
                            case pygame.K_d:
                                self.movePlayer(0, 1)

                if (
                    self.isEditing
                    and self.isMouseDown
                    and not isFilenameWindowOpen
                    and not self.isGenerating
                ):
                    self.placeObject()

    def notify(self, text):
        self.notiBox.show()
        self.notiText.show()
        self.notiText.set_text(text)
        self.notiClock = 0.0

    def visualizeAlgorithm(self):
        if (
            self.algorithmResult is None
            or self.algorithmResult[5] is None
            or self.visualizeIndex >= len(self.algorithmResult[5])
        ):
            self.visualizeClock = None
            self.mazeDropdownMenu.enable()
            self.algorithmDropDownMenu.enable()
            self.resetButton.enable()
            self.runButton.set_text("Run")
            self.runButton.enable()
            self.editButton.enable()
            self.createButton.enable()
            return

        # print(
        #     f"Step {self.visualizeIndex + 1}/{len(self.algorithmResult[5])}: {self.algorithmResult[5][self.visualizeIndex]}"
        # )

        dx, dy = 0, 0
        pushStone = False
        match self.algorithmResult[5][self.visualizeIndex]:
            case "u":
                dx = -1
            case "d":
                dx = 1
            case "l":
                dy = -1
            case "r":
                dy = 1
            case "U":
                dx = -1
                pushStone = True
            case "D":
                dx = 1
                pushStone = True
            case "L":
                dy = -1
                pushStone = True
            case "R":
                dy = 1
                pushStone = True

        nx, ny = self.playerPosition[0] + dx, self.playerPosition[1] + dy

        if self.currentMaze[nx][ny] == "#":
            print("Invalid move: Hill in the way")
            self.notify("Invalid move: Hill in the way")
            self.visualizeIndex += 1
            return

        if pushStone == True:
            if (
                self.currentMaze[nx][ny][0] != "$"
                and self.currentMaze[nx][ny][0] != "*"
            ):
                print("Invalid move: No stone to push")
                self.notify("Invalid move: No stone to push")
                self.visualizeIndex += 1
                return
        else:
            if self.currentMaze[nx][ny] == "$" or self.currentMaze[nx][ny] == "*":
                print("Invalid move: Cannot push the stone")
                self.notify("Invalid move: Cannot push the stone")
                self.visualizeIndex += 1
                return

        self.movePlayer(dx, dy)
        self.visualizeIndex += 1

    def saveResult(self):
        savedResult = []
        if os.path.exists(f"Mazes/output-{self.mazeDatas[self.choosenMaze][2]}.txt"):
            with open(
                f"Mazes/output-{self.mazeDatas[self.choosenMaze][2]}.txt", "r"
            ) as f:
                savedResult = f.read().split("\n")

        while len(savedResult) < 12:
            savedResult.append("Not available")

        lineIdx = 0
        for algo in ["BFS", "DFS", "UCS", "A*"]:
            savedResult[lineIdx] = f"{algo}"
            if self.choosenAlgorithm == algo:
                savedResult[lineIdx + 1] = (
                    f"Steps: {self.algorithmResult[0]}, Weight: {self.algorithmResult[1]}, Node: {self.algorithmResult[2]}, Time (ms): {self.algorithmResult[3]:.2f}, Memory (MB): {self.algorithmResult[4]:.2f}"
                )
                savedResult[lineIdx + 2] = self.algorithmResult[5]
            lineIdx += 3

        with open(f"Mazes/output-{self.mazeDatas[self.choosenMaze][2]}.txt", "w") as f:
            f.write("\n".join(savedResult))

    def runAlgorithm(self):
        self.isRunning = True

        self.mazeDropdownMenu.disable()
        self.algorithmDropDownMenu.disable()
        self.resetButton.disable()
        self.runButton.set_text("Stop")
        self.editButton.disable()
        self.createButton.disable()

        parameterWeights = []
        parameterMaze = [[cell[0] for cell in line] for line in self.currentMaze]
        self.algorithmResult = None
        self.spinClock = 0.0
        for i in range(len(self.currentMaze)):
            for j in range(len(self.currentMaze[0])):
                if self.currentMaze[i][j][0] == "$" or self.currentMaze[i][j][0] == "*":
                    parameterWeights.append(int(self.currentMaze[i][j][1:]))

        try:
            if self.choosenAlgorithm == "BFS":
                self.algorithmResult = BFS.getOutput(parameterWeights, parameterMaze)
            elif self.choosenAlgorithm == "DFS":
                self.algorithmResult = DFS.getOutput(parameterWeights, parameterMaze)
            elif self.choosenAlgorithm == "UCS":
                self.algorithmResult = UCS.getOutput(parameterWeights, parameterMaze)
            elif self.choosenAlgorithm == "A*":
                self.algorithmResult = AStar.getOutput(parameterWeights, parameterMaze)

            if self.algorithmResult is None:
                print("No solution")
                self.notify("No solution")
        except Exception:
            traceback.print_exc()
            print("Algorithm failed")
            self.notify("Failed to run algorithm")
            self.algorithmResult = None

        print("Algorithm result:", self.algorithmResult)

        if self.countSteps == 0 and self.algorithmResult is not None:
            self.saveResult()

        self.playerDirection = 0
        self.spinClock = None
        self.visualizeIndex = 0
        self.visualizeClock = 0.0
        self.runButton.set_text("Visualizing")
        self.runButton.disable()
        self.isRunning = False

    def generateMaze(self):
        self.objectDropdownMenu.disable()
        self.mazeSizeSlider.disable()
        self.mazeSizeText.disable()
        self.numStonesSlider.disable()
        self.numStonesText.disable()
        self.randomButton.disable()
        self.clearButton.disable()
        self.cancelButton.disable()
        self.createButton.disable()
        self.isGenerating = True

        startTime = pygame.time.get_ticks()
        try:
            self.newMaze = self.centerMaze(
                self.normalizeMaze(
                    MazeGenerator.generate_maze(
                        self.choosenMazeSize, self.choosenNumStones
                    )
                ),
                self.MAZE_CELL,
            )
        except Exception:
            traceback.print_exc()
            print("Failed to generate maze")
            self.notify("Failed to generate maze")
            self.objectDropdownMenu.enable()
            self.mazeSizeSlider.enable()
            self.mazeSizeText.enable()
            self.numStonesSlider.enable()
            self.numStonesText.enable()
            self.randomButton.enable()
            self.clearButton.enable()
            self.cancelButton.enable()
            self.createButton.enable()
            self.isGenerating = False
            return

        endTime = pygame.time.get_ticks()
        self.objectDropdownMenu.enable()
        self.mazeSizeSlider.enable()
        self.mazeSizeText.enable()
        self.numStonesSlider.enable()
        self.numStonesText.enable()
        self.randomButton.enable()
        self.clearButton.enable()
        self.cancelButton.enable()
        self.createButton.enable()
        self.isGenerating = False

        print(f"Maze generated in {(endTime - startTime) / 1000:.3f} seconds")
        self.notify("Maze generated")

    def isWinning(self):
        for i in range(len(self.currentMaze)):
            for j in range(len(self.currentMaze[0])):
                if (
                    self.currentMaze[i][j] == "."
                    or self.currentMaze[i][j] == "$"
                    or self.currentMaze[i][j] == "+"
                ):
                    return False
        return True

    def movePlayer(self, dx, dy):
        match (dx, dy):
            case (-1, 0):
                self.playerDirection = 1
            case (1, 0):
                self.playerDirection = 0
            case (0, -1):
                self.playerDirection = 2
            case (0, 1):
                self.playerDirection = 3

        x, y = self.playerPosition
        nx, ny = x + dx, y + dy

        if self.currentMaze[nx][ny] == "#":
            print("Invalid move: Hill in the way")
            self.notify("Invalid move: Hill in the way")
            return

        if self.currentMaze[nx][ny][0] == "$" or self.currentMaze[nx][ny][0] == "*":
            nnx, nny = nx + dx, ny + dy
            if (
                self.currentMaze[nnx][nny] == "#"
                or self.currentMaze[nnx][nny][0] == "$"
                or self.currentMaze[nnx][nny][0] == "*"
            ):
                print("Invalid move: Cannot push the stone")
                self.notify("Invalid move: Cannot push the stone")
                return

            if self.currentMaze[nnx][nny] == " ":
                self.currentMaze[nnx][nny] = "$" + self.currentMaze[nx][ny][1:]
            elif self.currentMaze[nnx][nny] == ".":
                self.currentMaze[nnx][nny] = "*" + self.currentMaze[nx][ny][1:]

            self.totalWeight += int(self.currentMaze[nx][ny][1:])

        if self.currentMaze[x][y] == "+":
            self.currentMaze[x][y] = "."
        else:
            self.currentMaze[x][y] = " "

        if self.currentMaze[nx][ny] == "." or self.currentMaze[nx][ny][0] == "*":
            self.currentMaze[nx][ny] = "+"
        else:
            self.currentMaze[nx][ny] = "@"

        self.playerPosition = (nx, ny)

        self.countSteps += 1
        self.stepText.set_text(f"Step: {self.countSteps}")
        self.weightText.set_text(f"Weight: {self.totalWeight}")
        self.costText.set_text(f"Cost: {self.countSteps + self.totalWeight}")

        if self.isWinning():
            if not self.hasWon:
                if self.choosenAlgorithm == "Manual":
                    self.notify("Congratulations! You win!")
                else:
                    self.notify("Algorithm wins!")
            self.hasWon = True
        else:
            self.hasWon = False

    def createMaze(self, edit=False):
        self.mazeText.hide()
        self.mazeDropdownMenu.hide()
        self.algorithmText.hide()
        self.algorithmDropDownMenu.hide()
        self.visualizeText.hide()
        self.runButton.hide()
        self.speedSlider.hide()
        self.speedText.hide()
        self.resetButton.hide()
        self.statText.hide()
        self.statBox.hide()
        self.stepText.hide()
        self.weightText.hide()
        self.costText.hide()
        self.generateText.show()
        self.mazeSizeSlider.show()
        self.mazeSizeSlider.sliding_button.hide()
        self.mazeSizeText.show()
        self.numStonesSlider.show()
        self.numStonesSlider.sliding_button.hide()
        self.numStonesText.show()
        self.randomButton.show()
        self.clearButton.show()
        self.objectText.show()
        self.objectDropdownMenu.show()
        self.cancelButton.show()
        self.editButton.hide()
        self.createButton.set_text("Save")

        self.isEditing = True
        self.grassPosition = None
        if edit:
            self.newMaze = [list(line) for line in self.mazeDatas[self.choosenMaze][1]]
            weightIndex = 0
            for i in range(len(self.newMaze)):
                for j in range(len(self.newMaze[0])):
                    if self.newMaze[i][j] == "$" or self.newMaze[i][j] == "*":
                        self.newMaze[i][j] += str(
                            self.mazeDatas[self.choosenMaze][0][weightIndex]
                        )
                        weightIndex += 1

            self.newMaze = self.centerMaze(self.newMaze, self.MAZE_CELL)
        elif self.newMaze is None:
            self.newMaze = [
                [
                    (
                        "#"
                        if i == 0
                        or i == self.MAZE_CELL - 1
                        or j == 0
                        or j == self.MAZE_CELL - 1
                        else " "
                    )
                    for j in range(self.MAZE_CELL)
                ]
                for i in range(self.MAZE_CELL)
            ]

    def cancelCreate(self):
        self.mazeText.show()
        self.mazeDropdownMenu.show()
        self.algorithmText.show()
        self.algorithmDropDownMenu.show()
        self.visualizeText.show()
        self.runButton.show()
        self.speedSlider.show()
        self.speedSlider.sliding_button.hide()
        self.speedText.show()
        self.resetButton.show()
        self.statText.show()
        self.statBox.show()
        self.stepText.show()
        self.weightText.show()
        self.costText.show()
        self.generateText.hide()
        self.mazeSizeSlider.hide()
        self.mazeSizeText.hide()
        self.numStonesSlider.hide()
        self.numStonesText.hide()
        self.randomButton.hide()
        self.clearButton.hide()
        self.objectText.hide()
        self.objectDropdownMenu.hide()
        self.cancelButton.hide()
        self.editButton.show()
        self.createButton.set_text("Create")

        self.isEditing = False
        self.grassPosition = None

    def placeObject(self):
        if self.choosenObject is None:
            return

        x, y = pygame.mouse.get_pos()

        if (
            x < self.SCREEN_WIDTH - self.MAZE_SIZE
            or x >= self.SCREEN_WIDTH
            or y < 0
            or y >= self.MAZE_SIZE
        ):
            return

        x, y = y // (self.MAZE_SIZE // self.MAZE_CELL), (
            x - self.SCREEN_WIDTH + self.MAZE_SIZE
        ) // (self.MAZE_SIZE // self.MAZE_CELL)

        if self.choosenObject != "Hill" and (
            x == 0 or x == self.MAZE_CELL - 1 or y == 0 or y == self.MAZE_CELL - 1
        ):
            return

        match self.choosenObject:
            case "Hill":
                self.newMaze[x][y] = "#"
            case "Land":
                self.newMaze[x][y] = " "
            case "Stone":
                randomWeight = random.randrange(1, 101)
                if self.newMaze[x][y][0] == "." or self.newMaze[x][y][0] == "*":
                    self.newMaze[x][y] = "*" + str(randomWeight)
                else:
                    self.newMaze[x][y] = "$" + str(randomWeight)
            case "Switch":
                if self.newMaze[x][y][0] == "$" or self.newMaze[x][y][0] == "*":
                    self.newMaze[x][y] = "*" + self.newMaze[x][y][1:]
                elif self.newMaze[x][y][0] == "@" or self.newMaze[x][y][0] == "+":
                    self.newMaze[x][y] = "+"
                else:
                    self.newMaze[x][y] = "."
            case "Player":
                if self.newMaze[x][y][0] == "." or self.newMaze[x][y][0] == "+":
                    self.newMaze[x][y] = "+"
                else:
                    self.newMaze[x][y] = "@"

    def saveMaze(self, fileName):
        newInputIndex = len(self.mazeDatas) + 1
        file = f"input-{newInputIndex}"
        if fileName:
            file += f"-{fileName}"
        file += ".txt"

        with open(f"Mazes/{file}", "w") as f:
            self.savedMaze = self.normalizeMaze(self.savedMaze)
            f.write(" ".join(map(str, self.savedWeights)) + "\n")
            f.write("\n".join(["".join(line) for line in self.savedMaze]))

        self.cancelCreate()
        self.newMaze = None

        self.readMaze(file, True)
        self.chooseMaze(newInputIndex - 1)
        self.updateMazeDropdownMenu()

    def chooseAlgorithm(self, index):
        self.choosenAlgorithm = index
        self.algorithmResult = None

    def chooseMaze(self, index):
        if index != self.choosenMaze:
            self.grassPosition = None
        self.choosenMaze = index
        self.currentMaze = [list(line) for line in self.mazeDatas[index][1]]
        self.playerDirection = 0
        maze = self.mazeDatas[self.choosenMaze][1]
        weightIndex = 0
        for i in range(len(maze)):
            for j in range(len(maze[0])):
                if maze[i][j] == "@" or maze[i][j] == "+":
                    self.playerPosition = (i, j)
                elif maze[i][j] == "$" or maze[i][j] == "*":
                    self.currentMaze[i][j] = maze[i][j] + str(
                        self.mazeDatas[self.choosenMaze][0][weightIndex]
                    )
                    weightIndex += 1

        self.algorithmResult = None
        self.countSteps = 0
        self.totalWeight = 0
        self.stepText.set_text(f"Steps: {self.countSteps}")
        self.weightText.set_text(f"Weight: {self.totalWeight}")
        self.costText.set_text(f"Cost: {self.countSteps + self.totalWeight}")

    def drawMaze(self):
        maze = self.centerMaze(self.currentMaze if not self.isEditing else self.newMaze)

        n = len(maze)
        cellSize = self.MAZE_SIZE // n

        activeCorner = [[False] * n for _ in range(n)]
        for i in range(1, n):
            for j in range(1, n):
                if maze[i][j] != "#":
                    continue

                count = 0
                for dx, dy in [(0, 0), (-1, 0), (0, -1), (-1, -1)]:
                    if maze[i + dx][j + dy] == "#":
                        count += 1

                if count == 4:
                    activeCorner[i][j] = True

        if self.grassPosition is None:
            self.grassPosition = [[None] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    if random.randrange(0, 5) == 0:
                        self.grassPosition[i][j] = (
                            random.randrange(0, 6) * 16,
                            random.randrange(5, 7) * 16,
                        )

        image = self.assets["hills"]
        for i in range(n):
            for j in range(n):
                position = (
                    self.SCREEN_WIDTH - self.MAZE_SIZE + j * cellSize,
                    i * cellSize,
                )

                if self.grassPosition[i][j] == None:
                    self.screen.blit(
                        pygame.transform.scale(
                            self.assets["grass"].subsurface((16, 16, 16, 16)),
                            (cellSize, cellSize),
                        ),
                        position,
                    )
                else:
                    self.screen.blit(
                        pygame.transform.scale(
                            self.assets["grass"].subsurface(
                                (
                                    self.grassPosition[i][j][0],
                                    self.grassPosition[i][j][1],
                                    16,
                                    16,
                                )
                            ),
                            (cellSize, cellSize),
                        ),
                        position,
                    )

        pygame.draw.rect(
            self.screen,
            (232, 207, 166),
            (self.SCREEN_WIDTH - self.MAZE_SIZE, 0, self.MAZE_SIZE, self.MAZE_SIZE),
            cellSize // 2,
        )

        if self.isEditing:
            for i in range(1, n):
                pygame.draw.line(
                    self.screen,
                    (210, 224, 119),
                    (self.SCREEN_WIDTH - self.MAZE_SIZE, i * cellSize - 1),
                    (self.SCREEN_WIDTH, i * cellSize - 1),
                    2,
                )
                pygame.draw.line(
                    self.screen,
                    (210, 224, 119),
                    (self.SCREEN_WIDTH - self.MAZE_SIZE + i * cellSize - 1, 0),
                    (
                        self.SCREEN_WIDTH - self.MAZE_SIZE + i * cellSize - 1,
                        self.MAZE_SIZE,
                    ),
                    2,
                )

        for i in range(n):
            for j in range(n):
                position = (
                    self.SCREEN_WIDTH - self.MAZE_SIZE + j * cellSize,
                    i * cellSize,
                )
                match maze[i][j][0]:
                    case "#":
                        bitmask = 1 << 4
                        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                            nx, ny = i + dx, j + dy
                            if 0 <= nx < n and 0 <= ny < n and maze[nx][ny] == "#":
                                bitmask |= 1 << ((dx + 1) * 3 + (dy + 1))

                        for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                            nx, ny = i + dx, j + dy
                            if 0 <= nx < n and 0 <= ny < n and activeCorner[nx][ny]:
                                bitmask |= 1 << ((2 * dx) * 3 + (2 * dy))

                        y, x = self.bf.getPosition(bitmask)
                        if y == 1 and x == 1 and self.grassPosition[i][j] != None:
                            x = self.grassPosition[i][j][0] // 16
                            y = self.grassPosition[i][j][1] // 16

                        self.screen.blit(
                            pygame.transform.scale(
                                image.subsurface((x * 16, y * 16, 16, 16)),
                                (cellSize, cellSize),
                            ),
                            position,
                        )
                    case " ":
                        pass
                    case "$":
                        self.screen.blit(
                            pygame.transform.scale(
                                self.assets["biom"].subsurface((128, 16, 16, 16)),
                                (cellSize, cellSize),
                            ),
                            position,
                        )

                        weightText = self.font.render(
                            f"{int(maze[i][j][1:])}",
                            True,
                            (0, 0, 0),
                        )
                        self.screen.blit(
                            weightText,
                            (
                                position[0]
                                + cellSize // 2
                                - weightText.get_width() // 2,
                                position[1]
                                + cellSize // 2
                                - weightText.get_height() // 2,
                            ),
                        )
                    case "@":
                        self.screen.blit(
                            pygame.transform.scale(
                                self.assets["player"].subsurface(
                                    (
                                        16,
                                        48
                                        * (
                                            0
                                            if self.isEditing
                                            else self.playerDirection
                                        )
                                        + 16,
                                        16,
                                        16,
                                    )
                                ),
                                (cellSize, cellSize),
                            ),
                            position,
                        )
                    case ".":
                        self.screen.blit(
                            pygame.transform.scale(
                                self.assets["furniture"].subsurface((0, 80, 16, 16)),
                                (cellSize, cellSize),
                            ),
                            position,
                        )
                    case "*":
                        self.screen.blit(
                            pygame.transform.scale(
                                self.assets["furniture"].subsurface((0, 80, 16, 16)),
                                (cellSize, cellSize),
                            ),
                            position,
                        )

                        self.screen.blit(
                            pygame.transform.scale(
                                self.assets["biom"].subsurface((128, 16, 16, 16)),
                                (cellSize, cellSize),
                            ),
                            position,
                        )

                        weightText = self.font.render(
                            f"{int(maze[i][j][1:])}",
                            True,
                            (84, 89, 89),
                        )
                        self.screen.blit(
                            weightText,
                            (
                                position[0]
                                + cellSize // 2
                                - weightText.get_width() // 2,
                                position[1]
                                + cellSize // 2
                                - weightText.get_height() // 2,
                            ),
                        )
                    case "+":
                        self.screen.blit(
                            pygame.transform.scale(
                                self.assets["furniture"].subsurface((0, 80, 16, 16)),
                                (cellSize, cellSize),
                            ),
                            position,
                        )

                        self.screen.blit(
                            pygame.transform.scale(
                                self.assets["player"].subsurface(
                                    (16, 48 * self.playerDirection + 16, 16, 16)
                                ),
                                (cellSize, cellSize),
                            ),
                            position,
                        )

    def centerMaze(self, maze, fixedSize=None):
        n = len(maze)
        m = len(maze[0])

        mazeSize = self.MAZE_CELL
        if fixedSize is not None:
            mazeSize = fixedSize
        else:
            for i in range(max(n, m), self.MAZE_CELL + 1):
                if self.MAZE_SIZE % i == 0:
                    mazeSize = i
                    break

        topPadding = (mazeSize - n) // 2
        leftPadding = (mazeSize - m) // 2
        bottomPadding = mazeSize - n - topPadding
        rightPadding = mazeSize - m - leftPadding

        maze = [
            ["#" for _ in range(leftPadding)]
            + line
            + ["#" for _ in range(rightPadding)]
            for line in maze
        ]
        maze = (
            [
                ["#" for _ in range(mazeSize + leftPadding + rightPadding)]
                for _ in range(topPadding)
            ]
            + maze
            + [
                ["#" for _ in range(mazeSize + leftPadding + rightPadding)]
                for _ in range(bottomPadding)
            ]
        )

        return maze

    def loadMaze(self):
        for file in os.listdir("Mazes"):
            if file.startswith("input-") and file.endswith(".txt"):
                with open(f"Mazes/{file}", "r") as f:
                    self.readMaze(file)

        self.mazeDatas.sort(key=lambda x: x[2])

    def readMaze(self, file, bypass=False):
        with open(f"Mazes/{file}", "r") as f:
            weights = list(map(int, f.readline().split()))
            maze = [list(line) for line in f.read().splitlines()]
            if bypass or self.validateMaze((weights, maze, file)):
                file = file[6:-4]
                self.fileToIndex[file] = len(self.mazeDatas)
                self.mazeDatas.append((weights, self.normalizeMaze(maze), file))

    def validateMaze(self, mazeData):
        try:
            weights, maze, file = mazeData
            print(f"Validating maze from file {file}:")

            for weight in weights:
                if weight < 1 or weight > 100:
                    print("Weight should be an integer between 1 and 100")
                    return False

            n = len(maze)
            m = len(maze[0])

            cntPlayers = 0
            cntStones = 0
            cntSwitches = 0
            playerPos = None
            for i in range(n):
                if len(maze[i]) != m:
                    print("All lines in maze should have the same length")
                    return False

                for j in range(m):
                    match maze[i][j]:
                        case "#":
                            pass
                        case " ":
                            pass
                        case "$":
                            cntStones += 1
                        case "@":
                            cntPlayers += 1
                            playerPos = (i, j)
                        case ".":
                            cntSwitches += 1
                        case "*":
                            cntStones += 1
                            cntSwitches += 1
                        case "+":
                            cntPlayers += 1
                            cntSwitches += 1
                            playerPos = (i, j)
                        case _:
                            print(f"Unknown character '{maze[i][j]}'")
                            return False

            if cntPlayers != 1:
                print("There should be exactly one player")
                self.notify("There should be exactly one player")
                return False

            if cntStones != cntSwitches:
                print("Number of stones and switches should be equal")
                self.notify("Number of stones and switches should be equal")
                return False

            if cntStones == 0:
                print("There should be at least one stone")
                self.notify("There should be at least one stone")
                return False

            if cntStones != len(weights):
                print("Number of stones and size of weight list should be equal")
                self.notify("Number of stones and size of weight list should be equal")
                return False

            queue = deque()
            visited = [[False] * m for _ in range(n)]
            queue.append(playerPos)
            visited[playerPos[0]][playerPos[1]] = True

            while queue:
                x, y = queue.popleft()
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < n
                        and 0 <= ny < m
                        and maze[nx][ny] != "#"
                        and not visited[nx][ny]
                    ):
                        visited[nx][ny] = True
                        queue.append((nx, ny))

            for i in range(n):
                for j in range(m):
                    if i == 0 or i == n - 1 or j == 0 or j == m - 1:
                        if visited[i][j]:
                            print("Maze should be surrounded by hills")
                            self.notify("Maze should be surrounded by hills")
                            return False

                    if maze[i][j] == "$":
                        if not visited[i][j]:
                            print("Stone should be reachable")
                            self.notify("Stone should be reachable")
                            return False

                    if maze[i][j] == ".":
                        if not visited[i][j]:
                            print("Switch should be reachable")
                            self.notify("Switch should be reachable")
                            return False
        except:
            print("Unknow error, please check the maze manually")
            return False

        print("No errors found")
        return True

    def normalizeMaze(self, maze):
        n = len(maze)
        m = len(maze[0])

        playerPos = [
            (x, y)
            for x in range(n)
            for y in range(m)
            if maze[x][y] == "@" or maze[x][y] == "+"
        ][0]
        queue = deque()
        visited = [[False] * m for _ in range(n)]
        queue.append(playerPos)
        visited[playerPos[0]][playerPos[1]] = True

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < n
                    and 0 <= ny < m
                    and maze[nx][ny] != "#"
                    and not visited[nx][ny]
                ):
                    visited[nx][ny] = True
                    queue.append((nx, ny))

        for i in range(n):
            for j in range(m):
                if not visited[i][j]:
                    maze[i][j] = "#"

        topBound = 0
        for i in range(n):
            if all(cell == "#" for cell in maze[i]):
                topBound = i
            else:
                break

        bottomBound = n - 1
        for i in range(n - 1, -1, -1):
            if all(cell == "#" for cell in maze[i]):
                bottomBound = i
            else:
                break

        leftBound = 0
        for j in range(m):
            if all(maze[i][j] == "#" for i in range(n)):
                leftBound = j
            else:
                break

        rightBound = m - 1
        for j in range(m - 1, -1, -1):
            if all(maze[i][j] == "#" for i in range(n)):
                rightBound = j
            else:
                break

        return [
            line[leftBound : rightBound + 1]
            for line in maze[topBound : bottomBound + 1]
        ]

    def updateMazeDropdownMenu(self):
        if self.mazeDropdownMenu is not None:
            self.mazeDropdownMenu.kill()

        self.mazeDropdownMenu = pygame_gui.elements.UIDropDownMenu(
            options_list=[f"{mazeData[2]}" for mazeData in self.mazeDatas],
            starting_option=f"{self.mazeDatas[-1][2]}",
            relative_rect=pygame.Rect((10, 50), (180, 30)),
            manager=self.manager,
            object_id="#maze_dropdown_menu",
        )

    def loadAssets(self):
        self.assets["icon"] = pygame.image.load("Assets/Icon.png")
        self.assets["grass"] = pygame.image.load("Assets/Tilesets/Grass.png")
        self.assets["hills"] = pygame.image.load("Assets/Tilesets/HillsFixed.png")
        self.assets["furniture"] = pygame.image.load("Assets/Objects/Furniture.png")
        self.assets["biom"] = pygame.image.load("Assets/Objects/Biom.png")
        self.assets["player"] = pygame.image.load("Assets/Characters/Charakter.png")

    def loadSettings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)

                self.visualizeSpeed = settings.get("visualize_speed", 1)
                self.choosenMaze = settings.get("choosen_maze", 0)
                self.choosenAlgorithm = settings.get("choosen_algorithm", "Manual")

        self.visualizeSpeed = (
            self.visualizeSpeed
            if self.visualizeSpeed is not None and self.visualizeSpeed in self.allSpeeds
            else 1
        )
        self.choosenMaze = (
            self.choosenMaze
            if self.choosenMaze is not None and self.choosenMaze < len(self.mazeDatas)
            else 0
        )
        self.choosenAlgorithm = (
            self.choosenAlgorithm
            if self.choosenAlgorithm is not None
            and self.choosenAlgorithm in ["Manual", "BFS", "DFS", "UCS", "A*"]
            else "Manual"
        )

    def saveSettings(self):
        with open("settings.json", "w") as f:
            settings = {
                "visualize_speed": self.visualizeSpeed,
                "choosen_maze": self.choosenMaze,
                "choosen_algorithm": self.choosenAlgorithm,
            }

            json.dump(settings, f)
