import plotly.graph_objects as go
import networkx as nx
from datetime import datetime as dt
import os
import random
from utilities import Utilities as utils

class Graph:
    def __init__(self, debug=False):
        os.environ["PATH"] += os.pathsep + os.getenv('graphizRoute')
        self.node_base_size = 300
        self.color_list = ["#FF5454",'#FF9E54','#FFD454','#DAFF54','#A7FF54','#54FF7F','#54FFE3','#54DAFF','#AF54FF','#E054FF','#FF54EE','#FF5496','#FF545A']
        self.debug = debug



    def random_color_from_list(self):
        """
        Generates a random color from the color list.

        Returns:
            str: A randomly selected color from `color_list`.
        """
        return self.color_list[random.randrange(0,len(self.color_list))]

    def generate_graph(self, total_artists, registered_songs, last_collab_artist, artist_data, artist_profile_urls, level=0):
        """
        Generates a graph based on the given data.

        Parameters:
            total_artists (dict): A dictionary containing the total number of songs of each artist.
            registered_songs (dict): A dictionary containing the registered songs.
            last_collab_artist (dict): A dictionary containing the last collaboration date of each artist.
            artist_data (dict): A dictionary containing the data of the main artist.
            artist_profile_urls (list): A list containing the profile URLs of the artists.
            level (int): The level of the graph generation.

        Returns:
            fig (go.Figure): The generated graph figure.
        """
        max_value = max(total_artists, key=total_artists.get)
        artists_copy = total_artists.copy()  # Copy the original dictionary
        del artists_copy[max_value]  # Remove the main artist
        second_max_value = max(artists_copy, key=artists_copy.get) 
        
        for key, elem in last_collab_artist.items():
            last_collab_artist[key] = dt.strptime(elem,'%Y-%m-%d')

        minval = min(last_collab_artist)

        deltas_datetime = {}
        for key, val in last_collab_artist.items():
            delta = last_collab_artist[minval] - val
            deltas_datetime[key] = delta.days + 1

        deltas_to_regularize = deltas_datetime.values()
        deltas_regularized = utils.normalize(deltas_to_regularize, 1, 10)

        index = 0
        for key, val in deltas_datetime.items():
            deltas_datetime[key] = deltas_regularized[index]
            index += 1
        
        node_sizes = []
        colors = []

        G = nx.Graph(scale=1)
        G.add_node(max_value)
        node_sizes.append(total_artists[second_max_value])
        colors.append(self.random_color_from_list())

        for artist, songs in total_artists.items():
            if artist == max_value:
                continue
            G.add_node(artist)
            if self.debug:
                print(artist, songs, deltas_datetime[artist])
            G.add_edge(max_value, artist, color='black', weight=deltas_datetime[artist])
            node_sizes.append(songs)
            colors.append(self.random_color_from_list())

        if level >= 1:
            for song, artists in registered_songs.items():
                for artist_list in artists:
                    reduced_list = artist_list
                    reduced_list.remove(max_value)
                    for i in range(0, len(reduced_list)):
                        for x in range(i+1, len(reduced_list)):
                            if not G.has_edge(reduced_list[i], reduced_list[x]):
                                G.add_edge(reduced_list[i], reduced_list[x], color='g')

        node_sizes = utils.normalize(node_sizes, 0.1, 1)
        node_sizes = [item * self.node_base_size for item in node_sizes]

        pos = nx.kamada_kawai_layout(G)
        
        node_labels = {node: node for node in G.nodes()}

        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=1, color='black'),
            hoverinfo='none',
            mode='lines')

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)

        node_trace = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode='markers',
            customdata=[],
            hoverinfo='text',
            marker=dict(
                showscale=False,   
                colorscale='YlGnBu',
                size=node_sizes,
                line_width=2))

        node_trace.marker.color = colors

        label_trace = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode='text',
            hoverinfo='none',
            textfont=dict(
                family="sans serif",
                size=12,
                color="black"
            )
        )

        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += (x,)
            node_trace['y'] += (y,)

            if node == max_value:
                node_label = "Collabs: {}".format(total_artists[node])
            else:
                last_collab_date = last_collab_artist[node].strftime('%d-%m-%Y')
                node_label = "Collabs: {}\nLast: {}".format(total_artists[node], last_collab_date)

            node_trace['text'] += (node_label,)
            node_trace['customdata'] += (node,)

            label_trace['x'] += (x,)
            label_trace['y'] += (y,)
            label_trace['text'] += (node_labels[node],)

        layout = go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            annotations=[],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))

        fig = go.Figure(data=[edge_trace, node_trace, label_trace], layout=layout)
        return fig
