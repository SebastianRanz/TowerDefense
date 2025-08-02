from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from modules.map_generator import MapGenerator

# Initialize Flask app
app = Flask(__name__)

# --- Configuration for a secure app and database ---
# TODO: Change this secret key to a long, random string in production.
app.config['SECRET_KEY'] = 'your-very-secret-key-that-you-should-change'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ...existing code...
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Progression fields
    level = db.Column(db.Integer, nullable=False, default=1)
    xp = db.Column(db.Integer, nullable=False, default=0)
    selected_map = db.Column(db.String(100), nullable=False, default='holy_c_path')
    gold = db.Column(db.Integer, nullable=False, default=500)
    lives = db.Column(db.Integer, nullable=False, default=20)
    wave = db.Column(db.Integer, nullable=False, default=1)
    score = db.Column(db.Integer, nullable=False, default=0)
    unlocked_towers = db.Column(db.String(500), nullable=False, default='["basic"]')  # JSON string of tower IDs
    
    def add_xp(self, amount):
        """Add XP and handle level ups"""
        self.xp += amount
        with open('config/progression.json', 'r') as f:
            progression = json.load(f)
        
        # Check for level up
        next_level = self.level + 1
        next_level_data = next((x for x in progression['levels'] if x['level'] == next_level), None)
        
        if next_level_data and self.xp >= next_level_data['xp_required']:
            self.level = next_level
            self._update_unlocked_towers(progression['tower_unlocks'])
            return True
        return False
    
    def _update_unlocked_towers(self, tower_unlocks):
        """Update available towers based on level and XP"""
        current_towers = json.loads(self.unlocked_towers)
        for tower_id, requirements in tower_unlocks.items():
            if (self.level >= requirements['level_required'] and 
                self.xp >= requirements['xp_required'] and 
                tower_id not in current_towers):
                current_towers.append(tower_id)
        self.unlocked_towers = json.dumps(current_towers)

    # Method to set a hashed password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check a password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# --- CORRECTED: User loader callback for Flask-Login (uses modern SQLAlchemy) ---
@login_manager.user_loader
def load_user(user_id):
    """
    This function is required by Flask-Login. It loads a user from the
    database by their ID. The modern SQLAlchemy way is to use db.session.get().
    """
    return db.session.get(User, int(user_id))


# --- Routes for user authentication ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# --- Main application routes, now protected with @login_required ---
@app.route('/')
@login_required
def index():
    return render_template('index_stefan.html', game_title="Towerdefender", username=current_user.username)

@app.route('/game', methods=['GET', 'POST'])
@login_required
def game():
    if request.method == 'POST':
        # This route is used for initial page load or a redirect, no JSON data here
        return jsonify({'redirect': '/game'})
    
    # Use current_user to get the logged-in user's progression data
    gamestate = {
        'player_name': current_user.username,
        'selected_map': current_user.selected_map,
        'gold': current_user.gold,
        'lives': current_user.lives,
        'wave': current_user.wave,
        'score': current_user.score
    }
    return render_template('game.html', gamestate=gamestate)

@app.route('/options', methods=['POST'])
@login_required
def options():
    return jsonify({'redirect': '/options'})

@app.route('/credits', methods=['POST'])
@login_required
def credits():
    return jsonify({'redirect': '/credits'})


# --- API endpoints, now linked to the database ---
@app.route('/api/maps', methods=['GET'])
def get_maps():
    """Returns the map data from a JSON file."""
    return send_file('map_data/maps.json')

@app.route('/api/player', methods=['GET', 'POST'])
@login_required
def player_data():
    """
    Handles GET/POST requests for the current user's player data,
    loading and saving directly to the database.
    """
    if request.method == 'GET':
        return jsonify({
            "health": 100, # This is a temporary value, not stored
            "gold": current_user.gold,
            "lives": current_user.lives,
            "current_wave": current_user.wave,
            "score": current_user.score,
            "username": current_user.username
        })
    elif request.method == 'POST':
        data = request.get_json()
        
        # Update user attributes from the POST data
        current_user.gold = data.get('gold', current_user.gold)
        current_user.lives = data.get('lives', current_user.lives)
        current_user.wave = data.get('current_wave', current_user.wave)
        current_user.score = data.get('score', current_user.score)
        
        db.session.commit()
        return jsonify({"status": "Updated", "data": data})


