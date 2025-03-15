import pygame
import chess
import chess.engine
import random
import os
import datetime
import json
from pathlib import Path
pygame.init()
pygame.mixer.init()
WIDTH = 1100
HEIGHT = 750
BOARD_SIZE = 750
SQUARE_SIZE = BOARD_SIZE // 8
WHITE = (240, 217, 181)
BROWN = (181, 136, 99)
SELECTED_COLOR = (186, 202, 43)
MOVE_HIGHLIGHT_COLOR = (214, 214, 189)
TEXT_COLOR = (50, 50, 50)
MENU_BG_COLOR = (45, 45, 45)
MENU_BUTTON_COLOR = (70, 70, 70)
MENU_BUTTON_HOVER = (90, 90, 90)
MENU_TEXT_COLOR = (230, 230, 230)
class Button:
    def __init__(self, x, y, width, height, text, font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont('Arial', font_size)
        self.is_hovered = False
    def draw(self, screen):
        color = MENU_BUTTON_HOVER if self.is_hovered else MENU_BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, MENU_TEXT_COLOR, self.rect, 2, border_radius=10)
        text_surface = self.font.render(self.text, True, MENU_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False
class StartupMenu:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.selected_theme = "classic"
        center_x = WIDTH // 2  # This will now use the new WIDTH
        self.buttons = {
            'new_game': Button(center_x - 100, 200, 200, 50, "New Game"),
            'load_game': Button(center_x - 100, 300, 200, 50, "Load Game"),
            'classic_theme': Button(center_x - 250, 400, 200, 50, "Classic Theme"),
            'modern_theme': Button(center_x + 50, 400, 200, 50, "Modern Theme"),
            'quit': Button(center_x - 100, 500, 200, 50, "Quit")
        }
    def run(self):
        while self.running:
            self.screen.fill(MENU_BG_COLOR)
            font = pygame.font.SysFont('Arial', 48, bold=True)
            title = font.render("Chess Game", True, MENU_TEXT_COLOR)
            title_rect = title.get_rect(center=(WIDTH // 2, 100))
            self.screen.blit(title, title_rect)
            for button in self.buttons.values():
                button.draw(self.screen)
            font = pygame.font.SysFont('Arial', 24)
            theme_text = font.render(f"Selected Theme: {self.selected_theme.title()}", 
                                   True, MENU_TEXT_COLOR)
            self.screen.blit(theme_text, (WIDTH // 2 - 100, 460))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit', self.selected_theme
                for button_name, button in self.buttons.items():
                    if button.handle_event(event):
                        if button_name == 'quit':
                            return 'quit', self.selected_theme
                        elif button_name == 'classic_theme':
                            self.selected_theme = 'classic'
                        elif button_name == 'modern_theme':
                            self.selected_theme = 'modern'
                        elif button_name in ['new_game', 'load_game']:
                            return button_name, self.selected_theme
class PromotionMenu:
    def __init__(self, screen, square_pos, is_white):
        self.screen = screen
        self.is_white = is_white
        self.color = 'white' if is_white else 'black'
        col, row = square_pos
        self.x = col * SQUARE_SIZE
        self.y = row * SQUARE_SIZE
        self.width = SQUARE_SIZE
        self.height = SQUARE_SIZE * 4
        if self.y + self.height > BOARD_SIZE:
            self.y = BOARD_SIZE - self.height
        self.pieces = ['Q', 'R', 'B', 'N']
        self.selected = None
    def draw(self, pieces_images):
        pygame.draw.rect(self.screen, (240, 240, 240), 
                        (self.x, self.y, self.width, self.height))
        pygame.draw.rect(self.screen, (0, 0, 0), 
                        (self.x, self.y, self.width, self.height), 2)
        for i, piece in enumerate(self.pieces):
            piece_y = self.y + (i * SQUARE_SIZE)
            if self.is_hovered(pygame.mouse.get_pos(), i):
                pygame.draw.rect(self.screen, (200, 200, 100),
                               (self.x, piece_y, SQUARE_SIZE, SQUARE_SIZE))
            piece_surface = pieces_images[self.color][piece]
            self.screen.blit(piece_surface, 
                           (self.x + 10, piece_y + 10))
    def is_hovered(self, pos, index):
        mouse_x, mouse_y = pos
        piece_y = self.y + (index * SQUARE_SIZE)
        return (self.x <= mouse_x <= self.x + SQUARE_SIZE and
                piece_y <= mouse_y <= piece_y + SQUARE_SIZE)
    def handle_click(self, pos):
        for i, piece in enumerate(self.pieces):
            if self.is_hovered(pos, i):
                return piece
        return None
class ChessGame:
    def __init__(self, theme='classic'):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.board = chess.Board()
        self.selected_square = None
        self.player_turn = True
        self.possible_moves = set()
        self.move_history = []
        self.captured_pieces = {'white': [], 'black': []}
        self.theme = theme
        self.clock = pygame.time.Clock()
        self.promotion_menu = None
        self.pending_promotion = None
        self.game_message = None
        self.font = pygame.font.SysFont('Arial', 24)
        self.load_assets()
    def record_move(self, move):
        """Record a move in the move history"""
        piece = self.board.piece_at(move.from_square)
        capture = self.board.piece_at(move.to_square)
        move_san = self.board.san(move)
        turn_number = len(self.move_history) // 2 + 1
        if capture:
            captured_color = 'white' if capture.color == chess.WHITE else 'black'
            self.captured_pieces[captured_color].append(capture.symbol())
        self.move_history.append({
            'turn': turn_number,
            'move': move_san,
            'player': 'White' if self.board.turn == chess.BLACK else 'Black'
        })
    def draw_move_history(self):
        """Draw the move history on the right side of the board"""
        start_x = BOARD_SIZE + 10
        start_y = 10
        
        # Draw header
        header = self.font.render("Move History", True, TEXT_COLOR)
        self.screen.blit(header, (start_x, start_y))
        
        # Draw moves
        for i, move in enumerate(self.move_history[-10:]):  # Show last 10 moves
            text = f"{move['turn']}. {move['player']}: {move['move']}"
            move_text = self.font.render(text, True, TEXT_COLOR)
            self.screen.blit(move_text, (start_x, start_y + 30 + (i * 25)))

    def draw_captured_pieces(self):
        """Draw captured pieces below the move history"""
        start_x = BOARD_SIZE + 10
        start_y = 300
        
        # Draw white captured pieces
        white_text = self.font.render("White captured:", True, TEXT_COLOR)
        self.screen.blit(white_text, (start_x, start_y))
        captured_white = " ".join(self.captured_pieces['white'])
        white_pieces = self.font.render(captured_white, True, TEXT_COLOR)
        self.screen.blit(white_pieces, (start_x, start_y + 25))
        
        # Draw black captured pieces
        black_text = self.font.render("Black captured:", True, TEXT_COLOR)
        self.screen.blit(black_text, (start_x, start_y + 60))
        captured_black = " ".join(self.captured_pieces['black'])
        black_pieces = self.font.render(captured_black, True, TEXT_COLOR)
        self.screen.blit(black_pieces, (start_x, start_y + 85))

    def show_game_message(self, message):
        """Display a game message"""
        self.game_message = {
            'text': message,
            'color': (255, 215, 0),  # Gold color for the message
            'start_time': pygame.time.get_ticks()
        }

    def draw_game_message(self):
        """Draw the game message if it exists"""
        if self.game_message:
            current_time = pygame.time.get_ticks()
            if current_time - self.game_message['start_time'] < 5000:  # Display for 5 seconds
                # Create gradient background
                gradient_rect = pygame.Surface((WIDTH, HEIGHT))
            
                # Animate background colors
                time_factor = (current_time - self.game_message['start_time']) / 1000  # Time in seconds
                color_index = int(time_factor * 2) % len(self.game_message['background_colors'])
                next_color_index = (color_index + 1) % len(self.game_message['background_colors'])
            
                color1 = self.game_message['background_colors'][color_index]
                color2 = self.game_message['background_colors'][next_color_index]
            
                for i in range(HEIGHT):
                    # Create smooth gradient transition
                    factor = i / HEIGHT
                    current_color = (
                        int(color1[0] * (1 - factor) + color2[0] * factor),
                        int(color1[1] * (1 - factor) + color2[1] * factor),
                        int(color1[2] * (1 - factor) + color2[2] * factor)
                    )
                    pygame.draw.line(gradient_rect, current_color, (0, i), (WIDTH, i))
            
                # Add some transparency to the gradient
                gradient_rect.set_alpha(200)
                self.screen.blit(gradient_rect, (0, 0))
            
                # Draw main message
                font_large = pygame.font.SysFont('Arial', 72, bold=True)
                text_large = font_large.render(self.game_message['text'], True, (255, 255, 255))
                text_rect_large = text_large.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            
                # Add glow effect
                glow_surf = pygame.Surface((text_rect_large.width + 20, text_rect_large.height + 20))
                glow_surf.fill((0, 0, 0))
                glow_surf.set_colorkey((0, 0, 0))
            
                # Draw the text multiple times with increasing size for glow effect
                for offset in range(10, 0, -2):
                    glow_text = font_large.render(self.game_message['text'], True, (255, 215, 0, 25))
                    glow_rect = glow_text.get_rect(center=(glow_surf.get_width()//2 + offset, glow_surf.get_height()//2))
                    glow_surf.blit(glow_text, glow_rect)
            
                # Draw the glowing background
                glow_rect = glow_surf.get_rect(center=text_rect_large.center)
                self.screen.blit(glow_surf, glow_rect)
            
                # Draw the main text
                self.screen.blit(text_large, text_rect_large)
            
                # Add additional message
                font_small = pygame.font.SysFont('Arial', 36)
                text_small = font_small.render("Press any key to continue...", True, (255, 255, 255))
                text_rect_small = text_small.get_rect(center=(WIDTH // 2, HEIGHT * 3 // 4))
                self.screen.blit(text_small, text_rect_small)
            
                # Add some particle effects
                for _ in range(20):
                    x = random.randint(0, WIDTH)
                    y = random.randint(0, HEIGHT)
                    size = random.randint(2, 6)
                    color = random.choice(self.game_message['background_colors'])
                    pygame.draw.circle(self.screen, color, (x, y), size)
            else:
                self.game_message = None
    def handle_move(self, from_square, to_square):
        piece = self.board.piece_at(from_square)
        is_promotion = (piece is not None and 
                       piece.piece_type == chess.PAWN and
                       ((piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or
                        (piece.color == chess.BLACK and chess.square_rank(to_square) == 0)))
        
        if is_promotion:
            self.pending_promotion = (from_square, to_square)
            col = chess.square_file(to_square)
            row = 7 - chess.square_rank(to_square)
            self.promotion_menu = PromotionMenu(self.screen, (col, row), piece.color == chess.WHITE)
            return False
        else:
            move = chess.Move(from_square, to_square)
            if move in self.board.legal_moves:
                self.record_move(move)
                self.board.push(move)
                return True
        return False

    def ai_move(self):
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            move = random.choice(legal_moves)
            self.record_move(move)
            self.board.push(move)

    def load_assets(self):
        """Load chess piece images"""
        try:
            self.pieces = {'white': {}, 'black': {}}
            piece_chars = 'KQRBNP'
            theme_folder = f'chess_pieces/{self.theme}'
        
            for piece in piece_chars:
                white_path = os.path.join(theme_folder, f'white_{piece.lower()}.png')
                black_path = os.path.join(theme_folder, f'black_{piece.lower()}.png')
            
                if os.path.exists(white_path):
                    white_img = pygame.image.load(white_path)
                    self.pieces['white'][piece] = pygame.transform.scale(
                        white_img, (SQUARE_SIZE - 20, SQUARE_SIZE - 20)
                    )
                else:
                    white_surf = pygame.Surface((SQUARE_SIZE - 20, SQUARE_SIZE - 20))
                    white_surf.fill((255, 255, 255))
                    pygame.draw.rect(white_surf, (0, 0, 0), white_surf.get_rect(), 2)
                    font = pygame.font.SysFont('Arial', 36)
                    text = font.render(piece, True, (0, 0, 0))
                    text_rect = text.get_rect(center=white_surf.get_rect().center)
                    white_surf.blit(text, text_rect)
                    self.pieces['white'][piece] = white_surf
                
                if os.path.exists(black_path):
                    black_img = pygame.image.load(black_path)
                    self.pieces['black'][piece] = pygame.transform.scale(
                        black_img, (SQUARE_SIZE - 20, SQUARE_SIZE - 20)
                    )
                else:
                    black_surf = pygame.Surface((SQUARE_SIZE - 20, SQUARE_SIZE - 20))
                    black_surf.fill((100, 100, 100))
                    pygame.draw.rect(black_surf, (255, 255, 255), black_surf.get_rect(), 2)
                    font = pygame.font.SysFont('Arial', 36)
                    text = font.render(piece, True, (255, 255, 255))
                    text_rect = text.get_rect(center=black_surf.get_rect().center)
                    black_surf.blit(text, text_rect)
                    self.pieces['black'][piece] = black_surf
        except Exception as e:
            print(f"Error loading assets: {e}")
            self.create_fallback_pieces()

    def create_fallback_pieces(self):
        """Create basic piece representations if images can't be loaded"""
        self.pieces = {'white': {}, 'black': {}}
        piece_chars = 'KQRBNP'
    
        for piece in piece_chars:
            # Create white pieces
            white_surf = pygame.Surface((SQUARE_SIZE - 20, SQUARE_SIZE - 20))
            white_surf.fill((255, 255, 255))
            pygame.draw.rect(white_surf, (0, 0, 0), white_surf.get_rect(), 2)
            font = pygame.font.SysFont('Arial', 36)
            text = font.render(piece, True, (0, 0, 0))
            text_rect = text.get_rect(center=white_surf.get_rect().center)
            white_surf.blit(text, text_rect)
            self.pieces['white'][piece] = white_surf
        
            # Create black pieces
            black_surf = pygame.Surface((SQUARE_SIZE - 20, SQUARE_SIZE - 20))
            black_surf.fill((100, 100, 100))
            pygame.draw.rect(black_surf, (255, 255, 255), black_surf.get_rect(), 2)
            text = font.render(piece, True, (255, 255, 255))
            text_rect = text.get_rect(center=black_surf.get_rect().center)
            black_surf.blit(text, text_rect)
            self.pieces['black'][piece] = black_surf

    def draw_board(self):
        """Draw the chess board"""
        for row in range(8):
            for col in range(8):
                color = WHITE if (row + col) % 2 == 0 else BROWN
                pygame.draw.rect(
                    self.screen, 
                    color, 
                    (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                )
                square = chess.square(col, 7 - row)
                if self.selected_square and (row, col) == self.selected_square:
                    pygame.draw.rect(
                        self.screen,
                        SELECTED_COLOR,
                        (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                        5
                    )
                if square in self.possible_moves:
                    pygame.draw.circle(
                        self.screen,
                        MOVE_HIGHLIGHT_COLOR,
                        (col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                        row * SQUARE_SIZE + SQUARE_SIZE // 2),
                        15
                    )

    def draw_pieces(self):
        """Draw the chess pieces on the board"""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                if piece:
                    color = 'white' if piece.color == chess.WHITE else 'black'
                    piece_char = piece.symbol().upper()
                    if piece_char in self.pieces[color]:
                        piece_surface = self.pieces[color][piece_char]
                        piece_pos = (
                            col * SQUARE_SIZE + 10,
                            row * SQUARE_SIZE + 10
                        )
                        self.screen.blit(piece_surface, piece_pos)

    def get_square_from_mouse(self, pos):
        """Convert mouse position to board square"""
        x, y = pos
        if x >= BOARD_SIZE:
            return None
        return (y // SQUARE_SIZE, x // SQUARE_SIZE)

    def get_possible_moves(self, square):
        """Get all possible moves for a piece"""
        moves = set()
        for move in self.board.legal_moves:
            if move.from_square == square:
                moves.add(move.to_square)
        return moves


    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            self.screen.fill((0, 0, 0))
            self.draw_board()
            self.draw_pieces()
            self.draw_move_history()
            self.draw_captured_pieces()
            if self.promotion_menu:
                self.promotion_menu.draw(self.pieces)
            if self.game_message:
                self.draw_game_message()
            
            pygame.display.flip()

            if self.board.is_game_over():
                if self.board.is_checkmate():
                    winner = "Black" if self.board.turn == chess.WHITE else "White"
                    self.show_game_message(f"Checkmate! {winner} wins!")
                else:
                    self.show_game_message("Game Over! It's a draw!")
                pygame.time.wait(5000)  # Show the message for 5 seconds
                running = False
                continue

            if not self.player_turn and not self.promotion_menu:
                self.ai_move()
                self.player_turn = True
                continue

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.promotion_menu:
                        piece = self.promotion_menu.handle_click(event.pos)
                        if piece:
                            from_square, to_square = self.pending_promotion
                            promotion_piece = {'Q': chess.QUEEN, 'R': chess.ROOK,
                                            'B': chess.BISHOP, 'N': chess.KNIGHT}[piece]
                            move = chess.Move(from_square, to_square, promotion=promotion_piece)
                            if move in self.board.legal_moves:
                                self.record_move(move)
                                self.board.push(move)
                                self.player_turn = False
                            self.promotion_menu = None
                            self.pending_promotion = None
                    elif self.player_turn:
                        result = self.get_square_from_mouse(event.pos)
                        if result is None:
                            continue
                        row, col = result
                        square = chess.square(col, 7 - row)
                        if self.selected_square is None:
                            piece = self.board.piece_at(square)
                            if piece and piece.color == chess.WHITE:
                                self.selected_square = (row, col)
                                self.possible_moves = self.get_possible_moves(square)
                        else:
                            from_square = chess.square(
                                self.selected_square[1],
                                7 - self.selected_square[0]
                            )
                            if self.handle_move(from_square, square):
                                self.player_turn = False
                            
                            self.selected_square = None
                            self.possible_moves = set()
def main():
    Path("chess_pieces/classic").mkdir(parents=True, exist_ok=True)
    Path("chess_pieces/modern").mkdir(parents=True, exist_ok=True)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess Game")
    
    while True:
        menu = StartupMenu(screen)
        action, theme = menu.run()
        if action == 'quit':
            break
        game = ChessGame(theme)
        game.run()
    
    pygame.quit()

if __name__ == "__main__":
    main()