import json, random, os
import colorsys

class Utilities:
    def saveResponse(response, filename):
        app_json = json.dumps(response)
        f = open(filename, "w")

        f.write(app_json)
        f.close()

    def normalSave(response, filename):
        f = open(filename, "w")
        f.write(response)
        f.close()

    def loadJson(filename):
        with open(filename) as json_file:
            data = json.load(json_file)
            return data

    def random_color(saturation=1.0, value=1.0):
        """
        Generate a random color with constant saturation in hexadecimal format.

        Parameters:
            saturation (float): Saturation of the color. Default is 1.0 (full saturation).
            value (float): Value (brightness) of the color. Default is 1.0 (full brightness).

        Returns:
            str: A random color in hexadecimal format.
        """
        hue = random.random()  # Random hue between 0 and 1
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return '#%02X%02X%02X' % (int(r*255), int(g*255), int(b*255))
    
    def normalize(arr, t_min, t_max):
        """
        Normalize an array of values to a specified range.

        Parameters:
            arr (list): The input array of values.
            t_min (float): The minimum value of the target range.
            t_max (float): The maximum value of the target range.

        Returns:
            list: The normalized array of values.
        """
        norm_arr = []
        diff = t_max - t_min
        diff_arr = max(arr) - min(arr)
        for i in arr:
            temp = (((i - min(arr))*diff)/diff_arr) + t_min
            norm_arr.append(temp)
        return norm_arr
    
    @staticmethod
    def get_genre_color(genre, filename="data/genre_colors.json"):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                genre_colors = json.load(f)
        else:
            genre_colors = {}

        if genre not in genre_colors:
            genre_colors[genre] = Utilities.random_color()

            with open(filename, "w") as f:
                json.dump(genre_colors, f)

        return genre_colors[genre]

                