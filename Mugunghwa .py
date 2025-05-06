from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_TIMES_ROMAN_24
import math
import random
import time

class GameState:
    def __init__(self):
        # Game constants
        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = 1080, 600
        self.BASE_GAME_LENGTH = 1000  # Base distance to finish line
        self.BASE_PLAYER_SPEED = 5
        self.BASE_TURN_SPEED = 5
        self.BASE_SPOTTER_TURN_SPEED = 2  # Increased from 1 to make spotting more challenging
        self.SPOTTER_HEAD_ANGLE_RANGE = (-90, 90)  # Narrowed the range
        self.BASE_BULLET_SPEED = 15
        self.BASE_OBSTACLE_COUNT = 10
        
        # Level system
        self.current_level = 1
        self.max_level = 5
        self.level_complete = False
        self.level_up_time = 0
        self.level_up_display_duration = 1  
        self.show_level_start = True
        self.level_start_time = 0
        self.total_time = 0
        
        # Game state
        self.reset_level()

        # Camera settings
        self.cam_angle, self.cam_radius, self.cam_height = 45, 500, 500
        self.first_person = False

        # Key states
        self.keys_pressed = {
            b'w': False,
            b's': False,
            b'a': False,
            b'd': False,
            b' ': False  # Space for shooting
        }
    
    def generate_obstacles(self):
        self.obstacles = []
        for _ in range(self.OBSTACLE_COUNT):
            x = random.randint(100, self.GAME_LENGTH - 100)
            y = random.randint(-400, 400)
            self.obstacles.append([x, y])

    def generate_trees(self):
        self.trees = []
        
        # Boundary trees - along the sides (spaced farther apart)
        for x in range(-400, self.GAME_LENGTH + 400, 100):
            # Left side (fewer trees)
            if random.random() > 0.3:
                self.trees.append([x, -450 + random.randint(-20, 20)])
            # Right side (fewer trees)
            if random.random() > 0.3:
                self.trees.append([x, 450 + random.randint(-20, 20)])
        
        # Less dense trees behind spotter area
        for _ in range(30):
            x = self.spotter_pos[0] + random.randint(50, 300)
            y = random.randint(-500, 500)
            self.trees.append([x, y])
        
        # Fewer random trees in the play area
        for _ in range(15):
            x = random.randint(100, self.GAME_LENGTH - 100)
            y = random.randint(-400, 400)
            self.trees.append([x, y])

    def generate_npcs(self):
        self.npcs = []
        colors = [
            (0.2, 0.2, 0.8),   # Blue
            (0.8, 0.8, 0.2),   # Yellow
            (0.8, 0.2, 0.8),   # Purple
            (0.2, 0.8, 0.8)    # Cyan
        ]
        
        for i in range(4):
            self.npcs.append({
                'pos': [random.randint(-100, 100), random.randint(-100, 100), 0],
                'angle': 0,  # Facing forward along positive X axis
                'speed': self.PLAYER_SPEED * random.uniform(0.7, 1.3),
                'color': colors[i],
                'caught': False,
                'finished': False,
                'last_move_time': 0,
                'move_delay': random.uniform(0.5, 2.0),
                'last_angle_change': 0,
                'angle_change_delay': random.uniform(2.0, 5.0)
            })

    def reset_level(self):
        # Adjust difficulty based on level
        level_multiplier = 1 + 0.15 * (self.current_level - 1)
        self.GAME_LENGTH = int(self.BASE_GAME_LENGTH * level_multiplier)
        self.OBSTACLE_COUNT = self.BASE_OBSTACLE_COUNT + (self.current_level - 1) * 5
        self.PLAYER_SPEED = self.BASE_PLAYER_SPEED * (1 + 0.05 * (self.current_level - 1))
        self.TURN_SPEED = self.BASE_TURN_SPEED
        self.SPOTTER_TURN_SPEED = self.BASE_SPOTTER_TURN_SPEED * (1 + 0.1 * (self.current_level - 1))
        self.BULLET_SPEED = self.BASE_BULLET_SPEED * (1 + 0.1 * (self.current_level - 1))
        
        # Reset game state for new level
        self.player_pos = [0, 0, 0]
        self.player_angle = 0
        self.spotter_pos = [self.GAME_LENGTH + 200, 0, 0]
        self.spotter_head_angle = 0
        self.spotter_state = "green"
        self.last_state_change = 0
        self.state_duration = 0
        self.game_over = False
        self.game_won = False
        self.player_caught = False
        self.start_time = time.time()
        self.finish_time = 0
        self.bullets = []
        self.obstacles = []
        self.trees = []
        self.level_complete = False
        self.show_level_start = True
        self.level_start_time = time.time()        
        self.generate_obstacles()
        self.generate_trees()
        self.generate_npcs()

