from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import json
import os
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Path to the JSON file for storing user bios
USER_BIOS_FILE = 'user_bios.json'

# Load bios from file or initialize an empty dictionary
if os.path.exists(USER_BIOS_FILE):
    with open(USER_BIOS_FILE, 'r') as file:
        user_bios = json.load(file)
else:
    user_bios = {}

messages_file = 'user_messages.json'

def load_messages():
    if os.path.exists(messages_file):
        with open(messages_file, 'r') as f:
            return json.load(f)
    return {}

def save_messages(messages):
    with open(messages_file, 'w') as f:
        json.dump(messages, f)

# Initialize matches dictionary
if 'matches' not in user_bios:
    user_bios['matches'] = {}


# Function to save bios to file
def save_bios_to_file():
    with open(USER_BIOS_FILE, 'w') as file:
        json.dump(user_bios, file)

@app.route('/')
def index():
    username = request.cookies.get('username')
    if username :
        return redirect(url_for('profile', username=username))
    else :
        return render_template('bio_home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the username exists and the password matches
        if username in user_bios and user_bios[username]['password'] == password:
            # Create a response object to set the cookie
            response = make_response(redirect(url_for('profile', username=username)))

            # Store the username in a cookie (e.g., valid for 30 minutes)
            response.set_cookie('username', username, max_age=1800,path='/')
            print(request.cookies.get('username'))
            print(request.cookies.get('username'))
            return response
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/create_bio', methods=['GET', 'POST'])
def create_bio():
    if request.method == 'POST':
        username = request.form['username']
        bio = request.form['bio']
        gender = request.form['gender']
        preferred_gender = request.form['preferred_gender']
        password = request.form['password']
        # Save the bio and additional info for the user
        user_bios[username] = {
            'bio': bio,
            'gender': gender,
            'preferred_gender': preferred_gender,
            'password': password,  # Save password (should use hashing for production)
            'likes': []
        }
        save_bios_to_file()  # Save the updated bios to the file
        response = make_response(redirect(url_for('profile', username=username)))

        # Store the username in a cookie (e.g., valid for 30 minutes)
        response.set_cookie('username', username, max_age=1800, path='/')
        print(request.cookies.get('username'))
        print(request.cookies.get('username'))
        return response

    return render_template('create_bio.html')

@app.route('/edit_bio', methods=['GET', 'POST'])
def edit_bio():
    username = request.cookies.get('username')
    if not username:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        bio = request.form['bio']
        gender = request.form['gender']
        preferred_gender = request.form['preferred_gender']
        # Update the user's bio and additional info
        user_bios[username]['bio'] = bio
        user_bios[username]['gender'] = gender
        user_bios[username]['preferred_gender'] = preferred_gender
        save_bios_to_file()  # Save the updated bios to the file
        flash('Bio updated successfully!', 'success')
        return redirect(url_for('profile', username=username))

    # Pre-fill the form with existing user info
    user_info = user_bios.get(username, {})
    return render_template('edit_bio.html', user_info=user_info)

@app.route('/profile/<username>')
def profile(username):
    user_info = user_bios.get(username, None)
    if user_info:
        bio = user_info['bio']
        gender = user_info['gender']
        preferred_gender = user_info['preferred_gender']
    else:
        bio = "This user hasn't created a bio yet."
        gender = preferred_gender = None
    return render_template('profile_view.html', username=username, bio=bio, gender=gender, preferred_gender=preferred_gender)

@app.route('/my_profile')
def my_profile():
    username = request.cookies.get('username')
    if username:
        return profile(username)
    else:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))

@app.route('/profile/<username>', methods=['GET'])
def view_profile(username):
    user_info = user_bios.get(username, {})
    matches = user_bios.get('matches', {}).get(username, [])

    return render_template('profile_view.html', user_info=user_info, matches=matches)


