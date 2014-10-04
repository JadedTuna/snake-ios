import collections, random, scene, time

GROW_PER_APPLE = 10
CELL = scene.Size(16, 16)
SIZE = scene.Size(34, 34)

def convert(dict):
    """ Subdivides all the value in a dict by 255
        to make them Pythonista compatible."""
    return {k:tuple([i/255. for i in v]) for k, v in dict.items()}

COLORS = convert({
    "mbg":   (  0,   0,   0),
    "bg":    ( 30,  40,  50),
    "walls": (119, 136, 153),
    "snake": ( 50, 205,  50),
    "head":  (  0, 100,   0),
    "apple": (255,  99,  71),
})

dir_opp = collections.namedtuple('dir_opp', 'direction opposite')
UDLR = {
    'up'    : dir_opp((+0, +1), 'down'),
    'down'  : dir_opp((+0, -1), 'up'),
    'left'  : dir_opp((-1, +0), 'right'),
    'right' : dir_opp((+1, +0), 'left')
}

def make_levels():
    w, h = SIZE
    r = range
    levels = [
        ({(w//2,i) for i in r(h//2-3)}|{(w//2,i) for i in r(h//2+3,h)}),
        ({(w//4,i) for i in r(3*h//5)}|{(3*w//4,i) for i in r(2*h//5,h)}),
        ({(w//2,i) for i in r(5,h-5)}|{(i,h//2) for i in r(3,w//2-3)}|
            {(i+w//2+3, h//2) for i in r(3,w//2-3)})]
    return levels
LEVELS = make_levels()

class State (object):
    def __init__(self, scene, name):
        self.scene = scene
        self.name = name
        self.size = self.scene.size

    def draw(self):
        pass

    def touch_began(self, touch):
        pass

    def touch_moved(self, touch):
        pass

    def touch_ended(self, touch):
        pass

class GState (State):
    def __init__(self, *args):
        State.__init__(self, *args)
        self.font_size = 20 if self.size.w < 700 else 50

    def draw_text_center(self, text):
        x = self.size.w/2.
        y = self.size.h/2.
        scene.text(text, "Monofur", self.font_size, x, y)

class MenuState (GState):
    def __init__(self, in_scene):
        GState.__init__(self, in_scene, "Menu")

    def draw(self):
        self.draw_text_center("Touch to play")

    def touch_ended(self, touch):
        self.scene.cstate = "game"

class Apple (object):
    def __init__(self, walls, snake):
        self.snake = snake
        self.walls = walls
        self.respawn()

    def random_pos(self):
        return scene.Point(random.randrange(0, SIZE.w),
                           random.randrange(0, SIZE.h))

    def respawn(self):
        obst = self.snake.body + self.walls
        while True:
            pos = self.random_pos()
            if not pos.as_tuple() in obst:
                break
        self.pos = pos

    def draw(self, state):
        scene.fill(*COLORS["apple"])
        state.draw_cell(*self.pos)

class Snake (object):
    def __init__(self):
        self.body = [(10, 25), (10, 24)]
        self.speed = 8.
        self.direction = "up"
        self.growing = 0
        self.dead  = False
        self.timer = time.time()

    def update(self, state):
        now = time.time()
        if not self.dead and now - self.timer >= 1/self.speed:
            self.timer = now
            pos = self.calc_new_segment()
            if state.apple.pos == pos:
                state.apple.respawn()
                self.growing += GROW_PER_APPLE
                state.score += 1
            tpos = pos.as_tuple()
            if tpos in self.body + state.walls:
                self.dead = True
            self.body.insert(0, tpos)
            if self.growing:
                self.growing -= 1
            else:
                self.body.pop()

    def calc_new_segment(self):
        cx, cy = self.body[0]
        px, py = UDLR[self.direction].direction  # DIRECTIONS[self.direction]
        return scene.Point(cx + px, cy + py)

    def change_direction(self, axis, val):
        if val < 0:
            direction = {"x": "left", "y": "down"}[axis]
        else:
            direction = {"x": "right", "y": "up"}[axis]
        if self.direction != UDLR[direction].opposite:  # OPPOSITES[direction]:
            self.direction = direction

    def draw(self, state):
        scene.fill(*COLORS["snake"])
        for segment in self.body[1:]:
            state.draw_cell(*segment)
        scene.fill(*COLORS["head"])
        state.draw_cell(*self.body[0])

class GameState (GState):
    def __init__(self, in_scene):
        GState.__init__(self, in_scene, "Game")
        self.walls = self.create_level()
        self.snake = Snake()
        self.apple = Apple(self.walls, self.snake)
        w = SIZE.w * CELL.w
        h = SIZE.h * CELL.h
        x = in_scene.size.w/2 - w/2
        y = in_scene.size.h/2 - h/2
        self.bounds = scene.Rect(x, y, w, h)
        self.score  = 0
        text_width  = scene.render_text("Score:", "Monofur", 30)[1][1]
        self.scorepos = (10, 10 + self.size.h - text_width)

    def make_walls(self):
        walls = set()
        for i in range(-1, SIZE[0]+1):
            walls.add((i, -1))
            walls.add((i, SIZE[1]))
        for j in range(-1, SIZE[1]+1):
            walls.add((-1, j))
            walls.add((SIZE[0], j))
        return walls

    def create_level(self):
        return list(self.make_walls() | random.choice(LEVELS))

    def draw(self):
        scene.background(*COLORS["mbg"])
        scene.fill(*COLORS["bg"])
        scene.rect(*self.bounds)
        scene.fill(*COLORS["walls"])
        for wall in self.walls:
            self.draw_cell(*wall)
        self.apple.draw(self)
        self.snake.update(self)
        self.snake.draw(self)
        sx, sy = self.scorepos
        scene.text("Score: %d" % self.score, "Monofur", 30, sx, sy, 9)
        if self.snake.dead:
            self.draw_text_center("Game Over")

    def draw_cell(self, x, y):
        w, h = CELL
        scene.rect(self.bounds.x + x * w,
                   self.bounds.y + y * h,
                   w, h)

    def touch_began(self, touch):
        self.touch = touch

    def touch_ended(self, touch):
        if self.snake.dead:
            self.scene.states["game"] = GameState(self.scene)
            return
        if touch.touch_id == self.touch.touch_id:
            x = touch.location.x - self.touch.location.x
            y = touch.location.y - self.touch.location.y
            map = {abs(y): "y", abs(x): "x"}
            m = max((abs(x), abs(y)))
            if m > 50:
                axis = map[m]
                val = locals()[axis]
                self.snake.change_direction(axis, val)

class Scene (scene.Scene):
    def setup(self):
        self.states = {"menu": MenuState(self),
                       "game": GameState(self)}
        self.cstate = "menu"

    def draw(self):
        self.states[self.cstate].draw()

    def touch_began(self, touch):
        self.states[self.cstate].touch_began(touch)

    def touch_moved(self, touch):
        self.states[self.cstate].touch_moved(touch)

    def touch_ended(self, touch):
        self.states[self.cstate].touch_ended(touch)

def main():
    scene.run(Scene())

if __name__ == "__main__":
    main()
