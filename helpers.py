white = [1.0, 1.0, 1.0, 1.0]
grey = [0.5, 0.5, 0.5, 1.0]
black = [0.0, 0.0, 0.0, 1.0]
red = [0.5, 0.0, 0.0, 1.0]
green = [0.0, 0.5, 0.0, 1.0]
blue = [0.0, 0.0, 0.5, 1.0]
yellow = [0.5, 0.5, 0.0, 1.0]
purple = [0.5, 0.0, 0.5, 1.0]

clear = [0.0, 0.0, 0.0, 0.0]
menu_bg_color = [0.15, 0.15, 0.15, 1.0]
game_bg_color = [0.1, 0.4, 0.6, 1.0]
terrain_color = green
terrain_border_color = [0,0.7,0,1.0]


def pr(*args):
    print(args)

def tile_face_size(x,y):
    if x is not None:
        return x,y
    else:
        return (0,0)
