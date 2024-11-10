# Source: https://github.com/AlliBalliBaba/Sokoban-Level-Generator
# Author: Alexander Stecher

import random

canvas_x = 600
canvas_y = 600

### utils.py ###


# Create a 2D array filled with content
def array2d(x_size, y_size, content):
    return [[content for _ in range(y_size)] for _ in range(x_size)]


# Return a random integer between min (included) and max (excluded)
def random_int(min_val, max_val):
    return random.randint(min_val, max_val - 1)


# Find all permutations between elements of two lists of equal size
def find_permutations(a_list, b_list):
    permutations = []
    perm(a_list, b_list, [], permutations)
    return permutations


def perm(a_list, b_list, permutation, permutations):
    for j in range(len(b_list)):
        new_per = permutation + [(a_list[0], b_list[j])]
        if len(a_list) > 1:
            new_list = b_list[:j] + b_list[j + 1 :]
            perm(a_list[1:], new_list, new_per, permutations)
        else:
            permutations.append(new_per)


# Add to sorted array via binary search
def add_to_sorted_array(array, element, compare_function):
    index = binary_search(array, element, compare_function)
    if index < 0:
        index = -index - 1
    array.insert(index, element)


# Binary search in sorted array
def binary_search(array, element, compare_function):
    low, high = 0, len(array) - 1
    while low <= high:
        mid = (low + high) // 2
        cmp = compare_function(element, array[mid])
        if cmp > 0:
            low = mid + 1
        elif cmp < 0:
            high = mid - 1
        else:
            return mid
    return -low - 1


# Comparison function for elements based on 'f' attribute
def f_comparer(element1, element2):
    return element1.f - element2.f


# Check if a point is within the boundaries of a 2D array
def check_boundaries(arr2d, x, y):
    return 0 <= x < len(arr2d) and 0 <= y < len(arr2d[0])


# Function to prevent arrow keys from scrolling (not applicable in Python)
# This would be implemented in a GUI framework, if needed.

### pathfinder.py ###

wall_cost = 100  # Cost for traversing a wall
path_cost = 1  # Cost for traversing an unoccupied node
player_path_cost = -1  # Player cost for traversing an unoccupied node
box_cost = 10000  # Cost for traversing an occupied node


class Node:
    # Initialize each node as an unoccupied wall
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.f = 0  # Path cost estimation
        self.cost = 0  # Path cost
        self.closed = False  # Variable for pathfinding
        self.checked = False  # Variable for pathfinding
        self.wall = True  # Check if node has a wall
        self.occupied = False  # Check if node is occupied (for pathfinding)
        self.parent = None  # Node parent for pathfinding
        self.has_box = False  # Check if node has a box
        self.used = False  # Variable for optimizing


