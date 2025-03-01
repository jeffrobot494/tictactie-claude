import streamlit as st
import random
import time
import os
from dotenv import load_dotenv
import anthropic

# Try to load environment variables
try:
    load_dotenv()
except ImportError:
    pass

# Initialize Anthropic client
api_key = os.getenv("ANTHROPIC_API_KEY")

# Set page config
st.set_page_config(
    page_title="Tic Tac Toe vs Claude",
    page_icon="🎮",
    layout="centered"
)

# Set up session state
if 'board' not in st.session_state:
    st.session_state.board = [" " for _ in range(9)]
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
    # Check rows
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] != " ":
            return board[i]
    # Check columns
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] != " ":
            return board[i]
    # Check diagonals
    if board[0] == board[4] == board[8] != " ":
        return board[0]
    if board[2] == board[4] == board[6] != " ":
        return board[2]
    # Check for tie
    if " " not in board:
        return "Tie"
    return None

def get_ai_move(board, ai_marker, human_marker):
    # Format the board state for Claude
    board_str = f"""
    {board[0]}|{board[1]}|{board[2]}
    -+-+-
    {board[3]}|{board[4]}|{board[5]}
    -+-+-
    {board[6]}|{board[7]}|{board[8]}
    """
    
    prompt = f"""
    We're playing Tic Tac Toe. YOU are playing as '{ai_marker}' and I (the human) am playing as '{human_marker}'.
    
    IMPORTANT: To be absolutely clear:
    - All '{ai_marker}' marks on the board are YOUR marks
    - All '{human_marker}' marks on the board are MY marks (the human player)
    - You can only win by getting three '{ai_marker}' marks in a row
    - I can only win by getting three '{human_marker}' marks in a row
    - You cannot use my '{human_marker}' marks to form your winning line
    
    CRITICAL: Take your time to carefully read and understand the current board state. 
    Look at EACH position to identify ALL '{human_marker}' and '{ai_marker}' markers.
    Check for potential winning lines in ALL directions (rows, columns, and diagonals).
    
    The current board state is:
    
    {board_str}
    
    It's your turn. Make your move by placing another '{ai_marker}' mark on the board.
    Choose the index number (0-8) of an empty position.
    
    The board positions are numbered as follows:
    0|1|2
    -+-+-
    3|4|5
    -+-+-
    6|7|8
    
    Please explain your reasoning in 1-2 sentences, then provide your move.
    Format your response like this:
    
    [reasoning] I am choosing position X because... [/reasoning]
    
    X
    
    Where X is a single number 0-8 representing an empty position on the board.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=300,
            temperature=0.2,
            system="""You are playing Tic Tac Toe against a human player.

IMPORTANT - YOU MUST REMEMBER WHICH MARKER IS YOURS:
- If you're playing as X: All X marks on the board are YOUR marks, all O marks are the HUMAN's
- If you're playing as O: All O marks on the board are YOUR marks, all X marks are the HUMAN's
- You can only win by getting three of YOUR OWN markers in a row
- You CANNOT win by getting three of the HUMAN's markers in a row
- Always pay careful attention to which marker is yours in the current game

The rules of Tic Tac Toe are:
1. The board is a 3x3 grid numbered 0-8 as follows:
   0|1|2
   -+-+-
   3|4|5
   -+-+-
   6|7|8
2. X always goes first, O always goes second
3. Players take turns placing their marker on an empty space
4. The first player to get 3 of their OWN markers in a row (horizontal, vertical, or diagonal) wins
5. If all spaces are filled and no one has 3 in a row, the game is a tie

CAREFUL ANALYSIS IS REQUIRED:
- Take time to visualize the entire board layout
- Check EVERY position on the board for both your markers and the human's markers
- Scan ALL rows, columns, and both diagonals for potential winning lines or threats
- Double-check your understanding before making your move
- Being careful is more important than being quick

