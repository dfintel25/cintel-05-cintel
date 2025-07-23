from shiny import reactive, render
from shiny.express import ui, input  
import random
from datetime import datetime
from faicons import icon_svg

# --- Constants ---
DEFAULT_UPDATE_INTERVAL = 1
TEMP_RANGE = (-18, -16)
last_temp = {"value": None}  

# --- Reactive Data Calculation ---
@reactive.calc()
def live_data():
    reactive.invalidate_later(input.update_interval())  
    temp_c = round(random.uniform(*TEMP_RANGE), 1)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"temp": temp_c, "timestamp": timestamp}

# --- Render: Icon ---
@render.ui
def display_icon():
    temp = live_data()["temp"]
    icon = icon_svg("sun") if temp > -16.5 else icon_svg("snowflake")
    css_class = "text-yellow-500" if temp > -16.5 else "text-blue-500"
    return ui.span(icon, class_=css_class)      

# --- Render: Temperature ---
@render.text
def display_temp():
    temp_c = live_data()["temp"]
    use_f = input.use_fahrenheit()  

    temp_display = temp_c
    unit = "°C"
    if use_f:
        temp_display = round((temp_c * 9 / 5) + 32, 1)
        unit = "°F"

    trend_icon = "→"
    if last_temp["value"] is not None:
        if temp_c > last_temp["value"]:
            trend_icon = "↑"
        elif temp_c < last_temp["value"]:
            trend_icon = "↓"
    last_temp["value"] = temp_c

    return f"{temp_display} {unit} {trend_icon}"

# --- UI Layout + Output Declarations ---
ui.page_opts(title="PyShiny Express: Live Data (Basic)", fillable=True)

with ui.sidebar(open="open"):
    ui.h2("Antarctic Explorer", class_="text-center")
    ui.p("A demonstration of real-time temperature readings in Antarctica.", class_="text-center")
    ui.input_slider("update_interval", "Update every N seconds", min=1, max=30, value=DEFAULT_UPDATE_INTERVAL)
    ui.input_switch("use_fahrenheit", "Show in Fahrenheit", value=False)

# --- Declare outputs ---
ui.h2("Current Temperature", class_="text-xl mt-4")
ui.p("Warmer than usual", class_="italic text-gray-500")
ui.hr()
ui.h2("Current Date and Time", class_="text-xl mt-4")

# --- Render: Timestamp ---
@render.text
def display_time():
    return live_data()["timestamp"]


