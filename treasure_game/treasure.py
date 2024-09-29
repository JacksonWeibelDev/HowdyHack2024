from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Placeholder for user treasures and game state
games = {}
mini_challenges = [
    "Name three things you have in common.",
    "Share a memorable experience.",
    "What's your biggest dream?",
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['GET', 'POST'])
def start_game():
    if request.method == 'POST':
        username = request.form['username']
        treasure = request.form['treasure']
        game_id = request.form['game_id']

        # Initialize game if it doesn't exist
        if game_id not in games:
            games[game_id] = {'players': {}, 'questions': [], 'answers': {}, 'mini_challenges': [], 'game_ended': False, 'winner': None}

        # Store player info
        games[game_id]['players'][username] = {'treasure': treasure, 'questions_asked': []}
        session['username'] = username
        session['game_id'] = game_id

        return redirect(url_for('game', game_id=game_id))
    return render_template('start_game.html')

@app.route('/game/<game_id>', methods=['GET', 'POST'])
def game(game_id):
    username = session.get('username')
    if not username or game_id not in games:
        flash('You need to start the game first!', 'danger')
        return redirect(url_for('start_game'))

    if request.method == 'POST':
        action = request.form['action']
        if action == 'ask_question':
            question = request.form['question']
            games[game_id]['questions'].append((username, question))  # Store question
            games[game_id]['players'][username]['questions_asked'].append(question)  # Store user's questions
            games[game_id]['answers'][question] = None  # Initialize answer space
            flash(f'{username} asked: {question}', 'info')
        elif action == 'guess':
            guess = request.form['guess']
            partner_username = [user for user in games[game_id]['players'] if user != username]
            if partner_username:
                partner_username = partner_username[0]
                partner_treasure = games[game_id]['players'][partner_username]['treasure']
                if guess == partner_treasure:
                    games[game_id]['game_ended'] = True
                    games[game_id]['winner'] = username
                    flash(f'You guessed correctly! {username} wins!', 'success')
                else:
                    flash('Try again!', 'warning')
        elif action == 'answer_question':
            question = request.form['question']
            answer = request.form['answer']
            if question in games[game_id]['answers']:
                games[game_id]['answers'][question] = answer  # Store answer
                flash(f'{username} answered: {answer}', 'info')

    # Random mini-challenge
    challenge = random.choice(mini_challenges)

    # Get the partner's username
    partner_username = None
    if len(games[game_id]['players']) > 1:
        partner_username = [user for user in games[game_id]['players'] if user != username][0]

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'questions': games[game_id]['questions'],
            'answers': games[game_id]['answers'],
            'challenge': challenge,
            'partner_username': partner_username,
            'game_ended': games[game_id]['game_ended'],
            'winner': games[game_id]['winner']
        })

    return render_template('game.html', username=username, game_id=game_id, challenge=challenge,
                           questions=games[game_id]['questions'],
                           answers=games[game_id]['answers'],
                           partner_username=partner_username,
                           game_ended=games[game_id]['game_ended'],
                           winner=games[game_id]['winner'])

@app.route('/end_game')
def end_game():
    session.pop('username', None)
    session.pop('game_id', None)
    flash('Game ended. Thanks for playing!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
