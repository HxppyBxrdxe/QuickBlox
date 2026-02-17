import customtkinter as ctk
import tkinter as tk
from urllib.parse import urlparse
import webbrowser
import json
import os
import requests

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("media/coffee.json")

app = ctk.CTk()
app.title("Roblox Launcher")
app.geometry("460x420")
app.resizable(True, True)

top_frame = ctk.CTkFrame(app)
left_frame = ctk.CTkFrame(app)
right_frame = ctk.CTkFrame(app)

top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
left_frame.grid(row=1, column=0, padx=(10,5), pady=10, sticky="ns")
right_frame.grid(row=1, column=1, padx=(5,10), pady=10, sticky="ns")

app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(1, weight=1)

DATA_FILE = "games.json"
MAX_RECENTS = 1

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "games": {},
            "recents": [],
            "favourites": [],
            "settings": {"theme": "light"}
        }

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.setdefault("games", {})
    data.setdefault("recents", [])
    data.setdefault("favourites", [])
    data.setdefault("settings", {})
    data["settings"].setdefault("theme", "light")

    return data


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

data = load_data()
ctk.set_appearance_mode(data["settings"]["theme"])

# Check if the game actually exists
def check_game_exists(place_id: str) -> bool:
    #so they don't think it's a bot
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        universe_res = requests.get(
            f"https://apis.roblox.com/universes/v1/places/{place_id}/universe",
            headers=headers,
            timeout=5
        )

        universe_res.raise_for_status()
        universe_data = universe_res.json()

        universe_id = universe_data.get("universeId")
        if not universe_id:
            return False

        game_res = requests.get(
            "https://games.roblox.com/v1/games",
            params={"universeIds": universe_id},
            headers=headers,
            timeout=5
        )

        game_res.raise_for_status()
        game_data = game_res.json().get("data", [])

        return bool(game_data)

    except requests.RequestException:
        return False

# Light/Dark mode triggers
def toggle_theme():
    if theme_switch.get() == 1:
        mode = "Dark"
    else:
        mode = "Light"

    ctk.set_appearance_mode(mode)
    data["settings"]["theme"] = mode
    save_data()

# Get the ID from, the .json, and launch it with webbrowser
def launch_game(game_name):
    place_id = data["games"][game_name]

    webbrowser.open(f"roblox://placeId={place_id}")

    # Update recents
    if game_name in data["recents"]:
        data["recents"].remove(game_name)
    data["recents"].insert(0, game_name)
    data["recents"] = data["recents"][:MAX_RECENTS]

    save_data()
    show_launching_message(game_name)

def show_launching_message(game_name):
    status_label.configure(text=f"Launching {game_name}...")
    status_label.after(3000, hide_status_message)

def hide_status_message():
    status_label.configure(text="")

# Adding the game and checks
def add_game():
    url = url_entry.get().strip()
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")

    # Format check
    if len(parts) < 3 or parts[0] != "games":
        status_label.configure(text="This is not a valid link. ( ˘︹˘ )")
        return

    place_id = parts[1]
    game_name = parts[2].replace("-", " ").title()

    status_label.configure(text="Checking game...")
    app.update_idletasks()

    # Calling function
    if not check_game_exists(place_id):
        status_label.configure(text="This game doesn't exist twin 🥀")
        return

    # Only runs if valid
    data["games"][game_name] = place_id
    save_data()

    refresh_dropdown()
    status_label.configure(text=f"Added {game_name} ╰(*°▽°*)╯")

def delete_selected():
    name = games_dropdown.get()

    if name not in data["games"]:
        status_label.configure(text="This isn't a game in your list twin 🥀")
        return

    del data["games"][name]

    if name in data["recents"]:
        data["recents"].remove(name)

    save_data()
    refresh_dropdown()

    status_label.configure(text=f"Got rid of that yee yee ahh {name}.")

def launch_selected():
    name = games_dropdown.get()
    if name in data["games"]:
        launch_game(name)
    else:
        status_label.configure(text="Select a game first")


def launch_recent():
    if data["recents"]:
        launch_game(data["recents"][0])
    else:
        status_label.configure(text="You haven't played anything recently... Hop onnnn ಠ_ಠ")

def refresh_dropdown():
    games_dropdown.configure(values=list(data["games"].keys()))
    refresh_favourites()

# Add to favorites, will need to work on making it easier to understand
def toggle_favourite(name):
    if not name:
        return

    if name in data["favourites"]:
        data["favourites"].remove(name)
        status_label.configure(text=f"Removed {name} from favourites.")
    else:
        data["favourites"].append(name)
        status_label.configure(text=f"Added {name} to favourites")

    save_data()
    refresh_favourites()

def refresh_favourites():
    for widget in favourites_frame.winfo_children():
        widget.destroy()

    for name in data["favourites"]:
        btn = ctk.CTkButton(
            favourites_frame,
            text=name,
            width=160,
            command=lambda n=name: launch_game(n)
        )
        btn.pack(pady=2)

        btn.bind(
            "<Button-3>",
            lambda e, n=name: show_favourite_menu(e, n)
        )


def show_favourite_menu(event, name):
    global current_right_clicked
    current_right_clicked = name

    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()


#--------------------------- APP ----------------------------------------
# Right click funtionality
current_right_clicked = None

context_menu = tk.Menu(app, tearoff=0)
context_menu.add_command(
    label="Add / Remove Favourite",
    command=lambda: toggle_favourite(games_dropdown.get())
)
theme_switch = ctk.CTkSwitch(
    top_frame,
    text="Dark Mode",
    command=toggle_theme
)

theme_switch.pack(anchor="w", padx=1, pady=(1, 2))

url_entry = ctk.CTkEntry(
    top_frame,
    width=380,
    placeholder_text="https://www.roblox.com/games/...", justify="center"
)
url_entry.pack()

status_label = ctk.CTkLabel(top_frame, text="")
status_label.pack(pady=5)

theme_switch.pack(anchor="w", padx=10, pady=(8, 0))

games_dropdown = ctk.CTkComboBox(
    top_frame,
    width=380,
    values=list(data["games"].keys())
)
games_dropdown.pack(pady=10)

games_dropdown.bind(
    "<Button-3>",
    lambda e: context_menu.tk_popup(e.x_root, e.y_root)
)

ctk.CTkLabel(
    left_frame,
    text="Favourites",
    font=("Segoe UI", 16)
).pack(pady=(0,0))

ctk.CTkLabel(
    left_frame,
    text="Right-click a favourite to remove/add",
    font=("Segoe UI", 12)
).pack(pady=(0,5))

favourites_frame = ctk.CTkScrollableFrame(left_frame, width=180, height=150)
favourites_frame.pack(pady=5, fill="both", expand=True)

ctk.CTkButton(
    right_frame,
    text="Add Game",
    command=add_game
).pack(pady=5, fill="x")

ctk.CTkButton(
    right_frame,
    text="Launch Selected",
    command=launch_selected
).pack(pady=5, fill="x")

ctk.CTkButton(
    right_frame,
    text="Launch Recent",
    command=launch_recent
).pack(pady=5, fill="x")

ctk.CTkButton(
    right_frame,
    text="Delete Selected",
    command=delete_selected
).pack(pady=5, fill="x")

app.bind("<Return>", lambda e: launch_recent())

refresh_dropdown()
app.mainloop()
