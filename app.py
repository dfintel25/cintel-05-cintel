# --------------------------------------------
# Imports at the top - PyShiny EXPRESS VERSION
# --------------------------------------------

# From shiny, import just reactive and render
from shiny import reactive, render

# From shiny.express, import just ui and inputs if needed
from shiny.express import ui

import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
from scipy import stats
from shiny import render, ui as base_ui  # Note: for render.ui and ui.TagList


# --------------------------------------------
# Import icons as you like
# --------------------------------------------

# https://fontawesome.com/v4/cheatsheet/
from faicons import icon_svg

# --------------------------------------------
# Shiny EXPRESS VERSION
# --------------------------------------------

# --------------------------------------------
# First, set a constant UPDATE INTERVAL for all live data
# Constants are usually defined in uppercase letters
# Use a type hint to make it clear that it's an integer (: int)
# --------------------------------------------

UPDATE_INTERVAL_SECS: int = 5

# --------------------------------------------
# Initialize a REACTIVE VALUE with a common data structure
# The reactive value is used to store state (information)
# Used by all the display components that show this live data.
# This reactive value is a wrapper around a DEQUE of readings
# --------------------------------------------

DEQUE_SIZE: int = 5
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# --------------------------------------------
# Initialize a REACTIVE CALC that all display components can call
# to get the latest data and display it.
# The calculation is invalidated every UPDATE_INTERVAL_SECS
# to trigger updates.
# It returns a tuple with everything needed to display the data.
# Very easy to expand or modify.
# --------------------------------------------


@reactive.calc()
def reactive_calc_combined():
    # Invalidate this calculation every UPDATE_INTERVAL_SECS to trigger updates
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)

    # Data generation logic
    temp = round(random.uniform(-18, -16), 1)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_dictionary_entry = {"temp":temp, "timestamp":timestamp}

    # get the deque and append the new entry
    reactive_value_wrapper.get().append(new_dictionary_entry)

    # Get a snapshot of the current deque for any further processing
    deque_snapshot = reactive_value_wrapper.get()

    # For Display: Convert deque to DataFrame for display
    df = pd.DataFrame(deque_snapshot)

    # For Display: Get the latest dictionary entry
    latest_dictionary_entry = new_dictionary_entry

    # Return a tuple with everything we need
    # Every time we call this function, we'll get all these values
    return deque_snapshot, df, latest_dictionary_entry

# --------------------------------------------
# Initialize a REACTIVE CALC that calculates a prediction based off
# of reactive_calc_combined.
# Display results with a gradient theme.
#---------------------------------------------

@reactive.calc()
def predicted_temp():
    _, df, _ = reactive_calc_combined()

    if len(df) < 2:
        return None

    x_vals = list(range(len(df)))
    y_vals = df["temp"]
    slope, intercept, *_ = stats.linregress(x_vals, y_vals)

    next_x = len(df)
    return round(slope * next_x + intercept, 1)

def get_temp_gradient(temp: float) -> str:
    if temp is None:
        return "bg-gradient-gray-white"
    elif temp >= -16.2:
        return "bg-gradient-orange-red"
    elif temp >= -17.0:
        return "bg-gradient-yellow-orange"
    else:
        return "bg-gradient-blue-purple"


# Define the Shiny UI Page layout
# Call the ui.page_opts() function
# Set title to a string in quotes that will appear at the top
# Set fillable to True to use the whole page width for the UI
ui.page_opts(title="PyShiny Express: Live Data Example", fillable=True)