class Pathfinder:
    def __init__(self, level, start_x, start_y, end_x, end_y):
        self.level = level
        self.nodes = self.level.nodes
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.open = []
        self.closed = []

    def return_path(self, is_box_path):
        self.open.append(self.nodes[self.start_x][self.start_y])

        while self.open:
            this_node = self.open.pop(0)

            if this_node.x == self.end_x and this_node.y == self.end_y:
                self.open.append(this_node)
                return self.sum_path(this_node)
            else:
                this_node.closed = True
                self.closed.append(this_node)

                self.check_neighbor(
                    this_node.x + 1, this_node.y, this_node, is_box_path
                )
                self.check_neighbor(
                    this_node.x - 1, this_node.y, this_node, is_box_path
                )
                self.check_neighbor(
                    this_node.x, this_node.y + 1, this_node, is_box_path
                )
                self.check_neighbor(
                    this_node.x, this_node.y - 1, this_node, is_box_path
                )

        print("No path found")
        return self.sum_path(this_node)

    def sum_path(self, end_node):
        path = []
        cost = end_node.cost
        while end_node.parent:
            path.insert(0, end_node)
            end_node = end_node.parent
        self.reset_nodes()
        return path, cost

    def check_neighbor(self, x, y, parent, is_box_path):
        if check_boundaries(self.nodes, x, y):
            this_node = self.nodes[x][y]
            if not this_node.closed and not this_node.checked:
                this_node.cost = self.calculate_cost(this_node, parent, is_box_path)
                this_node.f = this_node.cost + abs(x - self.end_x) + abs(y - self.end_y)
                this_node.parent = parent
                this_node.checked = True
                self.add_to_open_list(this_node)
            elif not this_node.closed:
                cost = self.calculate_cost(this_node, parent, is_box_path)
                if (
                    cost < this_node.cost
                    and this_node.parent
                    and this_node.parent.parent
                ):
                    this_node.cost = cost
                    this_node.f = (
                        this_node.cost + abs(x - self.end_x) + abs(y - self.end_y)
                    )
                    this_node.parent = parent

    def calculate_cost(self, node, parent, is_box_path):
        temp_cost = 0
        if node.occupied:
            temp_cost = parent.cost + box_cost
        else:
            if is_box_path:
                temp_cost = parent.cost + (wall_cost if node.wall else path_cost)
            else:
                temp_cost = parent.cost + (wall_cost if node.wall else player_path_cost)

        # Player path adjustments for moving around a box
        if is_box_path and parent.parent:
            cost1, cost2 = self.calculate_detour_costs(node, parent)
            temp_cost += min(cost1, cost2)

        # Further optimization for used nodes
        if node.used:
            temp_cost -= 5
        return temp_cost

    def calculate_detour_costs(self, node, parent):
        # Define detour paths around the box based on relative position
        cost1 = cost2 = 0
        if node.x - 1 == parent.x:
            if node.y - 1 == parent.parent.y:
                cost1 = self.node_cost(node.x - 2, node.y) + self.node_cost(
                    node.x - 2, node.y - 1
                )
                cost2 = (
                    self.node_cost(node.x, node.y - 1)
                    + self.node_cost(node.x, node.y + 1)
                    + self.node_cost(node.x - 1, node.y + 1)
                    + self.node_cost(node.x - 2, node.y + 1)
                    + self.node_cost(node.x - 2, node.y)
                )
            else:
                cost1 = self.node_cost(node.x - 2, node.y) + self.node_cost(
                    node.x - 2, node.y + 1
                )
                cost2 = (
                    self.node_cost(node.x, node.y - 1)
                    + self.node_cost(node.x, node.y + 1)
                    + self.node_cost(node.x - 1, node.y - 1)
                    + self.node_cost(node.x - 2, node.y - 1)
                    + self.node_cost(node.x - 2, node.y)
                )
        # Similar structure for other cases...
        return cost1, cost2

    def node_cost(self, x, y):
        if check_boundaries(self.nodes, x, y):
            node = self.nodes[x][y]
            return (
                box_cost
                if node.occupied
                else (wall_cost if node.wall else player_path_cost)
            )
        else:
            return box_cost

    def reset_nodes(self):
        for node in self.open + self.closed:
            node.checked = False
            node.closed = False
            node.parent = None
            node.cost = 0
        self.open.clear()
        self.closed.clear()

    def add_to_open_list(self, node):
        # Insert node in sorted order based on 'f' value
        self.open.append(node)
        self.open.sort(key=lambda n: n.f)


### level.py ###


class Box:
    def __init__(self, x, y, button):
        self.x = x
        self.y = y
        self.px = x
        self.py = y
        self.placed = False
        self.solve_button = button

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def place_exactly(self, x, y):
        self.x = x
        self.y = y
        self.px = x
        self.py = y


