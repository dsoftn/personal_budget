import pystray
from PIL import Image
import subprocess


def on_quit(icon, item):
    icon.stop()

def on_activate(icon, item):
    # Dodajte ovde kod koji će se izvršiti kada korisnik klikne na ikonicu
    subprocess.run(["python", "budzet_main.pyw"], shell=True)

image = Image.open("data/assets/main_title.png")  # Zamijenite sa stvarnom putanjom do vaše ikonice
menu = (
    pystray.MenuItem("Otvori", on_activate, default=True),
    pystray.MenuItem("Izađi", on_quit)
)

icon = pystray.Icon("Licni Budzet", image, "Pokreni Licni Budzet", menu)
icon.run()
