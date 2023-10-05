
class Level(object):
    level_seed = None
    tile_set = 'CCVVVVVVVVVAAAAAFFFFFSS'
    
class Level1(Level):
    id = 1
    map = '''
        ppppp
        pppppp
        ppppppp
        pppppppp
        ppppppppp
        pppppppp
        ppppppp
        pppppp
        ppppp
        '''
    start = (4,4)
    start_tile = 'C'
    tile_set = 'CCVVVVVVVVVAAAAAFFFFFSS'

class Level2(Level):
    id = 2
    map = '''
        ppppp
        pmmmpp
        pmmmmpp
        pmwmmmpp
        pfwffmmpp
        ppwfffpp
        ppwwffp
        pppwwf
        ppppw
        '''
    start = (4,4)
    start_tile = 'C'

class Level3(Level):
    id = 3
    map = '''
        mmmmm
        mppppm
        mpppppm
        mpfwwfpm
        mpfwwwfpm
        mpfwwfpm
        mpppppm
        mppppm
        mmmmm
        '''
    start = (4,2)
    start_tile = 'C'