@app.route('/all_users', methods=['GET', 'POST'])
def all_users():
    username = request.cookies.get('username')  # Get the current user's username from the session

    # Load avatars from avatars.json
    with open('avatars.json', 'r') as f:
        avatars = json.load(f)

    # Get the preferred gender of the specified user
    user_info = user_bios.get(username, None)
    if user_info:
        preferred_gender = user_info['preferred_gender']
        # Filter users based on the preferred gender and exclude the current user
        filtered_users = {
            user: info for user, info in user_bios.items()
            if info.get('gender') == preferred_gender and user != username
        }

        if request.method == 'POST':
            liked_user = request.form['liked_user']
            if liked_user in user_bios:
                # Check if the current user has already liked the liked_user
                if liked_user in user_bios[username].get('likes', []):
                    # If already liked, unlike the user
                    user_bios[username]['likes'].remove(liked_user)

                    # Also remove from matches if they were matched
                    if liked_user in user_bios['matches'].get(username, []):
                        user_bios['matches'][username].remove(liked_user)
                        user_bios['matches'][liked_user].remove(username)

                    flash(f"You have unliked {liked_user}.")
                else:
                    # Add the like if not already liked
                    user_bios[username].setdefault('likes', []).append(liked_user)

                    # Check if the liked user also likes back to match them
                    if username in user_bios[liked_user].get('likes', []):
                        user_bios['matches'].setdefault(username, []).append(liked_user)
                        user_bios['matches'].setdefault(liked_user, []).append(username)

                    flash(f"You have liked {liked_user}.")

                save_bios_to_file()  # Save the updated data
    else:
        filtered_users = {}

    return render_template('all_users.html', users=filtered_users, avatars=avatars, current_user=username,
                           likes=user_bios[username].get('likes', []))

@app.route('/matches')
def matches():
    username = request.cookies.get('username')  # Get the current user's username from the session
    matches_list = user_bios.get('matches', {}).get(username, [])
    return render_template('matches.html', matches=matches_list, current_user=username)


@app.route('/logout')
def logout():
    response = redirect(url_for('login'))  # Redirect to login or home page
    response.delete_cookie('username') # Remove username from the session
    response.delete_cookie('username') # Remove username from the session
    flash('You have been logged out.', 'success')
    return response

def create_user_bio(username, bio, gender, preferred_gender, password):
    user_bios[username] = {
        'bio': bio,
        'gender': gender,
        'preferred_gender': preferred_gender,
        'likes': []  # Initialize an empty likes list
    }
    save_bios_to_file()


@app.route('/messages/<username>', methods=['GET', 'POST'])
def messages(username):
    current_username = request.cookies.get('username')
    user_info = user_bios.get(current_username, {})

    # Load existing messages
    all_messages = load_messages()

    # Sort the usernames alphabetically to create a consistent key
    if username is not None:
        user_pair = sorted([current_username, username])
        key = f"{user_pair[0]}_{user_pair[1]}"
    else:
        return redirect(url_for('login'))
    # Initialize the message list for the current conversation if it doesn't exist
    if key not in all_messages:
        all_messages[key] = []

    if request.method == 'POST':
        if 'hangman' in request.form:
            # Redirect to the Hangman game page
            return redirect(url_for('hangman', username=username))
        elif 'two_truths_and_a_lie' in request.form:
            # Redirect to the Two Truths and a Lie game page
            return redirect(url_for('two_truths_and_a_lie', username=username))
        else:
            # Get the message from the form
            message = request.form.get('message')
            # Store the message in the conversation
            if message:
                all_messages[key].append({"from": current_username, "message": message})
                save_messages(all_messages)

    # Retrieve messages for display
    messages_list = all_messages.get(key, [])

    return render_template('messages.html', username=username, user_info=user_info, messages=messages_list, current_username=current_username)

import random

@app.route('/two_truths_and_a_lie/<username>', methods=['GET', 'POST'])
def two_truths_and_a_lie(username):
    current_username = request.cookies.get('username')

    # Load existing messages
    all_messages = load_messages()

    # Sort the usernames to create a consistent key
    user_pair = sorted([current_username, username])
    key = f"{user_pair[0]}_{user_pair[1]}"

    if request.method == 'POST':
        # Get the two truths and one lie from the form
        truth1 = request.form.get('truth_1')
        truth2 = request.form.get('truth_2')
        lie = request.form.get('lie')

        if truth1 and truth2 and lie:
            # Create a list of truths and lie
            options = [truth1, truth2, lie]

            # Shuffle the list to randomize the order
            random.shuffle(options)

            if key not in all_messages:
                all_messages[key] = []

            # Store the shuffled options in the messages list
            all_messages[key].append({
                "from": current_username,
                "game": "two_truths_and_a_lie",
                "options": options,  # Shuffled truths and lie
                "lie": lie  # Still store the actual lie for comparison later
            })
            save_messages(all_messages)

            # Redirect back to messages page with a confirmation message
            flash('Two Truths and a Lie game has been sent!', 'success')
            return redirect(url_for('messages', username=username))

    return render_template('two_truths_and_a_lie.html', current_username=current_username)

