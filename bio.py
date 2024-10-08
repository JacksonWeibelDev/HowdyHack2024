from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

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

# Initialize matches dictionary
if 'matches' not in user_bios:
    user_bios['matches'] = {}


# Function to save bios to file
def save_bios_to_file():
    with open(USER_BIOS_FILE, 'w') as file:
        json.dump(user_bios, file)

@app.route('/')
def index():
    return render_template('bio_home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the username exists and the password matches
        if username in user_bios and user_bios[username]['password'] == password:
            session['username'] = username
            flash(f'Logged in as {username}', 'success')
            return redirect(url_for('profile', username=username))
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
            'password': password  # Save password (should use hashing for production)
        }
        save_bios_to_file()  # Save the updated bios to the file
        return redirect(url_for('profile', username=username))
    return render_template('create_bio.html')

@app.route('/edit_bio', methods=['GET', 'POST'])
def edit_bio():
    username = session.get('username')
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
    username = session.get('username')
    if username:
        return profile(username)
    else:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))

@app.route('/all_users', methods=['GET', 'POST'])
def all_users():
    username = session.get('username')  # Get the current user's username from the session

    # Get the preferred gender of the specified user
    user_info = user_bios.get(username, None)
    if user_info:
        preferred_gender = user_info['preferred_gender']
        # Filter users based on the preferred gender and exclude the current user
        filtered_users = {
            user: info for user, info in user_bios.items()
            if 'gender' in info and info['gender'] == preferred_gender and user != username
        }

        if request.method == 'POST':
            liked_user = request.form['liked_user']
            if liked_user in user_bios:
                # Check if the current user has already liked the liked_user
                if liked_user not in user_bios[username].get('likes', []):
                    # Add like only if it is not already liked
                    user_bios[username].setdefault('likes', []).append(liked_user)

                    # Check for matches only if the liked user also likes back
                    if username in user_bios[liked_user].get('likes', []):
                        user_bios['matches'].setdefault(username, []).append(liked_user)
                        user_bios['matches'].setdefault(liked_user, []).append(username)

                    save_bios_to_file()  # Save updated bios
                else:
                    flash(f"You've already liked {liked_user}.")

    else:
        filtered_users = {}

    return render_template('all_users.html', users=filtered_users, current_user=username, likes=user_bios[username].get('likes', []))


@app.route('/matches')
def matches():
    username = session.get('username')  # Get the current user's username from the session
    matches_list = user_bios.get('matches', {}).get(username, [])
    return render_template('matches.html', matches=matches_list, current_user=username)


@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

def create_user_bio(username, bio, gender, preferred_gender, password):
    user_bios[username] = {
        'bio': bio,
        'gender': gender,
        'preferred_gender': preferred_gender,
        'likes': []  # Initialize an empty likes list
    }
    save_bios_to_file()



if __name__ == '__main__':
    app.run(debug=True)
