import streamlit as st
# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="Tic Tac Toe vs Claude",
    page_icon="🎮",
    layout="centered"
)

import streamlit.components.v1 as components
import random
import time
import os
import base64
from dotenv import load_dotenv
import anthropic

# Set up cell click handling with a component
if 'clicked_cell' not in st.session_state:
    st.session_state.clicked_cell = None

# Check URL parameters
params = st.query_params
if 'cell' in params:
    try:
        # Store the cell click in session state
        st.session_state.clicked_cell = int(params['cell'])
        # Clear URL parameters
        params.clear()
    except (ValueError, KeyError, IndexError):
        pass

# Try to load environment variables
try:
    load_dotenv()
except ImportError:
    pass

# Initialize Anthropic client
api_key = os.getenv("ANTHROPIC_API_KEY")

# Set up session state
if 'board_size' not in st.session_state:
    st.session_state.board_size = 3
if 'board' not in st.session_state:
    st.session_state.board = [" " for _ in range(st.session_state.board_size**2)]
if 'current_player' not in st.session_state:
    st.session_state.current_player = random.choice(['X', 'O'])
if 'human_marker' not in st.session_state:
    st.session_state.human_marker = 'X'
if 'ai_marker' not in st.session_state:
    st.session_state.ai_marker = 'O'
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'winner' not in st.session_state:
    st.session_state.winner = None
if 'game_count' not in st.session_state:
    st.session_state.game_count = 1
if 'human_score' not in st.session_state:
    st.session_state.human_score = 0
if 'ai_score' not in st.session_state:
    st.session_state.ai_score = 0
if 'ties' not in st.session_state:
    st.session_state.ties = 0
if 'ai_reasoning' not in st.session_state:
    st.session_state.ai_reasoning = ""
if 'ai_move_history' not in st.session_state:
    st.session_state.ai_move_history = []

# Title and API key input
st.title("Tic Tac Toe vs Claude")

# API key input
if not api_key:
    api_key = st.text_input("Enter your Anthropic API key:", type="password")
    if not api_key:
        st.warning("Please enter your Anthropic API key to play.")
        st.stop()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=api_key)

# Functions for the game
def check_winner(board):
    size = int(st.session_state.board_size)
    win_length = 3  # Fixed win length of 3
    
    # Check rows
    for row_start in range(0, size*size, size):
        for col_start in range(size - win_length + 1):
            segment = board[row_start + col_start:row_start + col_start + win_length]
            if segment.count(segment[0]) == win_length and segment[0] != " ":
                return segment[0]
    
    # Check columns
    for col in range(size):
        for row_start in range(size - win_length + 1):
            segment = [board[(row_start + i) * size + col] for i in range(win_length)]
            if segment.count(segment[0]) == win_length and segment[0] != " ":
                return segment[0]
    
    # Check diagonals (top-left to bottom-right)
    for row_start in range(size - win_length + 1):
        for col_start in range(size - win_length + 1):
            segment = [board[(row_start + i) * size + (col_start + i)] for i in range(win_length)]
            if segment.count(segment[0]) == win_length and segment[0] != " ":
                return segment[0]
    
    # Check diagonals (top-right to bottom-left)
    for row_start in range(size - win_length + 1):
        for col_start in range(win_length - 1, size):
            segment = [board[(row_start + i) * size + (col_start - i)] for i in range(win_length)]
            if segment.count(segment[0]) == win_length and segment[0] != " ":
                return segment[0]
    
    # Check for tie
    if " " not in board:
        return "Tie"
    
    return None

def get_ai_move(board, ai_marker, human_marker):
    size = st.session_state.board_size
    # Format the board state for Claude
    board_str = ""
    separator = "-" + "-+-".join(["-" for _ in range(size-1)]) + "-"
    
    for i in range(size):
        row = "|".join(board[i*size:(i+1)*size])
        board_str += f"    {row}\n"
        if i < size - 1:
            board_str += f"    {separator}\n"
    
    # Generate the position numbers display
    position_display = ""
    for i in range(size):
        row_positions = "|".join([str(i*size+j) for j in range(size)])
        position_display += f"{row_positions}\n"
        if i < size - 1:
            position_display += f"{separator.strip()}\n"
    
    prompt = f"""
    We're playing Tic Tac Toe on a {size}x{size} board. YOU are playing as '{ai_marker}' and I (the human) am playing as '{human_marker}'.
    
    IMPORTANT: To be absolutely clear:
    - All '{ai_marker}' marks on the board are YOUR marks
    - All '{human_marker}' marks on the board are MY marks (the human player)
    - You can only win by getting 3 '{ai_marker}' marks in a row (not {size})
    - I can only win by getting 3 '{human_marker}' marks in a row (not {size})
    - You cannot use my '{human_marker}' marks to form your winning line
    
    CRITICAL: Take your time to carefully read and understand the current board state. 
    Look at EACH position to identify ALL '{human_marker}' and '{ai_marker}' markers.
    Check for potential winning lines of 3 in ALL directions (rows, columns, and diagonals).
    
    The current board state is:
    
{board_str}
    
    It's your turn. Make your move by placing another '{ai_marker}' mark on the board.
    Choose the index number (0-{size*size-1}) of an empty position.
    
    The board positions are numbered as follows:
{position_display}
    
    Please explain your reasoning in 1-2 sentences, then provide your move.
    Format your response like this:
    
    [reasoning] I am choosing position X because... [/reasoning]
    
    X
    
    Where X is a single number 0-{size*size-1} representing an empty position on the board.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=300,
            temperature=0.2,
            system=f"""You are playing Tic Tac Toe against a human player.

