DOMAIN = "tablet_assist_for_alexa"
MAX_WAV = 16 * 1024 * 1024
ROOMS = ("Büro", "Wohnzimmer", "Badezimmer", "Schlafzimmer", "Kinderzimmer")
PROFILES = ("Natürlich", "Studio", "Klar")
def settings(entry):
    return {**entry.data, **entry.options}
