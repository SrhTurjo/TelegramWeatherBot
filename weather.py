import requests, os, datetime

class WeatherApp:
    def __init__(self):
        self.api = os.environ.get('open_weather_api')
        self.event_flag = None

        self.search = None

        self.names = None
        self.coordinates = None

        self.today = None
        self.tomorrow = None

    def search_for_locations(self):
        self.event_flag.clear()

        search = self.search
        g_link = f"http://api.openweathermap.org/geo/1.0/direct?q={search}&limit=5&appid={self.api}"
        results = requests.get(url=g_link)
        results = list(results.json())
        names = []
        coordinates = []

        if results == []:
            self.names, self.coordinates = None, None
            self.event_flag.set()
        else:
            for i,result in enumerate(results):
                details = ['name', 'state', 'country']
                name = f"\n{i+1}) "
                for detail in details:
                    if detail in result:
                        name += f"{result[detail]}; "
                names.append(name)
                coordinate = (int(results[i]['lat']), int(results[i]['lon']))
                coordinates.append(coordinate)

            self.names, self.coordinates = names, coordinates
            self.event_flag.set()


    def get_weather(self, coordinates , unit="metric"):

        self.event_flag.clear()

        lat, lon = coordinates

        w_link = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api}&units={unit}"
        r = requests.get(url=w_link)
        weather_data = list(dict(r.json())['list'])

        sorted_data = []

        for data in weather_data:
            dt = data['dt_txt']
            temp = data['main']['temp']
            weather = data['weather'][0]['description']
            sorted_data.append({"time": dt, "temp": temp, "weather": weather})

        today = []
        tomorrow = []
        for i,data in enumerate(sorted_data):
            time = data['time']
            time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
            ctime = datetime.datetime.now()

            if time.date() == ctime.date():
                today.append(data)
                #get hour with pm/am
                sorted_data[i]['time'] = time.strftime("%I:%M %p")

            elif time.date() == ctime.date() + datetime.timedelta(days=1):
                tomorrow.append(data)
                sorted_data[i]['time'] = time.strftime("%I:%M %p")


        self.today, self.tomorrow = today, tomorrow
        self.event_flag.set()

