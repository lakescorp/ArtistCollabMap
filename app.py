from flask import Flask, render_template, request
import plotly
import json
from spoManager import SpotifyManager
from graph import Graph
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

app = Flask(__name__)
dash_app = dash.Dash(__name__, 
                     server=app, 
                     routes_pathname_prefix='/generate/',
                     requests_pathname_prefix='/generate/')

spoManagerInstance = SpotifyManager(True)
graphInstance = Graph()
artistSongs = {}
global_artist_info = {} 
global_registered_songs = {}

# Layout for Dash application
dash_app.layout = html.Div(style={"display": "flex", "height": "100%"}, children=[
    # Contenedor para el gráfico
    html.Div(style={"width": "50%", "paddingBottom": "50%", "position": "relative", "flexShrink": 0}, children=[
        dcc.Graph(id='artist-network', style={
            "position": "absolute",
            "height": "100%",
            "width": "100%",
            "top": "0",
            "left": "0"
        }),
    ]),
    # Div de la derecha
    html.Div(id='click-data', children='Click on a node to see more details', style={
        "flex": "1",
        "height": "100%",
        "overflow-y": "auto", 
    })
])






# Endpoint for home page
@app.route('/')
def index():
    """
    Route decorator for the root URL.
    
    Returns:
        The rendered index.html template.
    """
    return render_template('index.html')

# Endpoint for generating graph based on the artist's collaborations
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """
    Generates a graph and renders it on the index.html page.

    Parameters:
        None

    Returns:
        str: The rendered index.html page with the graph data.
    """
    global artistSongs, global_artist_info, global_registered_songs
    graphJSON = None

    if request.method == 'POST':
        print("Generate")
        input_artist = request.form['artist_link']
        total_artists, global_registered_songs, last_artist_collab, artist_data, global_artist_info = spoManagerInstance.getArtistCollabs(input_artist, False)

        artistSongs = {}
        for song, info_song in global_registered_songs.items():
            for artists in info_song["collaborations"]:
                for artist in artists:
                    if artist not in artistSongs:
                        artistSongs[artist] = []
                    artistSongs[artist].append(song)

        fig = graphInstance.generate_graph(total_artists, global_registered_songs, last_artist_collab, artist_data, global_artist_info, 0)
        dash_app.layout['artist-network'].figure = fig
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', graphJSON=graphJSON)

# Callback for displaying songs of the clicked artist on the graph
@dash_app.callback(
    Output('click-data', 'children'),
    [Input('artist-network', 'clickData')]
)
def display_click_data(clickData):
    if clickData:
        node_clicked_id = clickData['points'][0]['customdata']
        print(node_clicked_id)
        songs_list = artistSongs.get(node_clicked_id, [])
        print(songs_list)


        artist_name_display = global_artist_info[node_clicked_id]['name']
        artist_name = html.Div(artist_name_display, style={'fontWeight': 'bold', 'fontSize': 'larger', 'marginBottom': '10px'})

        song_items = [html.Li(html.A(global_registered_songs[song_id]['name'], href=global_registered_songs[song_id]['url'], target="_blank")) for song_id in songs_list]

        return html.Div([artist_name, html.Ul(song_items)])
    else:
        return 'Click on a node to see more details'


# Running the Flask app
if __name__ == '__main__':
    app.run(debug=True)
