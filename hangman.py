from flask import Flask, render_template, session, redirect, request, url_for

app = Flask(__name__)
app.secret_key = 'replace_this_with_a_secure_random_key'

# Constants
MAX_ATTEMPTS = 6

def initialize_game():
    """Initialize the game session"""
    session['word'] = ''
    session['correct_guessed_letters'] = []
    session['incorrect_guessed_letters'] = []
    session['attempts_left'] = MAX_ATTEMPTS
    session['game_over'] = False
    session['victory'] = False

def masked_word():
    """Return the word with underscores for letters not guessed correctly"""
    word = session.get('word', '')
    correct_guesses = session.get('correct_guessed_letters', [])
    return ''.join([letter if letter in correct_guesses else '_' for letter in word])

@app.route('/')
def index():
    if 'word' not in session or session['word'] == '':
        return redirect(url_for('set_word'))
    return redirect(url_for('play'))

@app.route('/set-word', methods=['GET', 'POST'])
def set_word():
    if request.method == 'POST':
        word = request.form['word'].lower()
        session['word'] = word
        session['correct_guessed_letters'] = []
        session['incorrect_guessed_letters'] = []
        session['attempts_left'] = MAX_ATTEMPTS
        session['game_over'] = False
        session['victory'] = False
        return redirect(url_for('play'))
    return render_template('set_word.html')

@app.route('/play', methods=['GET', 'POST'])
def play():
    if 'word' not in session or session['word'] == '':
        return redirect(url_for('set_word'))

    if request.method == 'POST' and not session['game_over']:
        guess = request.form['guess'].lower()

        # Ensure single-character guesses
        if len(guess) != 1 or not guess.isalpha():
            return redirect(url_for('play'))

        # Check if the letter has already been guessed
        if guess not in session['correct_guessed_letters'] and guess not in session['incorrect_guessed_letters']:
            if guess in session['word']:
                session['correct_guessed_letters'].append(guess)
                session.modified = True  # Explicitly tell Flask the session has been modified
                print(f"Correct guesses updated: {session['correct_guessed_letters']}")
            else:
                session['incorrect_guessed_letters'].append(guess)
                session['attempts_left'] -= 1
                session.modified = True  # Explicitly tell Flask the session has been modified
                print(f"Incorrect guesses updated: {session['incorrect_guessed_letters']}")

        # Check if the player has won or lost
        if all([letter in session['correct_guessed_letters'] for letter in session['word']]):
            session['victory'] = True
            session['game_over'] = True
        elif session['attempts_left'] <= 0:
            session['game_over'] = True

    return render_template('play.html',
                           masked_word=masked_word(),
                           attempts_left=session['attempts_left'],
                           correct_guessed_letters=session['correct_guessed_letters'],
                           incorrect_guessed_letters=session['incorrect_guessed_letters'],
                           game_over=session['game_over'],
                           victory=session['victory'],
                           word=session['word'] if session['game_over'] else None)

@app.route('/reset')
def reset():
    initialize_game()
    return redirect(url_for('set_word'))

if __name__ == '__main__':
    app.run(debug=True)
