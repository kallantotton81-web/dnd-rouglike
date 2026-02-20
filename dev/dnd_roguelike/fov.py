import math

def compute_fov(game_map, x, y, radius):
    # Reset visibility
    for column in game_map.tiles:
        for tile in column:
            tile.visible = False

    # Raycasting FOV
    for i in range(360):
        rad = math.radians(i)
        dx = math.cos(rad)
        dy = math.sin(rad)

        px = float(x)
        py = float(y)

        for _ in range(radius):
            px += dx
            py += dy

            ix, iy = int(round(px)), int(round(py))

            if ix < 0 or ix >= game_map.width or iy < 0 or iy >= game_map.height:
                break

            game_map.tiles[ix][iy].visible = True
            game_map.tiles[ix][iy].explored = True

            if game_map.tiles[ix][iy].block_sight:
                break

    # Player position is always visible
    game_map.tiles[x][y].visible = True
    game_map.tiles[x][y].explored = True
