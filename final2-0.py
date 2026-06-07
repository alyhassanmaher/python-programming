import pygame, sys, random
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
GRID_SIZE = 50
GRID_COLS, GRID_ROWS = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
BLACK, WHITE, BLUE, RED, GOLD, SLATE, EMERALD, CRIMSON = (0,0,0), (255,255,255), (0,0,255), (255,0,0), (255,215,0), (112,128,144), (80,200,120), (220,20,60)
MENU, GAME, GAME_OVER = 0, 1, 2

# Setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tactical War Game")
font = pygame.font.SysFont("Arial", 20)
title_font = pygame.font.SysFont("Arial", 36, bold=True)

class Unit:
    def __init__(self, x, y, unit_type, player):
        self.x, self.y = x, y
        self.unit_type = unit_type
        self.player = player
        self.selected = self.moved = self.attacked = False
        
        # Set stats based on unit type (simplified)
        stats = {"Infantry": (50, 30, 20, 3, 1), "Archer": (35, 40, 10, 2, 3), 
                "Cavalry": (60, 35, 15, 5, 1), "Tank": (75, 50, 30, 2, 2)}
        self.max_hp, self.hp, self.attack, self.defense, self.move_range, self.attack_range = stats[unit_type] + (stats[unit_type][4],)
        
        # Create unit image
        self.image = pygame.Surface((GRID_SIZE - 10, GRID_SIZE - 10))
        self.image.fill(BLUE if player == 1 else RED)
    
    def draw(self, screen):
        screen.blit(self.image, (self.x * GRID_SIZE + 5, self.y * GRID_SIZE + 5))
        if self.selected: pygame.draw.rect(screen, GOLD, (self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 3)
        
        # Health bar
        health_width = (GRID_SIZE - 10) * (self.hp / self.max_hp)
        pygame.draw.rect(screen, EMERALD, (self.x * GRID_SIZE + 5, self.y * GRID_SIZE, health_width, 5))
        
        # Status indicators
        if self.moved: pygame.draw.circle(screen, GOLD, (self.x * GRID_SIZE + 10, self.y * GRID_SIZE + GRID_SIZE - 10), 5)
        if self.attacked: pygame.draw.circle(screen, CRIMSON, (self.x * GRID_SIZE + 20, self.y * GRID_SIZE + GRID_SIZE - 10), 5)
    
    def can_move_to(self, x, y, game_map):
        if abs(self.x - x) + abs(self.y - y) > self.move_range or abs(self.x - x) + abs(self.y - y) == 0: return False
        if x < 0 or x >= GRID_COLS or y < 0 or y >= GRID_ROWS: return False
        if any(unit.x == x and unit.y == y for unit in game_map.units): return False
        if game_map.terrain[y][x] == 1: return False
        return True
    
    def can_attack(self, target):
        return abs(self.x - target.x) + abs(self.y - target.y) <= self.attack_range and self.player != target.player and not self.attacked
    
    def attack_unit(self, target):
        damage = max(5, self.attack - target.defense // 2)
        damage = int(damage * random.uniform(0.8, 1.2))
        target.hp -= damage
        if target.hp <= 0:
            target.hp = 0
            return True
        return False
    
    def reset_turn(self):
        self.moved = self.attacked = self.selected = False

class GameMap:
    def __init__(self):
        self.terrain = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.units = []
        self.generate_terrain()
        self.spawn_units()
    
    def generate_terrain(self):
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                if 2 < x < GRID_COLS - 3 and 2 < y < GRID_ROWS - 3:
                    if random.random() < 0.2: self.terrain[y][x] = 1
    
    def spawn_units(self):
        unit_types = ["Infantry", "Archer", "Cavalry", "Tank"]
        for i in range(4):
            self.units.append(Unit(1, 2 + i * 2, unit_types[i], 1))
            self.units.append(Unit(GRID_COLS - 2, 2 + i * 2, unit_types[i], 2))
    
    def draw(self, screen):
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, WHITE if (x + y) % 2 == 0 else BLACK if self.terrain[y][x] == 0 else SLATE, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)
        for unit in self.units: unit.draw(screen)
    
    def get_unit_at(self, x, y):
        for unit in self.units:
            if unit.x == x and unit.y == y: return unit
        return None
    
    def remove_unit(self, unit):
        if unit in self.units: self.units.remove(unit)

class Game:
    def __init__(self):
        self.state = MENU
        self.game_map = None
        self.current_player = 1
        self.selected_unit = None
        self.turn_count = 1
        self.winner = None
        self.moves_made = 0
        self.max_moves_per_turn = 2
    
    def start_game(self):
        self.game_map = GameMap()
        self.current_player = 1
        self.selected_unit = None
        self.turn_count = 1
        self.winner = None
        self.state = GAME
        self.moves_made = 0
    
    def select_unit(self, x, y):
        unit = self.game_map.get_unit_at(x, y)
        
        # Move selected unit
        if self.selected_unit and not unit:
            if self.selected_unit.can_move_to(x, y, self.game_map):
                self.selected_unit.x, self.selected_unit.y = x, y
                self.selected_unit.moved = True
                self.moves_made += 1
                if self.moves_made >= self.max_moves_per_turn: self.end_turn()
                return
        
        # Attack enemy unit
        if self.selected_unit and unit and unit.player != self.current_player and self.selected_unit.can_attack(unit):
            if self.selected_unit.attack_unit(unit):
                self.game_map.remove_unit(unit)
            self.selected_unit.attacked = True
            self.moves_made += 1
            if self.moves_made >= self.max_moves_per_turn: self.end_turn()
            return
        
        # Select own unit
        if unit and unit.player == self.current_player and (not unit.moved or not unit.attacked):
            if self.selected_unit: self.selected_unit.selected = False
            self.selected_unit = unit
            unit.selected = True
            return
        
        # Deselect unit
        if self.selected_unit:
            self.selected_unit.selected = False
            self.selected_unit = None
    
    def end_turn(self):
        if self.selected_unit:
            self.selected_unit.selected = False
            self.selected_unit = None
        
        # Switch players
        self.current_player = 2 if self.current_player == 1 else 1
        self.moves_made = 0
        
        # Reset units for new player
        for unit in self.game_map.units:
            if unit.player == self.current_player: unit.reset_turn()
        
        # Increment turn count when player 1's turn starts
        if self.current_player == 1: self.turn_count += 1
        
        # Check win condition
        player1_units = sum(1 for unit in self.game_map.units if unit.player == 1)
        player2_units = sum(1 for unit in self.game_map.units if unit.player == 2)
        
        if player1_units == 0:
            self.winner = 2
            self.state = GAME_OVER
        elif player2_units == 0:
            self.winner = 1
            self.state = GAME_OVER
    
    def draw(self):
        screen.fill(BLACK)
        
        if self.state == MENU:
            # Draw menu
            title = title_font.render("Tactical War Game", True, WHITE)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            start = font.render("Press SPACE to Start Game", True, WHITE)
            screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, 300))
        
        elif self.state == GAME:
            # Draw game
            self.game_map.draw(screen)
            
            # Draw UI
            pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 40))
            player_text = font.render(f"Player {self.current_player}'s Turn", True, BLUE if self.current_player == 1 else RED)
            screen.blit(player_text, (20, 10))
            turn_text = font.render(f"Turn: {self.turn_count}", True, WHITE)
            screen.blit(turn_text, (200, 10))
            moves_text = font.render(f"Moves: {self.moves_made}/{self.max_moves_per_turn}", True, WHITE)
            screen.blit(moves_text, (300, 10))
            
            # End turn button
            pygame.draw.rect(screen, EMERALD, (SCREEN_WIDTH - 120, 5, 100, 30))
            end_text = font.render("END TURN", True, BLACK)
            screen.blit(end_text, (SCREEN_WIDTH - 110, 10))
            
            # Show movement options for selected unit
            if self.selected_unit and not self.selected_unit.moved:
                for y in range(GRID_ROWS):
                    for x in range(GRID_COLS):
                        if self.selected_unit.can_move_to(x, y, self.game_map):
                            pygame.draw.rect(screen, EMERALD, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 3)
            
            # Show attack options for selected unit
            if self.selected_unit and not self.selected_unit.attacked:
                for unit in self.game_map.units:
                    if self.selected_unit.can_attack(unit):
                        pygame.draw.rect(screen, CRIMSON, (unit.x * GRID_SIZE, unit.y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 3)
        
        elif self.state == GAME_OVER:
            # Draw game over screen
            self.game_map.draw(screen)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            game_over = title_font.render("Game Over", True, WHITE)
            screen.blit(game_over, (SCREEN_WIDTH//2 - game_over.get_width()//2, 200))
            
            winner = font.render(f"Player {self.winner} Wins!", True, BLUE if self.winner == 1 else RED)
            screen.blit(winner, (SCREEN_WIDTH//2 - winner.get_width()//2, 300))
            
            restart = font.render("Press SPACE to Play Again", True, WHITE)
            screen.blit(restart, (SCREEN_WIDTH//2 - restart.get_width()//2, 400))
    
    def handle_event(self, event):
        if event.type == pygame.QUIT: return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: return False
            if event.key == pygame.K_SPACE and (self.state == MENU or self.state == GAME_OVER):
                self.start_game()
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = pygame.mouse.get_pos()
            
            if self.state == GAME:
                # End turn button
                if SCREEN_WIDTH - 120 <= x <= SCREEN_WIDTH - 20 and 5 <= y <= 35:
                    self.end_turn()
                # Map click
                elif y > 40:
                    grid_x, grid_y = x // GRID_SIZE, y // GRID_SIZE
                    self.select_unit(grid_x, grid_y)
        
        return True

def main():
    clock = pygame.time.Clock()
    game = Game()
    running = True
    
    while running:
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
        
        game.draw()
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