class Button:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Level:
    def __init__(self, x_size, y_size, num_boxes):
        self.xSize = x_size
        self.ySize = y_size
        self.buttons = []
        self.boxes = []
        self.ghostboxes = []
        self.blockSize = canvas_x / x_size
        self.solveCounter = num_boxes
        self.savedPositions = []
        self.trash = False

        # Initialize nodes for pathfinding
        self.nodes = [[Node(i, j) for j in range(y_size)] for i in range(x_size)]

        # Randomly place boxes and buttons
        self.define_allowed_spots()
        self.place_objects(num_boxes)

    def place_objects(self, num_boxes):
        # Place buttons
        for _ in range(num_boxes):
            pos = self.random_spot()
            if pos:
                self.buttons.append(Button(pos[0], pos[1]))

        # Place boxes
        for i in range(num_boxes):
            pos = self.random_spot()
            if pos:
                box = Box(pos[0], pos[1], self.buttons[i])
                self.boxes.append(box)
                self.nodes[pos[0]][pos[1]].has_box = True

        # Place player
        pos = self.random_spot()
        if pos is None:
            pos = [self.buttons[0].x, self.buttons[0].y]
        self.set_player_pos(pos[0], pos[1])
        self.player_start_x = self.playerX
        self.player_start_y = self.playerY

    def define_allowed_spots(self):
        self.allowedSpots = [
            self.nodes[i][j]
            for i in range(2, len(self.nodes) - 2)
            for j in range(2, len(self.nodes[0]) - 2)
        ]

    def random_spot(self):
        if self.allowedSpots:
            rand_index = random.randint(0, len(self.allowedSpots) - 1)
            x, y = self.allowedSpots[rand_index].x, self.allowedSpots[rand_index].y
            self.allowedSpots.pop(rand_index)
            self.nodes[x][y].wall = False
            if self.blockaded(x, y):
                return self.random_spot()
            else:
                return [x, y]
        return None

    def rip(self, amount):
        for _ in range(amount):
            if self.allowedSpots:
                self.random_spot()

    def set_player_pos(self, x, y):
        self.playerX = x
        self.playerY = y

    def blockaded(self, x, y):
        if self.nodes[x + 1][y].has_box:
            if (self.nodes[x + 1][y + 1].has_box and self.nodes[x][y + 1].has_box) or (
                self.nodes[x + 1][y - 1].has_box and self.nodes[x][y - 1].has_box
            ):
                return True
        if self.nodes[x - 1][y].has_box:
            if (self.nodes[x - 1][y - 1].has_box and self.nodes[x][y - 1].has_box) or (
                self.nodes[x - 1][y + 1].has_box and self.nodes[x][y + 1].has_box
            ):
                return True
        return False


### generator.py ###


def generate_paths(lvl):
    steps = 0
    # Create ghost boxes for solving
    ghost_boxes = copy_boxes(lvl, used=False)
    # Push the ghost boxes towards the buttons
    while lvl.solveCounter > 0:
        # Calculate the paths from all boxes to their buttons
        box_paths = calculate_box_paths(lvl, ghost_boxes)

        # Calculate the player paths to all boxes and choose the lowest-cost path
        player_paths = calculate_player_paths(lvl, ghost_boxes, box_paths)
        best_path = player_paths[1]
        player_path = player_paths[0][best_path][0]
        box_path = box_paths[best_path][0]

        # Remove all walls on the player's path
        for node in player_path:
            node.wall = False
            if getattr(node, "occupied", False):
                lvl.trash = True

        # Push the box into the solving direction
        this_box = ghost_boxes[best_path]
        current_node = box_path[0]
        diff_x = current_node.x - this_box.x
        diff_y = current_node.y - this_box.y
        stop = 0

        # If the box path is longer than 1, push until there is a turn
        if len(box_path) > 1:
            for i in range(1, len(box_path)):
                next_node = box_path[i]
                if (
                    diff_x == next_node.x - current_node.x
                    and diff_y == next_node.y - current_node.y
                ):
                    current_node = next_node
                else:
                    stop = i - 1
                    break

        # Remove all walls on the box's path
        for i in range(stop + 1):
            box_path[i].wall = False

        # Set new player and box positions
        lvl.nodes[this_box.x][this_box.y].occupied = False
        this_box.set_position(box_path[stop].x, box_path[stop].y)
        lvl.nodes[this_box.x][this_box.y].occupied = True
        lvl.set_player_pos(this_box.x - diff_x, this_box.y - diff_y)

        # Check if the moved box is on the button
        if (
            this_box.x == this_box.solve_button.x
            and this_box.y == this_box.solve_button.y
        ):
            this_box.placed = True
            lvl.solveCounter -= 1
            ghost_boxes.pop(best_path)

        steps += 1
        if steps > 4000:
            lvl.trash = True
            break

    # Reset player position
    lvl.set_player_pos(lvl.player_start_x, lvl.player_start_y)


def copy_boxes(lvl, used):
    new_boxes = []
    for box in lvl.boxes:
        new_box = Box(box.x, box.y, box.solve_button)
        new_boxes.append(new_box)
        lvl.nodes[box.x][box.y].occupied = True
        lvl.nodes[box.x][box.y].used = used
    return new_boxes


def calculate_box_paths(lvl, ghost_boxes):
    box_paths = []
    for box in ghost_boxes:
        lvl.nodes[box.x][box.y].occupied = False
        solver = Pathfinder(lvl, box.x, box.y, box.solve_button.x, box.solve_button.y)
        box_paths.append(solver.return_path(is_box_path=True))
        lvl.nodes[box.x][box.y].occupied = True
    return box_paths


