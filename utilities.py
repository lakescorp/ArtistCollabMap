import json

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
                