Respond with a reasoning explanation followed by a single number 0-8 representing your move position.""",
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
        for char in full_response:
            if char.isdigit() and 0 <= int(char) <= 8:
                move = int(char)
                # Verify it's a valid move
                if 0 <= move <= 8 and board[move] == " ":
                    return move
        
        # If we couldn't parse a valid move, find the first empty space
        for i in range(9):
            if board[i] == " ":
                return i
                
    except Exception as e:
        st.error(f"Error getting AI move: {e}")
        # Fallback: find first empty space
        for i in range(9):
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
    st.session_state.board = [" " for _ in range(9)]
    st.session_state.current_player = random.choice(['X', 'O'])
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.game_count += 1
    # Reset the AI reasoning for the new game
    st.session_state.ai_reasoning = ""
    # Note: ai_move_history is cleared in the Play Again button click handler

# UI elements
col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"Game #{st.session_state.game_count}")
    
    # Who goes first info
    if st.session_state.current_player == st.session_state.human_marker:
        st.info(f"You go first! You are '{st.session_state.human_marker}'")
    else:
        st.info(f"Claude goes first! You are '{st.session_state.human_marker}'")
    
    # Display the current board state with a simple, reliable approach
    st.subheader("Game Board")
    
    # Create three rows of three cells each
    for row in range(3):
        # Create a row with equal columns
        cols = st.columns(3)
        
        for col in range(3):
            index = row * 3 + col
            value = st.session_state.board[index]
            
            with cols[col]:
                # Create a consistent-sized cell with fixed height
                cell_container = st.container()
                
                # Add spacing above for consistent height
                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                
                # Style based on cell content
                if value == "X":
                    # Blue X
                    st.markdown(
                        "<div style='background-color:#e6f3ff; border:2px solid #0066cc; "
                        "height:80px; display:flex; justify-content:center; align-items:center; "
                        "font-size:40px; font-weight:bold; color:blue;'>X</div>",
                        unsafe_allow_html=True
                    )
                elif value == "O":
                    # Red O
                    st.markdown(
                        "<div style='background-color:#fff0f0; border:2px solid #cc0000; "
                        "height:80px; display:flex; justify-content:center; align-items:center; "
                        "font-size:40px; font-weight:bold; color:red;'>O</div>",
                        unsafe_allow_html=True
                    )
                else:
                    # For empty cells, we'll use a very simple approach
                    is_clickable = not st.session_state.game_over and st.session_state.current_player == st.session_state.human_marker
                    
                    if is_clickable:
                        # Use a regular button that looks like an empty cell
                        button_style = """
                        <style>
                        div[data-testid="stButton"] > button {
                            background-color: #f5f5f5;
                            border: 2px solid #cccccc;
                            border-radius: 4px;
                            color: transparent;
                            height: 80px;
                            width: 100%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }
                        div[data-testid="stButton"] > button:hover {
                            background-color: #e5e5e5;
                            border-color: #999999;
                        }
                        </style>
                        """
                        st.markdown(button_style, unsafe_allow_html=True)
                        
                        # Create a plain button styled to look like an empty cell
                        if st.button(" ", key=f"cell_{index}"):
                            make_move(index)
                            st.rerun()
                    else:
                        # Display a non-clickable empty cell
                        empty_cell_html = "<div style='background-color:#f5f5f5; border:2px solid #cccccc; " \
                                        "height:80px; display:flex; justify-content:center; " \
                                        "align-items:center; border-radius: 4px;'></div>"
                        st.markdown(empty_cell_html, unsafe_allow_html=True)
                
                # Add spacing below for consistent height
                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
    
    # Game status message and Play Again button (directly below the board)
    if st.session_state.game_over:
        status_container = st.container()
        with status_container:
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
    else:
        # Add some space when game is active
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    
    # Handle AI's turn (do this below the game status for state management)
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
                # Debug info
                print(f"Added AI move {ai_move} with reasoning: {reasoning}")
                
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
        
        # Create a container for the chat messages with the custom class
        chat_container = st.container()
        
        # Add a container with the custom CSS class
        st.markdown('<div class="ai-chat-container">', unsafe_allow_html=True)
        
        # Debugging info about history
        print(f"AI move history: {st.session_state.ai_move_history}")
        
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
        st.markdown("""
        1. You are playing against Claude, an AI.
        2. X always goes first, O goes second.
        3. Click on an empty space to place your marker.
        4. The first player to get 3 in a row (horizontally, vertically, or diagonally) wins.
        5. If all spaces are filled and no one has 3 in a row, the game is a tie.
        
        The game board positions are numbered as follows:
        ```
        0 | 1 | 2
        ---------
        3 | 4 | 5
        ---------
        6 | 7 | 8
        ```
        
        Claude has been programmed to play an optimal strategy, so it will be challenging to win!
        """)