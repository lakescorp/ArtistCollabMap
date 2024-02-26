"""
This script defines a Dash application that generates a graph of artist collaborations based on input from the user.
The application uses the SpotifyManager class from spoManager module and the Graph class from graph module.
The user can enter an artist name or link, and the application will generate a graph showing the collaborations between artists.
The graph is interactive, allowing the user to click on nodes to see more details about the artist and their songs.
"""

from spoManager import SpotifyManager
from graph import Graph
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

dash_app = dash.Dash(__name__)

ARTIST_URL_PREFIX = "https://open.spotify.com/artist/"
spoManagerInstance = SpotifyManager(debug=True)
graphInstance = Graph()
artist_data_store = {
    "songs": {},
    "artist_info": {},
    "registered_songs": {}
}

dash_app.layout = html.Div(className="base-div", children=[
    html.Div(className="input-button-container", children=[

        html.Div(children=[
            dcc.Input(
                type="text", 
                id="artist_link",
                className="artist-input",
                placeholder="Enter the artist name or link"
            ),
            html.Button("Generate graph", id="generate-button", className="generate-graph-button")
        ]),
        
    html.Div(id="artist-details", className="artist-details-div", children=[
    ]),


    ]),
    

    html.Div(className="graph-details-div", children=[
        html.Div(id='graph-container', className="graph-container-div", children=[
            dcc.Graph(id='artist-network', className="artist-network-graph"),
        ]),

        html.Div(id='click-data', className="click-data-div", children=[
            html.Button('Generate graph for artist', id='gen-selec-artist', n_clicks=0, className="gen-selec-artist-hidden"),
            html.Div(id='songs-list', children='Click on a node to see more details')
        ])
    ]),
    dcc.Store(id='selected-artist-id')

])








def process_artist_collabs(input_artist):
    """
    Process the artist collaborations.

    Args:
        input_artist (str): The input artist name.

    Returns:
        tuple: A tuple containing the following elements:
            - total_artists (int): The total number of artists.
            - registered_songs (dict): A dictionary of registered songs.
            - last_artist_collab (str): The last artist collaboration.
            - artist_data (dict): A dictionary of artist data.
            - artist_info (dict): A dictionary of artist information.
            - artist_songs (dict): A dictionary of artist songs.
    """
    total_artists, registered_songs, last_artist_collab, artist_data, artist_info = spoManagerInstance.getArtistCollabs(input_artist, False)
    artist_songs = {}

    for song, info_song in registered_songs.items():
        for artists in info_song["collaborations"]:
            for artist in artists:
                artist_songs.setdefault(artist, []).append(song)

    return total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs



@dash_app.callback(
    [
        Output('click-data', 'children'),
        Output('selected-artist-id', 'data')
    ],
    [Input('artist-network', 'clickData')]
)
def display_click_data(clickData):
    """
    Callback function that displays information based on the clicked data in the artist network.

    Parameters:
    - clickData (dict): The data of the clicked node in the artist network.

    Returns:
    - list: A list containing two elements:
        - html.Div: The HTML div containing the artist details and gallery items.
        - str: The ID of the clicked artist.
    """
    if not clickData:
        return [html.Div([
                html.Button('Generate graph for artist', id='gen-selec-artist', n_clicks=0, className="gen-selec-artist-hidden"),
                html.Div('Click on a node to see more details')
            ]), dash.no_update]

    node_clicked_id = clickData['points'][0]['customdata']
    songs_list = artist_data_store["songs"].get(node_clicked_id, [])

    artist_image_url = artist_data_store["artist_info"].get(node_clicked_id, {}).get('url', 'URL_DEFAULT')
    artist_image = html.Img(src=artist_image_url, className="artist-image-class")

    generate_button_for_artist = html.Button('Generate graph for artist', id='gen-selec-artist', n_clicks=0, className="gen-selec-artist-shown", **{'data-artist-id': node_clicked_id})
    


    artist_name_display = artist_data_store["artist_info"][node_clicked_id]['name']
    artist_spotify_url = ARTIST_URL_PREFIX + node_clicked_id

    total_collaborations = artist_data_store["songs"][node_clicked_id]
    last_collab_date = artist_data_store["last_artist_collab"].get(node_clicked_id, None)
    genres_list = artist_data_store["artist_info"][node_clicked_id]['genres']



    artist_name_link = html.A([artist_image, artist_name_display], href=artist_spotify_url, target="_blank", className="artist-link")

    artist_details_container = html.Div([
        html.Div([artist_name_link, generate_button_for_artist], className="artist-name-container"),
        html.Div([
            html.Div(f"📀 Total: {len(total_collaborations)}"),
            html.Div(f"📅 Last: {last_collab_date.strftime('%d-%m-%Y')}" if last_collab_date else ""),
            html.Div(f"🎷Genres: {', '.join(genres_list)}" if genres_list else "") 
        ], style={'display': 'flex','justifyContent': 'space-around'})   
    ], className='artist-details-container')


    gallery_items = []
    for song_id in songs_list:
        song_info = artist_data_store["registered_songs"][song_id]
        song_title = html.Div(song_info['name'], className="song-title-class")

        audio_preview = html.Audio(src=song_info['preview'], id=f"audio-{song_id}", controls=False) 

        song_thumbnail = html.Img(src=song_info['thumbnail'], 
                             className="song-thumbnail",
                             **{'data-song-id': song_id})


        song_item = html.Div([song_thumbnail, song_title, audio_preview], 
                     className="gallery-item-div")


        gallery_item = html.A(song_item, href=song_info['url'], target="_blank", className="gallery-item")
        gallery_items.append(gallery_item)

    return html.Div([artist_details_container] + gallery_items), node_clicked_id


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
    """
    Callback function that updates the graph and artist details based on user interactions.

    Parameters:
    - n_clicks_generate (int): Number of times the generate button is clicked.
    - n_clicks_selected (int): Number of times the select artist button is clicked.
    - input_artist (str): The artist name entered by the user.
    - artist_id (str): The ID of the selected artist.

    Returns:
    - fig (object): The updated graph figure.
    - artist_details (list): The updated artist details.
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    if ctx.triggered[0]['prop_id'] == "gen-selec-artist.n_clicks" and n_clicks_selected == 0:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'generate-button':
        if not input_artist:
            raise PreventUpdate

        total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs = process_artist_collabs(input_artist)
    elif button_id == 'gen-selec-artist':
        if not artist_id:
            raise PreventUpdate

        total_artists, registered_songs, last_artist_collab, artist_data, artist_info, artist_songs = process_artist_collabs(artist_id)

    artist_data_store["songs"] = artist_songs
    artist_data_store["artist_info"] = artist_info
    artist_data_store["registered_songs"] = registered_songs
    artist_data_store["last_artist_collab"] = last_artist_collab

    fig = graphInstance.generate_graph(total_artists, registered_songs, last_artist_collab, artist_info, 0)
    
    artist_name = artist_data_store["artist_info"].get(artist_data["id"], {}).get('name', None) if artist_data else None
    artist_image = artist_data_store["artist_info"].get(artist_data["id"], {}).get('url', None) if artist_data else None


    artist_details = []
    if artist_name and artist_image:
        artist_details.append(html.Div(artist_name, className="artist-name-detail"))
        artist_details.append(html.Img(src=artist_image, alt=artist_name, className="artist-image-detail"))



    return fig, artist_details


if __name__ == '__main__':
    dash_app.run_server(debug=True)