game = GameState()

def text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix() 
    glLoadIdentity() 
    gluOrtho2D(0, game.WINDOW_WIDTH, 0, game.WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW) 
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y) 
    for char in text:
        glutBitmapCharacter(font, ord(char))
    glPopMatrix() 
    glMatrixMode(GL_PROJECTION)  
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_message_box(title, message, submessage=None, alpha=1.0):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, game.WINDOW_WIDTH, 0, game.WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Semi-transparent background
    glColor4f(0.2, 0.2, 0.5, alpha * 0.7)
    glBegin(GL_QUADS)
    glVertex2f(game.WINDOW_WIDTH//2 - 250, game.WINDOW_HEIGHT//2 + 150)
    glVertex2f(game.WINDOW_WIDTH//2 + 250, game.WINDOW_HEIGHT//2 + 150)
    glVertex2f(game.WINDOW_WIDTH//2 + 250, game.WINDOW_HEIGHT//2 - 150)
    glVertex2f(game.WINDOW_WIDTH//2 - 250, game.WINDOW_HEIGHT//2 - 150)
    glEnd()
    
    # Border
    glLineWidth(3)
    glColor4f(1, 1, 1, alpha)
    glBegin(GL_LINE_LOOP)
    glVertex2f(game.WINDOW_WIDTH//2 - 250, game.WINDOW_HEIGHT//2 + 150)
    glVertex2f(game.WINDOW_WIDTH//2 + 250, game.WINDOW_HEIGHT//2 + 150)
    glVertex2f(game.WINDOW_WIDTH//2 + 250, game.WINDOW_HEIGHT//2 - 150)
    glVertex2f(game.WINDOW_WIDTH//2 - 250, game.WINDOW_HEIGHT//2 - 150)
    glEnd()
    
    # Title
    glColor4f(1, 1, 1, alpha)
    text_x = game.WINDOW_WIDTH//2 - len(title) * 9
    text_y = game.WINDOW_HEIGHT//2 + 100
    glRasterPos2f(text_x, text_y)
    for char in title:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
    
    # Message
    text_y -= 50
    glRasterPos2f(game.WINDOW_WIDTH//2 - len(message) * 7, text_y)
    for char in message:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Submessage
    if submessage:
        text_y -= 30
        glRasterPos2f(game.WINDOW_WIDTH//2 - len(submessage) * 7, text_y)
        for char in submessage:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_level_up_message():
    current_time = time.time()
    if current_time - game.level_up_time < game.level_up_display_duration:
        alpha = min(1.0, 2 - 2 * (current_time - game.level_up_time) / game.level_up_display_duration)
        title = f"LEVEL {game.current_level} COMPLETE!"
        message = f"Advancing to Level {game.current_level + 1}"
        submessage = "More obstacles and faster enemies ahead!"
        draw_message_box(title, message, submessage, alpha)
    elif current_time - game.level_up_time < game.level_up_display_duration + 0.1:
        # Immediately advance to next level without waiting for user input
        game.current_level += 1
        game.reset_level()

def draw_level_start_message():
    current_time = time.time()
    if game.show_level_start and current_time - game.level_start_time < 1.5:
        alpha = min(1.0, 2 - 2 * (current_time - game.level_start_time) / 1.5)
        title = f"LEVEL {game.current_level}"
        message = f"Reach the finish line {game.GAME_LENGTH} units away"
        submessage = f"Obstacles: {game.OBSTACLE_COUNT}"
        draw_message_box(title, message, submessage, alpha)
    elif game.show_level_start:
        game.show_level_start = False

def draw_ground():
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.8, 0.2)  # Green ground
    glVertex3f(-500, -500, 0)
    glVertex3f(game.GAME_LENGTH + 500, -500, 0)
    glVertex3f(game.GAME_LENGTH + 500, 500, 0)
    glVertex3f(-500, 500, 0)
    glEnd()

def draw_finish_line():
    glBegin(GL_QUADS)
    glColor3f(1, 1, 1)  # White finish line
    glVertex3f(game.GAME_LENGTH, -500, 0)
    glVertex3f(game.GAME_LENGTH, 500, 0)
    glVertex3f(game.GAME_LENGTH, 500, 100)
    glVertex3f(game.GAME_LENGTH, -500, 100)
    glEnd()

def draw_tree(x, y):
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Taller trunk (increased height)
    glColor3f(0.5, 0.3, 0.1)  # Brown trunk
    glPushMatrix()
    glTranslatef(0, 0, 25)  # Raised base height
    glScalef(1, 1, 5)  # Increased trunk height (was 3)
    glutSolidCube(10)
    glPopMatrix()
    
    # Larger leaves at top
    glColor3f(0.1, 0.6, 0.1)  # Green leaves
    glPushMatrix()
    glTranslatef(0, 0, 70)  # Higher up (was 40)
    glutSolidSphere(25, 20, 20)  # Slightly larger canopy (was 20)
    glPopMatrix()
    
    glPopMatrix()

def draw_trees():
    for tree in game.trees:
        draw_tree(tree[0], tree[1])

def setup_camera():
    glMatrixMode(GL_PROJECTION) 
    glLoadIdentity()
    gluPerspective(60, game.WINDOW_WIDTH / game.WINDOW_HEIGHT, 1.0, 5000)
    glMatrixMode(GL_MODELVIEW) 
    glLoadIdentity()

    if game.first_person:
        x, y, z = game.player_pos
        look_x = x + math.sin(math.radians(-game.player_angle)) * 100
        look_y = y + math.cos(math.radians(-game.player_angle)) * 100
        gluLookAt(x, y, z + 50, look_x, look_y, z + 50, 0, 0, 1)
    else:
        angle = math.radians(game.cam_angle)
        x = game.player_pos[0] + game.cam_radius * math.sin(angle)
        y = game.player_pos[1] + game.cam_radius * math.cos(angle)
        gluLookAt(x, y, game.cam_height, game.player_pos[0], game.player_pos[1], 0, 0, 0, 1)

def draw_player():
    glPushMatrix()
    px, py, pz = game.player_pos 
    glTranslatef(px, py, pz + 35)
    glRotatef(game.player_angle, 0, 0, 1)  # Rotate player model to face direction
    
    # Body
    glColor3f(0.8, 0.2, 0.2)  # Red player
    glutSolidSphere(20, 20, 20)
    
    # Head
    glTranslatef(0, 0, 30)
    glColor3f(1, 0.8, 0.6)
    glutSolidSphere(15, 20, 20)
    
    # Eyes (positioned behind the sphere to match movement direction)
    glPushMatrix()
    glColor3f(0, 0, 0)
    glTranslatef(0, -15, 5)  # Position eyes at back of head (relative to movement direction)
    glTranslatef(5, 0, 0)    # Right eye offset
    glutSolidSphere(3, 10, 10)
    glTranslatef(-10, 0, 0)  # Left eye offset
    glutSolidSphere(3, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def draw_npc(npc):
    glPushMatrix()
    px, py, pz = npc['pos']
    glTranslatef(px, py, pz + 35)
    glRotatef(npc['angle'], 0, 0, 1)  # Rotate NPC model to face direction
    
    # Body
    glColor3f(*npc['color'])
    glutSolidSphere(20, 20, 20)
    
    # Head
    glTranslatef(0, 0, 30)
    glColor3f(1, 0.8, 0.6)
    glutSolidSphere(15, 20, 20)
    
    # Eyes (positioned to face forward)
    glPushMatrix()
    glColor3f(0, 0, 0)
    glTranslatef(0, -15, 5)  # Position eyes at back of head (relative to movement direction)
    glTranslatef(5, 0, 0)    # Right eye offset
    glutSolidSphere(3, 10, 10)
    glTranslatef(-10, 0, 0)  # Left eye offset
    glutSolidSphere(3, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def draw_spotter():
    glPushMatrix()
    px, py, pz = game.spotter_pos 
    glTranslatef(px, py, pz) 
    
    # Body
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glutSolidCube(60)
    glPopMatrix()
    
    # Head
    glPushMatrix()
    glTranslatef(0, 0, 110)
    glColor3f(1, 1, 1)
    glutSolidSphere(25, 20, 20)
    
    # Eyes
    glRotatef(game.spotter_head_angle, 0, 0, 1)
    glColor3f(0, 0, 0)
    glTranslatef(10, 20, 5)
    glutSolidSphere(5, 10, 10)
    glTranslatef(-20, 0, 0)
    glutSolidSphere(5, 10, 10)
    
    # Mouth
    if game.spotter_state == "red":
        glColor3f(1, 0, 0)
        glTranslatef(10, -10, 0)
        glutSolidSphere(8, 10, 10)
    else:
        glColor3f(0, 0.8, 0)
        glTranslatef(10, -10, 0)
        glScalef(1, 0.5, 1)
        glutSolidSphere(8, 10, 10)
    
    glPopMatrix()
    
    glPopMatrix()

def draw_bullet(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(1, 0, 0)
    glutSolidSphere(5, 10, 10)
    glPopMatrix()

def draw_obstacles():
    for obstacle in game.obstacles:
        glPushMatrix()
        glTranslatef(obstacle[0], obstacle[1], 0)
        glColor3f(0.5, 0.2, 0.1)
        glutSolidCube(40)
        glPopMatrix()

def update_spotter():
    current_time = time.time()
    if current_time - game.last_state_change > game.state_duration:
        game.spotter_state = "green" if game.spotter_state == "red" else "red"
        game.last_state_change = current_time
        game.state_duration = random.uniform(1.0, 3.0)
    
    if game.spotter_state == "red":
        game.spotter_head_angle += game.SPOTTER_TURN_SPEED
        if game.spotter_head_angle > game.SPOTTER_HEAD_ANGLE_RANGE[1]:
            game.spotter_head_angle = game.SPOTTER_HEAD_ANGLE_RANGE[1]
            game.SPOTTER_TURN_SPEED *= -1
        elif game.spotter_head_angle < game.SPOTTER_HEAD_ANGLE_RANGE[0]:
            game.spotter_head_angle = game.SPOTTER_HEAD_ANGLE_RANGE[0]
            game.SPOTTER_TURN_SPEED *= -1
    else:
        if abs(game.spotter_head_angle) > 1:
            game.spotter_head_angle *= 0.8

def update_bullets():
    for bullet in game.bullets[:]:
        # Calculate direction to player
        dx = game.player_pos[0] - bullet[0]
        dy = game.player_pos[1] - bullet[1]
        dist = math.sqrt(dx*dx + dy*dy)

        if dist < 20:  # Bullet hit player
            game.game_over = True
            game.player_caught = True
            game.bullets.remove(bullet)
        elif dist > 2000:  # Bullet out of range
            game.bullets.remove(bullet)
        else:
            # Move bullet toward player
            bullet[0] += (dx/dist) * game.BULLET_SPEED
            bullet[1] += (dy/dist) * game.BULLET_SPEED
            bullet[2] = 50  # Keep bullets at consistent height

def check_obstacles():
    for obstacle in game.obstacles:
        dx = game.player_pos[0] - obstacle[0]
        dy = game.player_pos[1] - obstacle[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 30:  # Player touched obstacle
            game.bullets.append([obstacle[0], obstacle[1], 0])

def check_player_visibility():
    if game.spotter_state == "red":
        move_x, move_y = 0, 0
        if game.keys_pressed[b'w'] or game.keys_pressed[b's'] or game.keys_pressed[b'a'] or game.keys_pressed[b'd']:
            if game.keys_pressed[b's']:  # Moving forward (s key)
                move_x = math.sin(math.radians(-game.player_angle))
                move_y = math.cos(math.radians(-game.player_angle))
            if game.keys_pressed[b'w']:  # Moving backward (w key)
                move_x = -math.sin(math.radians(-game.player_angle))
                move_y = -math.cos(math.radians(-game.player_angle))
        
        if move_x != 0 or move_y != 0:
            dx = game.player_pos[0] - game.spotter_pos[0]
            dy = game.player_pos[1] - game.spotter_pos[1]
            angle_to_player = math.degrees(math.atan2(dy, dx)) + 90
            angle_diff = abs(((game.spotter_head_angle - angle_to_player + 180) % 360) - 180)
            detection_angle = 30 + (abs(game.SPOTTER_TURN_SPEED) * 5)  # Dynamic detection angle
            
            if angle_diff < detection_angle:
                if not any(bullet for bullet in game.bullets if bullet[0] == game.spotter_pos[0] and bullet[1] == game.spotter_pos[1]):
                    game.bullets.append([game.spotter_pos[0], game.spotter_pos[1], 0])

def update_npcs():
    current_time = time.time()
    for npc in game.npcs:
        if npc['caught'] or npc['finished']:
            continue
            
        # NPCs only move during green light
        if game.spotter_state == "green" and current_time - npc['last_move_time'] > npc['move_delay']:
            # Move forward (positive X direction)
            npc['pos'][0] += npc['speed']
            
            # Occasionally change direction (but still generally forward)
            if current_time - npc['last_angle_change'] > npc['angle_change_delay']:
                npc['angle'] = random.uniform(-15, 15)  # Small angle variations
                npc['last_angle_change'] = current_time
                npc['angle_change_delay'] = random.uniform(2.0, 5.0)
            
            # Apply slight Y movement based on angle
            npc['pos'][1] += math.sin(math.radians(npc['angle'])) * npc['speed'] * 0.5
            
            npc['last_move_time'] = current_time
            npc['move_delay'] = random.uniform(0.1, 0.5)  # More frequent movement
            
            # Check if NPC hit obstacle
            for obstacle in game.obstacles:
                dx = npc['pos'][0] - obstacle[0]
                dy = npc['pos'][1] - obstacle[1]
                if math.sqrt(dx*dx + dy*dy) < 30:
                    npc['angle'] = 180  # Turn around if hit obstacle
                    npc['pos'][0] -= 20  # Move back a bit
                    break
            
            # Check if NPC reached finish line
            if npc['pos'][0] >= game.GAME_LENGTH:
                npc['finished'] = True
        
        # Keep NPC within bounds
        npc['pos'][0] = max(-500, min(game.GAME_LENGTH, npc['pos'][0]))
        npc['pos'][1] = max(-500, min(500, npc['pos'][1]))
        
        # Check if NPC moved during red light
        if game.spotter_state == "red" and current_time - npc['last_move_time'] < 0.1:
            dx = npc['pos'][0] - game.spotter_pos[0]
            dy = npc['pos'][1] - game.spotter_pos[1]
            angle_to_npc = math.degrees(math.atan2(dy, dx)) + 90
            angle_diff = abs(((game.spotter_head_angle - angle_to_npc + 180) % 360) - 180)
            
            if angle_diff < 30:  # NPC in spotter's view
                npc['caught'] = True

def update_player_movement():
    if game.game_over or game.level_complete:
        return
    
    player_moved = False
    
    # Store previous position before any movement
    prev_pos = game.player_pos.copy()
    
    # Handle turning - always allowed
    if game.keys_pressed[b'a']:
        game.player_angle += game.TURN_SPEED
    if game.keys_pressed[b'd']:
        game.player_angle -= game.TURN_SPEED
    
    # Normalize angle to 0-360 range
    game.player_angle %= 360
    
    # Handle movement (keeping w/s reversed as requested)
    move_x = math.sin(math.radians(-game.player_angle))
    move_y = math.cos(math.radians(-game.player_angle))
    
    if game.keys_pressed[b's']:  # Move forward (s key)
        game.player_pos[0] += move_x * game.PLAYER_SPEED
        game.player_pos[1] += move_y * game.PLAYER_SPEED
        player_moved = True
    if game.keys_pressed[b'w']:  # Move backward (w key)
        game.player_pos[0] -= move_x * game.PLAYER_SPEED
        game.player_pos[1] -= move_y * game.PLAYER_SPEED
        player_moved = True
    
    # Check if player actually moved (position changed)
    player_moved = player_moved and (prev_pos[0] != game.player_pos[0] or prev_pos[1] != game.player_pos[1])
    
    # Check if player moved during red light
    if game.spotter_state == "red" and player_moved:
        check_player_visibility()
    
    # Keep player within bounds
    game.player_pos[0] = max(-500, min(game.GAME_LENGTH, game.player_pos[0]))
    game.player_pos[1] = max(-500, min(500, game.player_pos[1]))
    
    # Check if player reached finish line
    if game.player_pos[0] >= game.GAME_LENGTH:
        if game.current_level < game.max_level:
            game.level_complete = True
            game.level_up_time = time.time()
            game.total_time += time.time() - game.start_time
        else:
            game.game_won = True
            game.game_over = True
            game.finish_time = game.total_time + (time.time() - game.start_time)
    
    check_obstacles()

def keyboard_down(key, x, y):
    if key == b'v':
        game.first_person = not game.first_person
    elif key == b'r' and game.game_over:
        game.current_level = 1
        game.total_time = 0
        game.reset_level()
    elif key in game.keys_pressed:
        game.keys_pressed[key] = True
    
    glutPostRedisplay()

def keyboard_up(key, x, y):
    if key in game.keys_pressed:
        game.keys_pressed[key] = False
    glutPostRedisplay()

def special_key_down(key, x, y):
    if key == GLUT_KEY_LEFT:
        game.cam_angle -= 5
    elif key == GLUT_KEY_RIGHT:
        game.cam_angle += 5
    elif key == GLUT_KEY_UP:
        game.cam_height += 20
    elif key == GLUT_KEY_DOWN:
        game.cam_height = max(100, game.cam_height - 20)
    game.cam_angle %= 360
    glutPostRedisplay()

def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_camera()
    
    draw_ground()
    draw_finish_line()
    draw_trees()
    draw_player()
    for npc in game.npcs:
        draw_npc(npc)
    draw_spotter()
    draw_obstacles()
    
    for bullet in game.bullets:
        draw_bullet(bullet[0], bullet[1], bullet[2])
    
    if game.level_complete:
        draw_level_up_message()
    elif game.show_level_start:
        draw_level_start_message()
    elif not game.game_over:
        # Display HUD
        text(20, 580, f"Level: {game.current_level}/{game.max_level}")
        text(20, 560, f"State: {game.spotter_state.upper()} LIGHT")
        text(20, 540, f"Distance: {int(game.GAME_LENGTH - game.player_pos[0])} units")
        text(20, 520, f"Obstacles: {game.OBSTACLE_COUNT}")
        text(20, 500, "Controls: WASD to move")
        text(20, 480, f"Time: {time.time() - game.start_time:.1f}s (Current Level)")
        text(20, 460, f"Total Time: {game.total_time + (time.time() - game.start_time):.1f}s")
        
        # Show NPC status
        for i, npc in enumerate(game.npcs):
            status = "Finished" if npc['finished'] else "Caught" if npc['caught'] else "Alive"
            text(20, 440 - i * 20, f"NPC {i+1}: {status}")
    else:
        if game.game_won:
            title = "CONGRATULATIONS!"
            message = f"You completed all {game.max_level} levels!"
            submessage = f"Total time: {game.finish_time:.2f} seconds"
            draw_message_box(title, message, submessage)
        else:
            title = "GAME OVER"
            message = "You were caught by the spotter!"
            submessage = 'Press "R" to restart'
            draw_message_box(title, message, submessage)
    
    glutSwapBuffers()

def update_game(value):
    if not game.game_over and not game.level_complete:
        update_spotter()
        update_player_movement()
        update_bullets()
        update_npcs()
    glutPostRedisplay()
    glutTimerFunc(16, update_game, 0)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(game.WINDOW_WIDTH, game.WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Red Light, Green Light - Multiplayer")
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.53, 0.81, 0.92, 1.0)
    
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_key_down)
    glutTimerFunc(0, update_game, 0)
    
    glutMainLoop()

if __name__ == "__main__":
    main()