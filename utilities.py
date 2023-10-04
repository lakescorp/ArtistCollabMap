import json, random

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

    def random_color():
        """
        Generate a random color in hexadecimal format.

        Returns:
            str: A random color in hexadecimal format (e.g., '#00FF00').
        """
        r = lambda: random.randint(0,255)
        return '#%02X%02X%02X' % (r(), r(), r())
    
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
                