@app.route('/play_two_truths_and_a_lie/<username>', methods=['GET', 'POST'])
def play_two_truths_and_a_lie(username):
    current_username = request.cookies.get('username')

    # Load existing messages
    all_messages = load_messages()

    # Sort the usernames to create a consistent key
    user_pair = sorted([current_username, username])
    key = f"{user_pair[0]}_{user_pair[1]}"

    # Get the most recent two truths and a lie game
    last_message = next((msg for msg in all_messages[key] if msg.get('game') == 'two_truths_and_a_lie'), None)

    if not last_message:
        flash('No Two Truths and a Lie game found.', 'danger')
        return redirect(url_for('messages', username=username))

    options = last_message['options']  # Shuffled list of options
    actual_lie = last_message['lie']  # The actual lie

    if request.method == 'POST':
        guessed_lie = request.form.get('guessed_lie')

        # Check if the guessed lie matches the actual lie
        if guessed_lie == actual_lie:
            flash('Correct! You found the lie!', 'success')
        else:
            flash('Incorrect! That was a truth.', 'danger')

        # After guessing, redirect to the messages page
        return redirect(url_for('messages', username=username))

    return render_template('play_two_truths_and_a_lie.html', options=options, current_username=current_username)


get_to_know_you_questions = {
    "What's your favorite animal?": "elephant",
    "What's your favorite color?": "blue",
    "What's your favorite movie?": "inception",
    "What's your favorite food?": "pizza",
    "What's your favorite hobby?": "reading",
}


@app.route('/hangman/<username>', methods=['GET', 'POST'])
def hangman(username):
    current_username = request.cookies.get('username')

    # Load existing messages
    all_messages = load_messages()

    # Sort the usernames to create a consistent key
    user_pair = sorted([current_username, username])
    key = f"{user_pair[0]}_{user_pair[1]}"

    if request.method == 'POST':
        # User submits their answer for the random question
        answer = request.form.get('answer')
        if answer:
            # Clean up the input: strip whitespace and convert to lowercase
            cleaned_answer = answer.strip().lower()

            # Clear previous hangman game messages

            if key not in all_messages:
                all_messages[key] = []
            all_messages[key] = [msg for msg in all_messages[key] if msg.get('game') != 'hangman']

            # Store the chosen answer in the messages list
            all_messages[key].append({
                "from": current_username,
                "game": "hangman",
                "word": cleaned_answer,  # Use cleaned answer
                "guessed_letters": [],  # Initialize guessed_letters as an empty list
                "game_status": "ongoing"  # Initialize game status
            })
            save_messages(all_messages)

            # Redirect back to messages page with a confirmation message
            flash('Hangman game has been sent!', 'success')  # Use flash to show a success message
            return redirect(url_for('messages', username=username))

    # Get a random question from the list
    random_question = random.choice(list(get_to_know_you_questions.keys()))

    return render_template('hangman.html', question=random_question, current_username=current_username)


