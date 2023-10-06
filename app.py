from flask import Flask, render_template, request
import json
import plotly.utils
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
artist_data_store = {
    "songs": {},
    "artist_info": {},
    "registered_songs": {}
}

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


# Helper function for processing artist collabs
def process_artist_collabs(input_artist):
    total_artists, registered_songs, last_artist_collab, artist_data, artist_info = spoManagerInstance.getArtistCollabs(input_artist, False)
    artist_songs = {}

    for song, info_song in registered_songs.items():
        for artists in info_song["collaborations"]:
            for artist in artists:
                artist_songs.setdefault(artist, []).append(song)

    return total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs



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
    graphJSON, artist_name, artist_image = None, None, None

    if request.method == 'POST':
        input_artist = request.form['artist_link']
        total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs = process_artist_collabs(input_artist)

        artist_data_store["songs"] = artist_songs
        artist_data_store["artist_info"] = artist_info
        artist_data_store["registered_songs"] = registered_songs

        fig = graphInstance.generate_graph(total_artists, registered_songs, last_artist_collab, artist_data, artist_info, 0)
        dash_app.layout['artist-network'].figure = fig
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        artist_name = artist_data_store["artist_info"].get(artist_data["id"], {}).get('name', None) if artist_data else None
        artist_image = artist_data_store["artist_info"].get(artist_data["id"], {}).get('url', None) if artist_data else None

    return render_template('index.html', graphJSON=graphJSON, artist_name=artist_name, artist_image=artist_image)


# Callback para mostrar las canciones del artista clickeado en el gráfico
@dash_app.callback(
    Output('click-data', 'children'),
    [Input('artist-network', 'clickData')]
)
def display_click_data(clickData):
    if not clickData:
        return 'Click on a node to see more details'

    node_clicked_id = clickData['points'][0]['customdata']
    songs_list = artist_data_store["songs"].get(node_clicked_id, [])

    artist_image_url = artist_data_store["artist_info"][node_clicked_id]['url']
    artist_image = html.Img(src=artist_image_url, style={
        "width": "50px", 
        "height": "50px", 
        "borderRadius": "50%",
        "marginRight": "10px"
    })

    artist_name_display = artist_data_store["artist_info"][node_clicked_id]['name']
    artist_name = html.Div([artist_image, artist_name_display], style={
        'fontWeight': 'bold', 
        'fontSize': 'larger', 
        'marginBottom': '10px',
        'display': 'flex',
        'alignItems': 'center'
    })

    gallery_items = []
    for song_id in songs_list:
        song_info = artist_data_store["registered_songs"][song_id]
        song_title = html.Div(song_info['name'], style={"textAlign": "center"})

        # Elemento de audio para la vista previa
        audio_preview = html.Audio(src=song_info['preview'], id=f"audio-{song_id}", controls=False)  # Sin controles

        # Agrega los atributos de mouseover y mouseout al thumbnail de la canción
        song_thumbnail = html.Img(src=song_info['thumbnail'], 
                             className="song-thumbnail", 
                             style={"width": "100px", "display": "block", "margin": "auto"},
                             **{'data-song-id': song_id})


        # Agrupamos todo en un div
        song_item = html.Div([song_thumbnail, song_title, audio_preview], style={"display": "inline-block", "margin": "10px"})

        gallery_item = html.A(song_item, href=song_info['url'], target="_blank")
        gallery_items.append(gallery_item)

    return html.Div([artist_name] + gallery_items)






# Running the Flask app
if __name__ == '__main__':
    app.run(debug=True)