def calculate_player_paths(lvl, ghost_boxes, box_paths):
    player_paths = []
    best_path = -1
    lowest_cost = float("inf")
    for i, box in enumerate(ghost_boxes):
        new_x, new_y = box.x, box.y
        if box_paths[i][0][0].x == box.x + 1:
            new_x -= 1
        elif box_paths[i][0][0].x == box.x - 1:
            new_x += 1
        elif box_paths[i][0][0].y == box.y + 1:
            new_y -= 1
        else:
            new_y += 1

        solver = Pathfinder(lvl, lvl.playerX, lvl.playerY, new_x, new_y)
        player_path = solver.return_path(is_box_path=False)
        player_paths.append(player_path)

        if player_path[1] < lowest_cost:
            lowest_cost = player_path[1]
            best_path = i

    return player_paths, best_path


### optimizer.py ###

opt_path_cost = 4  # Optimizer box path cost
opt_player_cost = 4  # Optimizer player path cost


def optimize_lvl(lvl, iterations):
    max_unnecessary = []
    min_destroy_wall = []
    best_path = 0
    steps = 0
    lvl.playerX = lvl.player_start_x
    lvl.playerY = lvl.player_start_y

    global player_path_cost, path_cost
    temp_player_cost = player_path_cost
    player_path_cost = opt_player_cost

    # Free the button positions
    for button in lvl.buttons:
        lvl.nodes[button.x][button.y].occupied = False
        lvl.nodes[button.x][button.y].used = True

    # Solve the level randomly and check if nodes weren't visited
    for _ in range(iterations):
        ghost_boxes = copy_boxes(lvl, True)
        solve_counter = len(ghost_boxes)
        destroy_wall = []
        trash = False
        while solve_counter > 0:
            temp_cost = path_cost
            path_cost = random.randint(-2, opt_path_cost)

            box_paths = calculate_box_paths(lvl, ghost_boxes)
            path_cost = temp_cost

            player_paths = calculate_player_paths(lvl, ghost_boxes, box_paths)[0]
            best_path = random.randint(0, len(player_paths) - 1)
            player_path = player_paths[best_path][0]
            box_path = box_paths[best_path][0]

            # Mark all nodes the player visited
            for node in player_path:
                node.used = True
                if node.wall:
                    destroy_wall.append(node)

            # Push the box in the solving direction until there is a turn
            this_box = ghost_boxes[best_path]
            current_node = box_path[0]
            diff_x = current_node.x - this_box.x
            diff_y = current_node.y - this_box.y

            stop = 0
            if len(box_path) > 1:
                for i in range(1, len(box_path)):
                    next_node = box_path[i]
                    if (
                        diff_x == next_node.x - current_node.x
                        and diff_y == next_node.y - current_node.y
                    ):
                        current_node = next_node
                    else:
                        stop = i - 1
                        break

            # Mark nodes on the box's path
            for i in range(stop + 1):
                box_path[i].used = True
                if box_path[i].wall:
                    destroy_wall.append(box_path[i])

            # Set and mark new player and box positions
            lvl.nodes[this_box.x][this_box.y].occupied = False
            this_box.set_position(box_path[stop].x, box_path[stop].y)
            lvl.nodes[this_box.x][this_box.y].occupied = True
            lvl.set_player_pos(this_box.x - diff_x, this_box.y - diff_y)

            # Check if the moved box is on the button
            if (
                this_box.x == this_box.solve_button.x
                and this_box.y == this_box.solve_button.y
            ):
                this_box.placed = True
                solve_counter -= 1
                ghost_boxes.pop(best_path)

            steps += 1
            if steps > 10000:
                trash = True
                break

        # Reset player position
        lvl.set_player_pos(lvl.player_start_x, lvl.player_start_y)
        lvl.nodes[lvl.playerX][lvl.playerY].used = True

        # Check if a node is unnecessary
        unnecessary = []
        for row in lvl.nodes:
            for node in row:
                if not node.wall and not node.used:
                    unnecessary.append(node)
                node.used = False
                node.occupied = False

        if not trash and len(unnecessary) - len(destroy_wall) > len(
            max_unnecessary
        ) - len(min_destroy_wall):
            max_unnecessary = unnecessary
            min_destroy_wall = destroy_wall

    # Remove the unnecessary free spaces
    for node in max_unnecessary:
        node.wall = True
    for node in min_destroy_wall:
        node.wall = False
    player_path_cost = temp_player_cost
    print(f"{len(max_unnecessary)} hills added, {len(min_destroy_wall)} hills removed")