@app.route('/play_hangman/<username>', methods=['GET', 'POST'])
def play_hangman(username):
    current_username = request.cookies.get('username')

    # Check if the current user is the recipient of the Hangman game
    if current_username == username:
        return "You are not authorized to play this Hangman game.", 403  # Forbidden

    # Load existing messages
    all_messages = load_messages()

    # Sort the usernames to create a consistent key
    user_pair = sorted([current_username, username])
    key = f"{user_pair[0]}_{user_pair[1]}"

    # Initialize the last_message variable
    # Retrieve the last message related to the Hangman game
    last_message = next((msg for msg in all_messages[key] if msg.get('game') == 'hangman'), None)

    if not last_message:
        return "No Hangman game found."

    # Check if the game is already finished
    if last_message.get('game_status') == 'finished':
        return render_template('hangman_finished.html', username=username)

    # Ensure the key exists in the all_messages dictionary
    if key in all_messages:
        last_message = next((msg for msg in all_messages[key] if msg.get('game') == 'hangman'), None)

    # Initialize variables safely
    word = last_message['word'] if last_message else ''
    guessed_letters = last_message.get('guessed_letters', []) if last_message else []

    # Initialize a variable to determine if the game has been won
    game_won = False

    if request.method == 'POST':
        guess = request.form.get('guess', '').lower()
        if guess and len(guess) == 1 and guess not in guessed_letters:
            guessed_letters.append(guess)
            # Save the updated guessed letters back to the messages
            if last_message:
                last_message['guessed_letters'] = guessed_letters
            else:
                all_messages[key].append({
                    "from": current_username,
                    "game": "hangman",
                    "word": word,
                    "guessed_letters": guessed_letters
                })
            save_messages(all_messages)

    word_display = ''.join([letter if letter in guessed_letters else '_' for letter in word])

    # Check if the game has been won
    if all(letter in guessed_letters for letter in word):
        game_won = True

        # Handle winning logic
        if game_won:  # This should be your game win condition
            # Send a completion message to both users
            completion_message = f"{current_username} has won the Hangman game!"
            all_messages[key].append({"from": "Game", "message": completion_message})

            # Set the game status to finished and remove the link message
            last_message['game_status'] = 'finished'
            save_messages(all_messages)

            # Redirect to the hangman_finished.html page
            return render_template('hangman_finished.html', username=username)

    return render_template('play_hangman.html', username=username, word_display=word_display, guessed_letters=', '.join(guessed_letters), game_won=game_won)

@app.route('/clear_messages/<username>', methods=['POST'])
def clear_messages(username):
    current_username = request.cookies.get('username')

    # Load existing messages
    all_messages = load_messages()

    # Sort the usernames to create a consistent key
    user_pair = sorted([current_username, username])
    key = f"{user_pair[0]}_{user_pair[1]}"

    # Remove all messages for this conversation
    if key in all_messages:
        all_messages[key] = []  # Clear the message list for this conversation
        save_messages(all_messages)

    flash('Messages have been cleared.', 'success')
    return redirect(url_for('messages', username=username))


# File to store avatar customizations
AVATAR_FILE = 'avatars.json'


# Helper function to load avatars from file
def load_avatars():
    if os.path.exists(AVATAR_FILE):
        with open(AVATAR_FILE, 'r') as file:
            return json.load(file)
    return {}


# Helper function to save avatars to file
def save_avatar(username, avatar_data):
    avatars = load_avatars()
    avatars[username] = avatar_data
    with open(AVATAR_FILE, 'w') as file:
        json.dump(avatars, file, indent=4)


# Route for avatar customization
@app.route('/customize-avatar', methods=['GET', 'POST'])
def customize_avatar():
    username = request.cookies.get('username')

    if not username:
        return "You need to be logged in to customize your avatar.", 403

    avatars = load_avatars()
    avatar_data = avatars.get(username, None)  # Get user's existing avatar if it exists

    if request.method == 'POST':
        # Get the selected options from the form
        skin_tone = request.form.get('skin_tone')
        hair_color = request.form.get('hair_color')
        hairstyle = request.form.get('hairstyle')

        # Get additional features
        hat = request.form.get('hat') == 'on'  # Checkbox for hat
        bandana = request.form.get('bandana') == 'on'  # Checkbox for bandana
        glasses = request.form.get('glasses') == 'on'  # Checkbox for glasses
        pipe = request.form.get('pipe') == 'on'  # Checkbox for pipe

        # Create avatar data to store
        avatar_data = {
            'skin_tone': skin_tone,
            'hair_color': hair_color,
            'hairstyle': hairstyle,
            'hat': hat,
            'bandana': bandana,
            'glasses': glasses,
            'pipe': pipe
        }

        # Save avatar to the JSON file
        save_avatar(username, avatar_data)

        return redirect(url_for('my_profile'))  # Redirect to avatar display page

    # Predefined options for hairstyles and facial features
    hairstyles = ['hair_one', 'hair_two', 'hair_three', 'hair_four', 'hair_five', 'hair_six']  # Use lowercase for image filenames
    #facial_features = ['beard', 'moustache', 'freckles', 'glasses']

    # If the user has an existing avatar, load its details; otherwise, set default values
    return render_template(
        'customize_avatar.html',
        hairstyles=hairstyles,
        avatar_data=avatar_data  # Pass existing avatar data if available
    )


if __name__ == '__main__':
    app.run(debug=True)