@app.route('/api/gamestate', methods=['GET', 'POST'])
@login_required
def gamestate_api():
    if request.method == 'GET':
        gamestate_data = {
            'player_name': current_user.username,
            'selected_map': current_user.selected_map,
            'gold': current_user.gold,
            'lives': current_user.lives,
            'wave': current_user.wave,
            'score': current_user.score,
            'level': current_user.level,
            'xp': current_user.xp,
            'unlocked_towers': json.loads(current_user.unlocked_towers)
        }
        return jsonify(gamestate_data)
    elif request.method == 'POST':
        data = request.get_json()
        
        # Update user attributes from the POST data
        if 'selected_map' in data:
            current_user.selected_map = data['selected_map']
        
        # Also update other fields that might be sent in the gamestate post
        current_user.gold = data.get('gold', current_user.gold)
        current_user.lives = data.get('lives', current_user.lives)
        current_user.wave = data.get('wave', current_user.wave)
        current_user.score = data.get('score', current_user.score)

        db.session.commit()
        return jsonify({
            "status": "Updated", 
            "gamestate": {
                'player_name': current_user.username,
                'selected_map': current_user.selected_map
            }
        })


@app.route('/api/progression', methods=['GET', 'POST'])
@login_required
def progression():
    """Handle progression-related requests"""
    if request.method == 'GET':
        # Load progression template
        with open('config/progression.json', 'r') as f:
            progression_data = json.load(f)
        
        # Get current level data
        current_level_data = next(
            (x for x in progression_data['levels'] if x['level'] == current_user.level), 
            None
        )
        
        return jsonify({
            'current_level': current_user.level,
            'current_xp': current_user.xp,
            'unlocked_towers': json.loads(current_user.unlocked_towers),
            'level_data': current_level_data
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Handle XP gain
        if 'xp_gained' in data:
            level_up = current_user.add_xp(data['xp_gained'])
            
            # Save changes
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'level_up': level_up,
                'new_level': current_user.level,
                'new_xp': current_user.xp,
                'unlocked_towers': json.loads(current_user.unlocked_towers)
            })

        return jsonify({'status': 'error', 'message': 'Invalid data'})



@app.route('/api/towers', methods=['GET'])
def get_towers():
    """Returns the tower data from a JSON file."""
    with open('tower_data/tower_data.json', 'r') as f:
        tower_data = json.load(f)
    return jsonify(tower_data)


@app.route('/api/enemies', methods=['GET'])
def get_enemies():
    """Returns the enemy data from a JSON file."""
    with open('enemy_data/enemy_data.json', 'r') as f:
        enemy_data = json.load(f)
    return jsonify(enemy_data)


# --- Map Generator API Endpoints ---
# Initialize map generator
map_generator = MapGenerator()

@app.route('/generator')
@login_required
def generator():
    """Map Generator page"""
    return render_template('generator.html', username=current_user.username)