def optimize_lvl2(lvl, iterations):
    box_permutations = find_permutations(lvl.boxes, lvl.buttons)
    temp_boxes = copy_boxes(lvl, False)

    for permutation in box_permutations:
        for j, (box, button) in enumerate(permutation):
            lvl.boxes[j] = Box(box.x, box.y, button)
        optimize_lvl(lvl, iterations)

    lvl.boxes = temp_boxes


def low_cost(value):
    return value[1] < 50


### playercontrols.py ###

# Set up necessary variables
active = True
win = False
in_game = False
current_lvl = None  # This should be assigned to the level object
active_spots = []
counter = 0


# Handle key press events
# def key_pressed(event):
#     global win, in_game
#     if active:
#         if event.key == pygame.K_LEFT:
#             go_left()
#         elif event.key == pygame.K_RIGHT:
#             go_right()
#         elif event.key == pygame.K_UP:
#             go_up()
#         elif event.key == pygame.K_DOWN:
#             go_down()
#         elif event.key == pygame.K_BACKSPACE:
#             revert_step()

#     if event.key == pygame.K_RETURN and (win or not in_game):
#         new_level()


# Handle key typed events (for key 'z')
# def key_typed(event):
#     if event.unicode == "z":
#         revert_step()


def go_right():
    x, y = current_lvl.player_x, current_lvl.player_y
    check_positions(x, y, x + 1, y, x + 2, y)


def go_left():
    x, y = current_lvl.player_x, current_lvl.player_y
    check_positions(x, y, x - 1, y, x - 2, y)


def go_up():
    x, y = current_lvl.player_x, current_lvl.player_y
    check_positions(x, y, x, y - 1, x, y - 2)


def go_down():
    x, y = current_lvl.player_x, current_lvl.player_y
    check_positions(x, y, x, y + 1, x, y + 2)


# Check the position for walls and boxes, move the player if possible
def check_positions(prev_x, prev_y, x, y, next_x, next_y):
    nodes = current_lvl.nodes
    if check_boundaries(nodes, x, y) and not nodes[x][y].wall:
        if not nodes[x][y].has_box:
            # Move player
            current_lvl.set_player_pos(x, y)
            add_activity(prev_x, prev_y, None)
            add_activity(x, y, None)
            save_position(prev_x, prev_y, None, 0, 0)
        elif (
            check_boundaries(nodes, next_x, next_y)
            and not nodes[next_x][next_y].wall
            and not nodes[next_x][next_y].has_box
        ):
            # Move player
            current_lvl.set_player_pos(x, y)
            add_activity(prev_x, prev_y, None)
            add_activity(x, y, None)

            # Move box
            box = get_box(x, y)
            box.set_position(next_x, next_y)
            box.placed = get_button(next_x, next_y)
            nodes[x][y].has_box = False
            nodes[next_x][next_y].has_box = True
            add_activity(next_x, next_y, box)
            save_position(prev_x, prev_y, box, x, y)

            if box.placed:
                check_win()

    # Hide optimize button (specific to your application)
    # pygame equivalent to hide button not shown; customize per UI library


# Revert the last step
def revert_step():
    if current_lvl.saved_positions:
        positions = current_lvl.saved_positions.pop()
        current_lvl.set_player_pos(positions[0], positions[1])
        px, py = current_lvl.player_x, current_lvl.player_y

        if positions[2] is not None:
            this_box = positions[2]
            current_lvl.nodes[this_box.x][this_box.y].has_box = False
            this_box.place_exactly(positions[3], positions[4])
            this_box.placed = get_button(this_box.x, this_box.y)
            current_lvl.nodes[this_box.x][this_box.y].has_box = True

    # draw_all()


# Refresh drawing at a node for 30 frames
def add_activity(x, y, box):
    active_spots.append([30, x, y, box])


# Save box and player positions for reverting
def save_position(player_x, player_y, box, box_x, box_y):
    current_lvl.saved_positions.append([player_x, player_y, box, box_x, box_y])


# Return the box object at a position
def get_box(x, y):
    for box in current_lvl.boxes:
        if box.x == x and box.y == y:
            return box
    return None


