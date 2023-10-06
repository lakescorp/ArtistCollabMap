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
            html.Button("Generate graph", id="generate-button", style={
                "backgroundColor": "#1DB954",  # Verde Spotify
                "border": "none",
                "borderRadius": "25px",  # Bordes completamente redondeados
                "color": "white"  # Texto blanco
            })
        ]),
        
    html.Div(id="artist-details", style={"display": "flex", "alignItems": "center"}, children=[
    ]),


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
            "overflowY": "auto",
            "maxHeight": "500px",
            "width": "50%",
            "paddingLeft": "20px"
        }, children=[
            html.Button('Generate graph for artist', id='gen-selec-artist', n_clicks=0, style={'display': 'none'}),
            html.Div(id='songs-list', children='Click on a node to see more details')
        ])
    ]),
    dcc.Store(id='selected-artist-id')

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



# Callback para mostrar las canciones del artista clickeado en el gráfico
@dash_app.callback(
    [
        Output('click-data', 'children'),
        Output('selected-artist-id', 'data')
    ],
    [Input('artist-network', 'clickData')]
)
def display_click_data(clickData):
    if not clickData:
        return [html.Div([
                html.Button('Generate graph for artist', id='gen-selec-artist', n_clicks=0, style={'display': 'none'}),
                html.Div('Click on a node to see more details')
            ]), dash.no_update]

    node_clicked_id = clickData['points'][0]['customdata']
    songs_list = artist_data_store["songs"].get(node_clicked_id, [])

    artist_image_url = artist_data_store["artist_info"].get(node_clicked_id, {}).get('url', 'URL_DEFAULT')
    artist_image = html.Img(src=artist_image_url, style={
        "width": "50px", 
        "height": "50px", 
        "borderRadius": "50%",
        "marginRight": "10px"
    })

    generate_button_for_artist = html.Button('Generate graph for artist', id='gen-selec-artist', n_clicks=0, **{'data-artist-id': node_clicked_id})
    generate_button_for_artist.style = {
            "backgroundColor": "#1DB954",  # Verde Spotify
            "border": "none",
            "borderRadius": "25px",  # Bordes completamente redondeados
            "color": "white",  # Texto blanco
            "marginLeft": "auto"
        }
    


    artist_name_display = artist_data_store["artist_info"][node_clicked_id]['name']
    artist_name = html.Div([artist_image, artist_name_display, generate_button_for_artist], style={
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

    return html.Div([artist_name] + gallery_items), node_clicked_id


@dash_app.callback(
    [
        Output('artist-network', 'figure'),
        Output('artist-details', 'children')
    ],
    [
        Input('generate-button', 'n_clicks'),
        Input('gen-selec-artist', 'n_clicks')
    ],
    [
        State('artist_link', 'value'),
        State('selected-artist-id', 'data')
    ]
)
def unified_update_graph(n_clicks_generate, n_clicks_selected, input_artist, artist_id):
    # Determinar qué botón se presionó
    ctx = dash.callback_context

    # Si no se presionó ninguno de los botones
    if not ctx.triggered:
        raise PreventUpdate

    if ctx.triggered[0]['prop_id'] == "gen-selec-artist.n_clicks" and n_clicks_selected == 0:
        raise PreventUpdate


    print(f"Callback 'unified_update_graph' fue disparada por {ctx.triggered[0]['prop_id']}")
    print(n_clicks_generate,n_clicks_selected)
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'generate-button':
        if not input_artist:
            raise PreventUpdate
        # Aquí, usa el input_artist como antes
        total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs = process_artist_collabs(input_artist)
    elif button_id == 'gen-selec-artist':
        if not artist_id:
            raise PreventUpdate
        # Usa artist_id directamente
        total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs = process_artist_collabs(artist_id)

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



    return fig, artist_details


if __name__ == '__main__':
    dash_app.run_server(debug=True)
