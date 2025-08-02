from flask import Flask, render_template, request, jsonify, send_file


app = Flask(__name__)


gamestate = {
    'player_name': 'Player1',
    'selected_map': 'holy_c_path',
}

@app.route('/')
def index():
    return render_template('index_stefan.html', game_title="Towerdefender")

@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == 'POST':
        return jsonify({'redirect': '/game'})
    return render_template('game.html', gamestate=gamestate)

@app.route('/options', methods=['POST'])
def options():
    return jsonify({'redirect': '/options'})

@app.route('/credits', methods=['POST'])
def credits():
    return jsonify({'redirect': '/credits'})


@app.route('/api/maps', methods=['GET'])
def get_maps():
    return send_file('map_data/maps.json')

@app.route('/api/player', methods=['GET', 'POST'])
def player_data():
    if request.method == 'GET':
        return jsonify({
            "health": 100, 
            "gold": 500,
            "lives": 20,
            "current_wave": 1,
            "score": 0
        })
    elif request.method == 'POST':
        # Handle player data updates
        data = request.get_json()
        # In a real app, you'd save this to a database
        return jsonify({"status": "Updated", "data": data})

@app.route('/api/gamestate', methods=['GET', 'POST'])
def gamestate_api():
    global gamestate
    if request.method == 'GET':
        return jsonify(gamestate)
    elif request.method == 'POST':
        data = request.get_json()
        if 'selected_map' in data:
            gamestate['selected_map'] = data['selected_map']
        if 'player_name' in data:
            gamestate['player_name'] = data['player_name']
        return jsonify(gamestate)


@app.route('/api/towers', methods=['GET'])
def get_towers():
    import json
    # Load the tower data and format it properly
    with open('tower_data/tower_data.json', 'r') as f:
        tower_data = json.load(f)
    
    # The current format is already correct, just return it
    return jsonify(tower_data)




if __name__ == '__main__':
    app.run(debug=True)
