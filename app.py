from spoManager import SpotifyManager
from graph import Graph
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

dash_app = dash.Dash(__name__)


spoManagerInstance = SpotifyManager(True)
graphInstance = Graph()
artist_data_store = {
    "songs": {},
    "artist_info": {},
    "registered_songs": {}
}

dash_app.layout = html.Div(style={"display": "flex", "height": "100%", "flexDirection": "column"}, children=[
    # Formulario en la parte superior
    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px"}, children=[
        # Formulario
        html.Div(children=[
            html.Label("Artist:", htmlFor="artist_link"),
            dcc.Input(type="text", id="artist_link"),
            html.Button("Generate graph", id="generate-button")
        ]),
        
        # Detalles del artista (nombre e imagen)
        html.Div(id="artist-details", style={"display": "flex", "alignItems": "center"})
    ]),
    
    # Contenedor principal para gráfico y galería
    html.Div(style={"display": "flex", "height": "100%", "flexDirection": "row", "overflow": "hidden"}, children=[
        # Contenedor para el gráfico
        html.Div(id='graph-container', style={"width": "50%", "paddingBottom": "50%", "position": "relative", "flexShrink": 0}, children=[
            dcc.Graph(id='artist-network', style={
                "position": "absolute",
                "height": "100%",
                "width": "100%",
                "top": "0",
                "left": "0"
            }),
        ]),

        # Galería de canciones a la derecha
        html.Div(id='click-data', style={
            "flex": "1",
            "overflowY": "auto",  # Hace que sea desplazable si el contenido supera la altura
            "maxHeight": "500px",  # Puedes ajustar esto según lo que necesites
            "width": "50%",
            "paddingLeft": "20px"
        }, children='Click on a node to see more details')
    ])
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



@dash_app.callback(
    [
        Output('artist-network', 'figure'),
        Output('artist-details', 'children')
    ],
    [
        Input('generate-button', 'n_clicks')
    ],
    [
        State('artist_link', 'value')
    ]
)
def update_graph(n_clicks, input_artist):
    if not n_clicks or not input_artist:
        raise PreventUpdate

    total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs = process_artist_collabs(input_artist)

    artist_data_store["songs"] = artist_songs
    artist_data_store["artist_info"] = artist_info
    artist_data_store["registered_songs"] = registered_songs

    fig = graphInstance.generate_graph(total_artists, registered_songs, last_artist_collab, artist_data, artist_info, 0)
    
    artist_name = artist_data_store["artist_info"].get(artist_data["id"], {}).get('name', None) if artist_data else None
    artist_image = artist_data_store["artist_info"].get(artist_data["id"], {}).get('url', None) if artist_data else None

    # Crear detalles del artista para mostrar en el layout
    artist_details = []
    if artist_name and artist_image:
        artist_details.append(html.Div(artist_name, style={"marginRight": "10px"}))
        artist_details.append(html.Img(src=artist_image, alt=artist_name, style={"width": "50px", "height": "50px", "borderRadius": "50%"}))

    # En este caso, dado que el gráfico ya está en el layout, no necesitamos crear un iframe. Simplemente devolvemos una lista vacía.
    graph_container_content = []

    return fig, artist_details



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

        audio_preview = html.Audio(src=song_info['preview'], id=f"audio-{song_id}", controls=False)  # Sin controles

        song_thumbnail = html.Img(src=song_info['thumbnail'], 
                             className="song-thumbnail", 
                             style={"width": "100px", "display": "block", "margin": "auto"},
                             **{'data-song-id': song_id})


        song_item = html.Div([song_thumbnail, song_title, audio_preview], style={"display": "inline-block", "margin": "10px"})

        gallery_item = html.A(song_item, href=song_info['url'], target="_blank")
        gallery_items.append(gallery_item)

    return html.Div([artist_name] + gallery_items)






if __name__ == '__main__':
    dash_app.run_server(debug=True)