IMPORTANT - YOU MUST REMEMBER WHICH MARKER IS YOURS:
- If you're playing as X: All X marks on the board are YOUR marks, all O marks are the HUMAN's
- If you're playing as O: All O marks on the board are YOUR marks, all X marks are the HUMAN's
- You can only win by getting 3 of YOUR OWN markers in a row (regardless of board size)
- You CANNOT win by getting 3 of the HUMAN's markers in a row
- Always pay careful attention to which marker is yours in the current game

The rules of Tic Tac Toe are:
1. The board is a {size}x{size} grid numbered 0-{size*size-1}
2. X always goes first, O always goes second
3. Players take turns placing their marker on an empty space
4. The first player to get 3 of their OWN markers in a row (horizontal, vertical, or diagonal) wins
5. If all spaces are filled and no one has 3 in a row, the game is a tie

CAREFUL ANALYSIS IS REQUIRED:
- Take time to visualize the entire board layout
- Check EVERY position on the board for both your markers and the human's markers
- Scan ALL rows, columns, and both diagonals for potential winning lines or threats
- Look for any sequences of 2 markers that can be extended to 3
- Double-check your understanding before making your move
- Check if the board size has changed since your last move
- Being careful is more important than being quick

Respond with a reasoning explanation followed by a single number 0-{size*size-1} representing your move position.""",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the full response
        full_response = response.content[0].text.strip()
        print(f"Full Claude response: {full_response}")
        
        # Store the AI's reasoning in session state
        reasoning = ""
        if "[reasoning]" in full_response and "[/reasoning]" in full_response:
            reasoning = full_response.split("[reasoning]")[1].split("[/reasoning]")[0].strip()
            st.session_state.ai_reasoning = reasoning
            print(f"Extracted reasoning: {reasoning}")
        else:
            # Try a more flexible approach to extract reasoning
            # Look for any text before a single number (the move)
            import re
            match = re.search(r"(.*?)(\d+)\s*$", full_response, re.DOTALL)
            if match:
                possible_reasoning = match.group(1).strip()
                # Only use if it's a reasonable length
                if len(possible_reasoning) > 5:
                    reasoning = possible_reasoning
                    st.session_state.ai_reasoning = reasoning
                    print(f"Extracted reasoning (alternative method): {reasoning}")
        
        # Try to parse the response to get just a number
        max_position = size*size - 1
        
        # First try to extract a possibly multi-digit number
        import re
        numbers = re.findall(r'\d+', full_response)
        for num_str in numbers:
            num = int(num_str)
            if 0 <= num <= max_position and board[num] == " ":
                return num
        
        # If that didn't work, try digit by digit
        for char in full_response:
            if char.isdigit() and 0 <= int(char) <= max_position:
                move = int(char)
                # Verify it's a valid move
                if board[move] == " ":
                    return move
        
        # If we couldn't parse a valid move, find the first empty space
        for i in range(size*size):
            if board[i] == " ":
                return i
                
    except Exception as e:
        st.error(f"Error getting AI move: {e}")
        # Fallback: find first empty space
        for i in range(size*size):
            if board[i] == " ":
                return i
    
    return None

def make_move(index):
    # Make sure the game isn't over and the move is valid
    if not st.session_state.game_over and st.session_state.board[index] == " ":
        st.session_state.board[index] = st.session_state.current_player
        
        # Check for winner
        winner = check_winner(st.session_state.board)
        if winner:
            st.session_state.game_over = True
            st.session_state.winner = winner
            if winner == "Tie":
                st.session_state.ties += 1
            elif winner == st.session_state.human_marker:
                st.session_state.human_score += 1
            else:
                st.session_state.ai_score += 1
        else:
            # Switch players
            st.session_state.current_player = 'O' if st.session_state.current_player == 'X' else 'X'

def reset_game():
    # Reset the board with the current board size
    size = st.session_state.board_size
    st.session_state.board = [" " for _ in range(size*size)]
    st.session_state.current_player = random.choice(['X', 'O'])
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.game_count += 1
    # Reset the AI reasoning for the new game
    st.session_state.ai_reasoning = ""
    # Note: ai_move_history is cleared in the Play Again button click handler

# Process click from URL if needed    
if st.session_state.clicked_cell is not None:
    cell_index = st.session_state.clicked_cell
    st.session_state.clicked_cell = None
    # Make the move if valid
    if (not st.session_state.game_over and 
        0 <= cell_index < len(st.session_state.board) and 
        st.session_state.board[cell_index] == " " and
        st.session_state.current_player == st.session_state.human_marker):
        make_move(cell_index)

# UI elements
# Adjust the column width based on board size to maintain square aspect ratio
if 'board_size' in st.session_state:
    if st.session_state.board_size >= 7:
        col1, col2 = st.columns([5, 1])
    elif st.session_state.board_size >= 5:
        col1, col2 = st.columns([4, 1])
    else:
        col1, col2 = st.columns([3, 1])
else:
    col1, col2 = st.columns([3, 1])

# Function to generate the game board HTML
# Function to handle cell clicks
def handle_cell_click(cell_index):
    if (not st.session_state.game_over and 
        0 <= cell_index < len(st.session_state.board) and 
        st.session_state.board[cell_index] == " " and
        st.session_state.current_player == st.session_state.human_marker):
        make_move(cell_index)
        st.rerun()

with col1:
    st.header(f"Game #{st.session_state.game_count}")
    
    # Who goes first info
    if st.session_state.current_player == st.session_state.human_marker:
        st.info(f"You go first! You are '{st.session_state.human_marker}'")
    else:
        st.info(f"Claude goes first! You are '{st.session_state.human_marker}'")
    
    # Display the current board state
    st.subheader("Game Board")
    
    # Add CSS for styling the buttons to match cells
    st.markdown("""
    <style>
    .stButton>button {
        background-color: #f5f5f5 !important;
        border: 2px solid #cccccc !important;
        border-radius: 4px !important;
        width: 50px !important;
        height: 50px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 0 !important;
        font-size: 24px !important;
        font-weight: bold !important;
        margin: 2px auto !important;
        color: transparent !important;
    }
    
    .stButton>button:hover {
        background-color: #e5e5e5 !important;
        border-color: #999999 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a grid layout for the board
    size = st.session_state.board_size
    board = st.session_state.board
    is_player_turn = st.session_state.current_player == st.session_state.human_marker and not st.session_state.game_over
    
    # Create a grid layout for direct button clicks
    # Use Streamlit's built-in grid
    size = st.session_state.board_size
    
    # Add CSS to make the buttons appear as cells
    st.markdown("""
    <style>
    .stButton button {
        width: 60px !important;
        height: 60px !important;
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 4px !important;
    }
    
    .stButton button:focus {
        box-shadow: none !important;
    }
    
    /* Make containers more compact */
    .element-container {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    div[data-testid="column"] > div {
        padding: 0 2px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display the board as a grid of buttons
    for row in range(size):
        cols = st.columns(size)
        for col in range(size):
            index = row * size + col
            with cols[col]:
                marker = st.session_state.board[index]
                
                if marker == "X":
                    # X cell
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #e6f3ff;
                            border: 2px solid #0066cc;
                            color: blue;
                            border-radius: 4px;
                            width: 60px;
                            height: 60px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            font-size: 24px;
                            font-weight: bold;
                            margin: 0 auto;
                        ">X</div>
                        """, 
                        unsafe_allow_html=True
                    )
                elif marker == "O":
                    # O cell
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #fff0f0;
                            border: 2px solid #cc0000;
                            color: red;
                            border-radius: 4px;
                            width: 60px;
                            height: 60px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            font-size: 24px;
                            font-weight: bold;
                            margin: 0 auto;
                        ">O</div>
                        """, 
                        unsafe_allow_html=True
                    )
                elif st.session_state.current_player == st.session_state.human_marker and not st.session_state.game_over:
                    # Empty cell that can be clicked
                    if st.button("", key=f"cell_{index}"):
                        # Handle the click directly
                        make_move(index)
                        st.rerun()
                else:
                    # Empty cell that can't be clicked
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #f5f5f5;
                            border: 2px solid #cccccc;
                            border-radius: 4px;
                            width: 60px;
                            height: 60px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            margin: 0 auto;
                        "></div>
                        """, 
                        unsafe_allow_html=True
                    )
    
    # Process clicks from URL parameters if any
    if st.session_state.clicked_cell is not None:
        cell_index = st.session_state.clicked_cell
        st.session_state.clicked_cell = None
        handle_cell_click(cell_index)
    
    # Game status message and Play Again button
    if st.session_state.game_over:
        if st.session_state.winner == "Tie":
            st.success("Game ended in a tie!")
        elif st.session_state.winner == st.session_state.human_marker:
            st.success("🎉 You won! 🎉")
        else:
            st.warning("Claude won this round!")
        
        # Play again button
        if st.button("Play Again"):
            reset_game()
            # Clear Claude's thought history when starting a new game
            st.session_state.ai_move_history = []
            st.rerun()
    
    # Handle AI's turn
    if not st.session_state.game_over and st.session_state.current_player == st.session_state.ai_marker:
        with st.spinner("Claude is thinking..."):
            time.sleep(1)  # Add a small delay to make it feel more natural
            ai_move = get_ai_move(st.session_state.board, st.session_state.ai_marker, st.session_state.human_marker)
            if ai_move is not None:
                # Add the move and reasoning to history
                reasoning = st.session_state.ai_reasoning if st.session_state.ai_reasoning else "No explanation provided"
                st.session_state.ai_move_history.append({
                    'move': ai_move,
                    'reasoning': reasoning
                })
                
                st.toast(f"Claude plays position {ai_move}")
                make_move(ai_move)
                st.rerun()
    
    # Add a chat-like display for Claude's reasoning
    ai_chat = st.container()
    with ai_chat:
        st.subheader("Claude's Thoughts")
        
        # Add CSS for the chat container
        st.markdown("""
        <style>
        .ai-chat-container {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            margin-bottom: 15px;
            max-height: 150px;
            overflow-y: auto;
        }
        .ai-message {
            background-color: #e6f3ff;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            border-left: 4px solid #0066cc;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Add container with the custom CSS class
        st.markdown('<div class="ai-chat-container">', unsafe_allow_html=True)
        
        # Add reasoning history as separate markdown elements with newest first
        if st.session_state.ai_move_history and len(st.session_state.ai_move_history) > 0:
            # Reverse the order to show newest first
            for move_info in reversed(st.session_state.ai_move_history):
                move_num = move_info.get('move', '?')
                reasoning_text = move_info.get('reasoning', 'No explanation provided')
                st.markdown(
                    f'<div class="ai-message"><strong>Move {move_num}</strong>: {reasoning_text}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<em>Claude will explain its moves here...</em>", unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.header("Scoreboard")
    col_you, col_claude, col_ties = st.columns(3)
    
    with col_you:
        st.metric("You", st.session_state.human_score)
    
    with col_claude:
        st.metric("Claude", st.session_state.ai_score)
    
    with col_ties:
        st.metric("Ties", st.session_state.ties)
    
    # Game options
    st.subheader("Options")
    
    # Board size slider
    new_board_size = st.number_input(
        "Board Size:", 
        min_value=3, 
        max_value=8, 
        value=int(st.session_state.board_size),
        step=1,
        help="Choose the size of the board (e.g., 3 for a 3x3 board, 4 for a 4x4 board)"
    )
    
    # Check if board size has changed
    if new_board_size != st.session_state.board_size:
        # Update the board size
        st.session_state.board_size = new_board_size
        
        # Resize the board to match the new size while preserving existing moves
        old_board = st.session_state.board.copy()
        old_size = int(len(old_board) ** 0.5)  # Calculate old size from board length
        new_board = [" " for _ in range(new_board_size * new_board_size)]
        
        # Copy values from old board to new board where possible
        min_size = min(old_size, new_board_size)
        for row in range(min_size):
            for col in range(min_size):
                old_index = row * old_size + col
                new_index = row * new_board_size + col
                if old_index < len(old_board) and new_index < len(new_board):
                    new_board[new_index] = old_board[old_index]
        
        st.session_state.board = new_board
        st.rerun()
    
    # Let user choose their marker for the next game
    new_marker = st.radio("Choose your marker for next game:", options=["X", "O"], index=0 if st.session_state.human_marker == "X" else 1)
    if new_marker != st.session_state.human_marker:
        st.session_state.human_marker = new_marker
        st.session_state.ai_marker = "O" if new_marker == "X" else "X"
    
    # Reset scores button
    if st.button("Reset Scores"):
        st.session_state.human_score = 0
        st.session_state.ai_score = 0
        st.session_state.ties = 0
        st.session_state.game_count = 1
        st.success("Scores reset!")
        time.sleep(1)
        st.rerun()
    
    # Game instructions
    with st.expander("How to Play"):
        st.markdown(f"""
        1. You are playing against Claude, an AI.
        2. X always goes first, O always goes second.
        3. Click on an empty space to place your marker.
        4. The first player to get 3 in a row (horizontally, vertically, or diagonally) wins.
        5. If all spaces are filled and no one has 3 in a row, the game is a tie.
        6. You can change the board size using the input above - from 3x3 up to 8x8!
        
        Claude has been programmed to play an optimal strategy, so it will be challenging to win!
        """)