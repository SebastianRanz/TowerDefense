from flask import Flask, render_template, request, jsonify

from modules.utils import retrieve_map_data
from modules.utils import retrieve_tower_data

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
    maps = retrieve_map_data()
    return jsonify(maps)


@app.route('/api/tower-types', methods=['GET'])
def get_maps():
    tower_data = retrieve_tower_data()
    return jsonify(tower_data)




if __name__ == '__main__':
    app.run(debug=True)