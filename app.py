"""A simple gradio app to predict NBA player performance this season"""

import gradio as gr
import pandas as pd
from prophet import Prophet
from datasets import load_dataset

pd.options.plotting.backend = "plotly"


# initialize empty players
players = [""]

# initialize empty seasons
seasons = [1977, 2021]

# load data
nba_dataset = load_dataset("andrewkroening/538-NBA-Historical-Raptor")

# initialize a dataframe from the nba dataset
nba_df = pd.DataFrame(nba_dataset["train"])

# make a player_df with seasons and every player for that season
player_df = nba_df[["season", "player_name"]].copy()


def get_players(this_season, df=player_df):
    """Get the players for a given season"""
    # get the players for the given season
    season_players = df[df["season"] == this_season]["player_name"].unique().tolist()

    return gr.Dropdown.update(choices=season_players), gr.update(visible=False)


def get_forecast(this_year, this_player):
    """Get the forecast for a given player and year and the performance for entire career"""
    # load data
    nba_data_fore = load_dataset("andrewkroening/538-NBA-Historical-Raptor")

    # initialize a dataframe from the nba dataset
    df = pd.DataFrame(nba_data_fore["train"])

    # truncate to the player selected
    dataset = df[df["player_name"] == this_player]
    player_data = dataset[["season", "war_total"]].copy()
    # player_perform = player_df.copy()

    # make a list of the seasons the player played in
    player_seasons = player_data["season"].unique().tolist()

    # make two dfs, one for actual performance and one for the model
    # player_perform = player_perform[player_perform["season"] <= year + 5]
    player_data = player_data[player_data["season"] <= this_year]

    # convert the season column to a datetime object
    player_data["season"] = pd.to_datetime(player_data["season"], format="%Y")

    # set the df for prophet
    player_data.columns = ["ds", "y"]
    player_data = player_data.sort_values("ds")

    # build the prophet model
    m = Prophet(seasonality_mode="multiplicative").fit(player_data)
    future = m.make_future_dataframe(periods=5, freq="Y")
    forecast = m.predict(future)

    # plot the forecast
    fig1 = m.plot(forecast, xlabel="Year", ylabel="Wins Above Replacement")

    # plot the actual performance
    # fig2 = player_perform.plot(
    #     x="season", y="war_total", title="Actual Performance", template="plotly_white")

    # return the figure

    return fig1, gr.Dropdown.update(choices=player_seasons), gr.update(visible=True)


with gr.Blocks() as demo:

    gr.Markdown(
        """
    ### This is a slightly comical NBA Player Performance Predictor.

    ***It is designed to show a projection for performance (Wins Above Replacement) and compare it to the actual performance over a career.***
    
    ***If the projection hangs, it is because the model is taking a long time to run. Refresh the page and give it another shot...get it?***
    """
    )
    with gr.Row():
        year = gr.Dropdown(1977, 2021, label="Season", interactive=True, step=1)
        player = gr.Dropdown(players, label="Player", interactive=True)

    with gr.Column(visible=False) as output_col:
        gr.Markdown(
            "**Below is the player forecast for the selected season plus 5 years. Next to the graph is a dropdown you can use to change the season and update the chart and see how a player's projection has changed over time.**"
        )

        with gr.Row():
            season = gr.Dropdown(seasons, label="Season", interactive=True, step=1)

        with gr.Row():
            plt = gr.Plot()

    year.change(get_players, inputs=year, outputs=[player, output_col])
    player.change(
        get_forecast, inputs=[year, player], outputs=[plt, season, output_col]
    )
    season.change(
        get_forecast, inputs=[season, player], outputs=[plt, season, output_col]
    )

demo.launch()
