from flask import Flask, render_template, request
import plotly
import plotly.graph_objs as go
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

# Layout for Dash application
dash_app.layout = html.Div([
    html.Div([
        dcc.Graph(id='artist-network'),
        html.Div(id='click-data', children='Click on a node to see more details')
    ], id='plotly-div')])

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
    global artistSongs
    graphJSON = None

    if request.method == 'POST':
        artist_link = request.form['artist_link']
        total_artists, registered_songs, last_artist_collab, artist_data, artist_profile_urls = spoManagerInstance.getArtistCollabs(artist_link, False)
        
        artistSongs = {}
        for song, artists_list in registered_songs.items():
            for artists in artists_list:
                for artist in artists:
                    if artist not in artistSongs:
                        artistSongs[artist] = []
                    artistSongs[artist].append(song)

        fig = graphInstance.generate_graph(total_artists, registered_songs, last_artist_collab, artist_data, artist_profile_urls, 0)
        dash_app.layout['artist-network'].figure = fig
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', graphJSON=graphJSON)

# Callback for displaying songs of the clicked artist on the graph
@dash_app.callback(
    Output('click-data', 'children'),
    [Input('artist-network', 'clickData')]
)
def display_click_data(clickData):
    """
    Generate a function comment for the given function body.

    Parameters:
        clickData (dict): The click data from the artist network.

    Returns:
        str or html.Ul: The children to display in the click-data component.
    """
    print(clickData)
    if clickData:
        node_clicked = clickData['points'][0]['customdata']
        songs_list = artistSongs.get(node_clicked, [])
        print(node_clicked)
        return html.Ul([html.Li(song) for song in songs_list])
    else:
        return 'Click on a node to see more details'

# Running the Flask app
if __name__ == '__main__':
    app.run(debug=True)
