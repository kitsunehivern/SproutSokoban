class BitmaskReferences:
    grid = None
    position = {}

    def __init__(self):
        with open("Assets/Tilesets/BitmaskReferences.txt", "r") as f:
            self.grid = [list(map(int, line.split())) for line in f.read().splitlines()]

        for i in range(0, len(self.grid), 3):
            for j in range(0, len(self.grid[0]), 3):
                if self.grid[i + 1][j + 1] != 1:
                    continue

                bitmask = 0
                for k in range(3):
                    for l in range(3):
                        bitmask |= self.grid[i + k][j + l] << (k * 3 + l)

                if bitmask in self.position:
                    print(
                        f"Duplicate bitmask {bitmask} at {i // 3}, {j // 3} and {self.position[bitmask]}"
                    )

                self.position[bitmask] = (i // 3, j // 3)

    def getPosition(self, bitmask):
        return self.position[bitmask]