@app.route('/api/generate-map', methods=['POST'])
@login_required
def generate_map():
    """Generate a new map with specified parameters"""
    try:
        data = request.get_json()
        
        difficulty = data.get('difficulty', 'medium')
        theme = data.get('theme', 'forest')
        size = data.get('size', 'medium')
        complexity = data.get('complexity', 'curved')
        custom_name = data.get('name', None)
        
        # Generate the map
        generated_map = map_generator.generate_map(
            difficulty=difficulty,
            theme=theme,
            size=size,
            complexity=complexity,
            custom_name=custom_name
        )
        
        return jsonify({
            'status': 'success',
            'map': generated_map
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/save-custom-map', methods=['POST'])
@login_required
def save_custom_map():
    """Save a custom generated map"""
    try:
        data = request.get_json()
        map_data = data.get('map')
        
        if not map_data:
            return jsonify({'status': 'error', 'message': 'No map data provided'}), 400
        
        # Load existing maps
        with open('map_data/maps.json', 'r') as f:
            maps = json.load(f)
        
        # Add the new map
        maps.append(map_data)
        
        # Save back to file
        with open('map_data/maps.json', 'w') as f:
            json.dump(maps, f, indent=4)
        
        return jsonify({
            'status': 'success',
            'message': 'Map saved successfully',
            'map_id': map_data['id']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/themes', methods=['GET'])
def get_themes():
    """Get available themes for map generation"""
    return jsonify(map_generator.get_themes())

@app.route('/api/generator-options', methods=['GET'])
def get_generator_options():
    """Get all available options for map generation"""
    return jsonify({
        'themes': map_generator.get_themes(),
        'difficulties': map_generator.get_difficulties(),
        'complexities': map_generator.get_complexities(),
        'sizes': ['small', 'medium', 'large']
    })

@app.route('/api/get-saved-maps', methods=['GET'])
@login_required
def get_saved_maps():
    """Get all saved maps for the map loader"""
    try:
        with open('map_data/maps.json', 'r') as f:
            all_maps = json.load(f)
        
        # Filter and format maps for the loader
        saved_maps = []
        for i, map_data in enumerate(all_maps):
            # Ensure all required fields exist with defaults
            map_id = map_data.get('id', i + 1)
            map_name = map_data.get('name', f'Map {map_id}')
            map_theme = map_data.get('theme', 'forest')
            map_difficulty = map_data.get('difficulty', 'medium')
            
            # Handle dimensions - some maps might not have this field
            if 'dimensions' in map_data:
                dimensions = map_data['dimensions']
            else:
                # Calculate dimensions from path data if available
                max_x = max_y = 0
                if 'path' in map_data and map_data['path']:
                    for point in map_data['path']:
                        max_x = max(max_x, point.get('x', 0))
                        max_y = max(max_y, point.get('y', 0))
                if 'start' in map_data:
                    max_x = max(max_x, map_data['start'].get('x', 0))
                    max_y = max(max_y, map_data['start'].get('y', 0))
                
                dimensions = {
                    'width': max_x + 5,  # Add some padding
                    'height': max_y + 5
                }
            
            # Handle obstacles
            obstacles = map_data.get('obstacles', [])
            
            # Add creation timestamp if not present
            created_at = map_data.get('created_at', f'2024-01-{str(i+1).zfill(2)}T00:00:00Z')
            
            saved_maps.append({
                'id': str(map_id),  # Ensure ID is string for consistency
                'name': map_name,
                'theme': map_theme,
                'difficulty': map_difficulty,
                'dimensions': dimensions,
                'obstacles': obstacles,
                'created_at': created_at
            })
        
        # Sort by creation date (newest first)
        saved_maps.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'maps': saved_maps
        })
        
    except Exception as e:
        print(f"Error in get_saved_maps: {str(e)}")  # Debug logging
        return jsonify({
            'status': 'error',
            'message': f'Failed to load maps: {str(e)}'
        }), 500

@app.route('/api/load-map/<map_id>', methods=['GET'])
@login_required
def load_map(map_id):
    """Load a specific map by ID"""
    try:
        with open('map_data/maps.json', 'r') as f:
            all_maps = json.load(f)
        
        # Find the map with the specified ID (handle both string and int IDs)
        target_map = None
        for map_data in all_maps:
            # Compare both as strings and as integers to handle mixed ID types
            current_id = map_data.get('id')
            if (str(current_id) == str(map_id) or 
                (isinstance(current_id, int) and current_id == int(map_id)) or
                (isinstance(current_id, str) and current_id == map_id)):
                target_map = map_data
                break
        
        if not target_map:
            return jsonify({
                'status': 'error',
                'message': f'Map with ID {map_id} not found'
            }), 404
        
        # Ensure the map has all required fields for the editor
        if 'theme' not in target_map:
            target_map['theme'] = 'forest'
        if 'complexity' not in target_map:
            target_map['complexity'] = 'curved'
        if 'dimensions' not in target_map:
            # Calculate dimensions from path data
            max_x = max_y = 0
            if 'path' in target_map and target_map['path']:
                for point in target_map['path']:
                    max_x = max(max_x, point.get('x', 0))
                    max_y = max(max_y, point.get('y', 0))
            if 'start' in target_map:
                max_x = max(max_x, target_map['start'].get('x', 0))
                max_y = max(max_y, target_map['start'].get('y', 0))
            
            target_map['dimensions'] = {
                'width': max_x + 5,
                'height': max_y + 5
            }
        
        return jsonify({
            'status': 'success',
            'map': target_map
        })
        
    except Exception as e:
        print(f"Error in load_map: {str(e)}")  # Debug logging
        return jsonify({
            'status': 'error',
            'message': f'Failed to load map: {str(e)}'
        }), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