# Check if a button is at a position
def get_button(x, y):
    for button in current_lvl.buttons:
        if button.x == x and button.y == y:
            return True
    return False


# Check if all boxes are placed
def check_win():
    global win, counter
    if all(box.placed for box in current_lvl.boxes):
        counter = 8
        win = True
        current_lvl.saved_positions = []


### index.py ###

current_lvl = None
counter = 0
box_number = 0
level_number = 0
level_size = 0
active = False
win = False
in_game = True
swap = False

# # load assets
# def preload():
#     load_all_images()

# # setup canvas
# def setup():
#     canvas = create_canvas(canvas_x, canvas_y)
#     canvas.parent('canvas1')
#     document.getElementById("optimize_button").style.visibility = "hidden"
#     display_html_values()
#     background(0)
#     prevent_arrow_key_scroll()
#     draw_only_walls()


# start new game
def start_game():
    global level_number, in_game
    level_number = 0
    in_game = False
    new_level()


# generate random level
def random_level():
    global level_number, in_game
    level_number = 0
    in_game = False
    new_level()


# optimize the level
def optimize(iterations):
    optimize_lvl(current_lvl, iterations)
    # draw_all()


# generate a new level
def new_level():
    global current_lvl, level_number, active, win, active_spots
    if in_game:
        random_values()
    else:
        read_html_values()

    # set_html_values()
    print(
        f"Generating a maze of size {level_size}x{level_size} with {box_number} stones"
    )
    current_lvl = Level(level_size, level_size, box_number)
    current_lvl.rip(random_int(-2, 5))
    generate_paths(current_lvl)

    if current_lvl.trash:
        print("Trash maze, proceed to generate a new one")
        new_level()
    else:
        level_number += 1
        active_spots = []
        # document.getElementById("optimize_button").style.visibility = "visible"

        if in_game and box_number < 6:
            optimize(random_int(-1000, 1000))

        active = True
        win = False
        # draw_all()


# called every frame
def draw():
    global counter, swap, active
    if active:
        # draw_active_spots()
        px = (px + current_lvl.player_x) * 0.5
        py = (py + current_lvl.player_y) * 0.5
        # draw_player(current_lvl)

        if win and counter >= 30:
            active = False
        elif counter >= 30:
            counter = 0
            swap = not swap
        counter += 1
    elif win:
        # draw_win()
        pass


# read slider values
def read_html_values():
    global level_size, box_number
    # level_size = int(document.getElementById("size_slider").value)
    # box_number = int(document.getElementById("num_slider").value)

    if box_number * 2 > (level_size - 4) * (level_size - 4) - 2:
        box_number = int(((level_size - 4) * (level_size - 4) - 2) / 2)


# # display slider values
# def display_html_values():
#     document.getElementById("size_txt").innerHTML = f"level size: {document.getElementById('size_slider').value}"
#     document.getElementById("box_txt").innerHTML = f"number of boxes: {document.getElementById('num_slider').value}"

# # set slider values
# def set_html_values():
#     document.getElementById("size_slider").value = level_size
#     document.getElementById("num_slider").value = box_number
#     display_html_values()


# set level_size and box_number randomly
def random_values():
    global level_size, box_number
    random_value = random.random()

    if random_value <= 0.1:
        level_size = random_int(7, 9)
        box_number = random_int(2, 4)
    elif random_value <= 0.3:
        level_size = random_int(8, 12)
        box_number = 3
    elif random_value <= 0.7:
        level_size = random_int(9, 13)
        box_number = 4
    elif random_value <= 0.9:
        level_size = random_int(9, 14)
        box_number = 5
    elif random_value <= 0.96:
        level_size = random_int(16, 20)
        box_number = random_int(4, 8)
    else:
        level_size = random_int(9, 16)
        box_number = random_int(6, 14)


# generate random level
def generate_maze(maze_size, num_boxes):
    global level_size, box_number
    level_size = maze_size
    box_number = num_boxes
    start_game()

    maze = [[" "] * current_lvl.xSize for _ in range(current_lvl.ySize)]
    for row in current_lvl.nodes:
        for node in row:
            maze[node.x][node.y] = "#" if node.wall else " "

    for box in current_lvl.boxes:
        maze[box.x][box.y] = "$" + str(random.randrange(1, 101))

    for button in current_lvl.buttons:
        maze[button.x][button.y] = "."

    maze[current_lvl.playerX][current_lvl.playerY] = "@"

    return maze