# Sidebar is typically used for user interaction/information
# Note the with statement to create the sidebar followed by a colon
# Everything in the sidebar is indented consistently
# Add a ui.h6 for "Last Updated"
with ui.sidebar(open="open"):

    ui.h2("Antarctic Explorer", class_="text-center")
    ui.p(
        "A demonstration of real-time temperature readings in Antarctica.",
        class_="text-center",
    )
    ui.hr()
    
    ui.h6("Links:")
    ui.a(
        "dfintel25 GitHub",
        href="https://github.com/dfintel25",
        target="_blank",
    )
    ui.a(
        "GitHub Source",
        href="https://github.com/denisecase/cintel-05-cintel",
        target="_blank",
    )
    ui.a(
        "GitHub App",
        href="https://denisecase.github.io/cintel-05-cintel/",
        target="_blank",
    )
    ui.a("PyShiny", href="https://shiny.posit.co/py/", target="_blank")
    ui.a(
        "PyShiny Express",
        href="hhttps://shiny.posit.co/blog/posts/shiny-express/",
        target="_blank",
    )

    ui.hr()
    ui.h6(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")


# In Shiny Express, everything not in the sidebar is in the main panel
with ui.layout_columns():
    # LEFT COLUMN: Stack value boxes
    with ui.layout_columns():
        with ui.value_box(
            showcase=icon_svg("sun"),
            theme="bg-gradient-blue-purple",
        ):
            "Current Temperature"

            @render.text
            def display_temp():
                _, _, latest = reactive_calc_combined()
                return f"{latest['temp']} °C"

            @render.text
            def display_temp_note():
                _, _, latest = reactive_calc_combined()
                return "Warmer than usual" if latest["temp"] > -17.0 else "Within expected range"

        # Predicted value box (call the reactive UI here)
        @render.ui
        def dynamic_predicted_value_box():
            temp = predicted_temp()
            theme = get_temp_gradient(temp)

            # Add a note about the prediction
            if temp is None:
                note = "Not enough data to predict"
                value_text = note
            else:
                if temp > -17.0:
                    note = "↑ Warming trend"
                elif temp < -17.5:
                    note = "↓ Cooling trend"
                else:
                    note = "Stable trend"

                # Combine value and note
                value_text = f"{temp} °C<br><small>{note}</small>"

            return ui.value_box(
            title="Next Predicted Temperature",
            value=base_ui.HTML(value_text),  # Use HTML to handle line break/small font
            showcase=icon_svg("chart-line"),
            theme=theme,
)

    # RIGHT COLUMN: Most Recent Readings
    with ui.layout_columns():
        with ui.card(full_screen=True):
            ui.card_header("Most Recent Readings")

            @render.data_frame
            def display_df():
                _, df, _ = reactive_calc_combined()
                pd.set_option('display.width', None)
                return render.DataGrid(df, width="100%")

#------------------------------------------------------------
# Initialize two charts
# 1) Scatter plot with regression
# 2) BAr chart with trend line
#------------------------------------------------------------

with ui.layout_columns():
    with ui.card():
        ui.card_header("Scatter Plot with Regression")
        
        @render_plotly
        def display_plot():
            _, df, _ = reactive_calc_combined()

            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                fig = px.scatter(
                    df,
                    x="timestamp",
                    y="temp",
                    title="Temperature Readings with Regression Line",
                    labels={"temp": "Temperature (°C)", "timestamp": "Time"},
                    color_discrete_sequence=["blue"]
                )

                x_vals = list(range(len(df)))
                y_vals = df["temp"]
                slope, intercept, *_ = stats.linregress(x_vals, y_vals)
                df["best_fit_line"] = [slope * x + intercept for x in x_vals]

                fig.add_scatter(
                    x=df["timestamp"],
                    y=df["best_fit_line"],
                    mode='lines',
                    name='Regression Line'
                )

                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Temperature (°C)",
                    xaxis_tickangle=-45
                )
                fig.update_traces(marker=dict(size=10), hovertemplate="Time: %{x}<br>Temp: %{y} °C")

                return fig

    with ui.card():
        ui.card_header("Temperature Bar Chart with Trend Line")

        @render_plotly
        def display_bar_chart():
            _, df, _ = reactive_calc_combined()

            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                fig = px.bar(
                    df,
                    x="timestamp",
                    y="temp",
                    title="Temperature Bar Chart",
                    labels={"temp": "Temperature (°C)", "timestamp": "Time"},
                    color_discrete_sequence=["skyblue"]
                )

                x_vals = list(range(len(df)))
                y_vals = df["temp"]
                slope, intercept, *_ = stats.linregress(x_vals, y_vals)
                df["trend_line"] = [slope * x + intercept for x in x_vals]

                fig.add_scatter(
                    x=df["timestamp"],
                    y=df["trend_line"],
                    mode="lines",
                    name="Trend Line",
                    line=dict(color="red", width=2, dash="dash")
                )

                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Temperature (°C)",
                    xaxis_tickangle=-45,
                    margin=dict(t=40, b=40, l=40, r=20)
                )

                return fig
