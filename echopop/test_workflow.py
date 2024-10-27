from pathlib import Path

import boto3
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError

import echopop.live.live_visualizer as elv
from echopop.live import live_data_loading as eldl, live_data_processing as eldp
from echopop.live.live_core import LIVE_DATA_STRUCTURE, LIVE_INPUT_FILE_CONFIG_MAP
from echopop.live.live_survey import LiveSurvey
from echopop.live.sql_methods import SQL, get_table_key_names, sql_data_exchange

sql_group_update, query_processed_files, sql_update_strata_summary
from functools import reduce

from echopop.acoustics import to_dB, to_linear, ts_length_regression
from echopop.live.live_acoustics import average_sigma_bs, compute_nasc
from echopop.live.live_biology import compute_sigma_bs
from echopop.live.live_data_loading import filter_filenames, read_biology_csv
from echopop.live.live_spatial_methods import apply_spatial_definitions
from echopop.utils.operations import group_interpolator_creator

##################################################################################################
# TEST: Set up `LiveSurvey` object
# NOTE: General initialization parameter configuration
live_init_config_path = "C:/Users/Brandyn/Documents/GitHub/echopop/config_files/live_initialization_config.yml"
# NOTE: File configuration
live_file_config_path = "C:/Users/Brandyn/Documents/GitHub/echopop/config_files/live_survey_year_2019_config.yml"
# NOTE: Create object
realtime_survey = LiveSurvey(live_init_config_path, live_file_config_path, verbose=True)

# NOTE: String-representation via `LiveSurvey.__repr__`:
# NOTE: Lists current files being processed and linked databases (WIP)
realtime_survey
#################################################################################################
# TEST: TRIGGER --> NEW ACOUSTIC DATA
# NOTE: Load new acoustic data (Either glob file search or `input_filenames Optional[List[str]]`)
realtime_survey.load_acoustic_data()
# NOTE: Process new acoustic data
# NOTE: This will update linked database tables
realtime_survey.process_acoustic_data()
# NOTE: Generate population estimates (or pass if there are no biological data)
# NOTE: `working_dataset = Literal["acoustic", "biology"]`
realtime_survey.estimate_population(working_dataset="acoustic")
# NOTE: String-representation via `LiveSurvey.__repr__`:
# NOTE: Lists current files being processed and linked databases (WIP)
realtime_survey.input["acoustics"]
##################################################################################################
# TEST: TRIGGER --> NEW BIOLOGY DATA
# NOTE: Load new biological data (Either glob file search or `input_filenames Optional[List[str]]`
realtime_survey.load_biology_data()
# NOTE: Process new biological data
# NOTE: This will update linked database tables
realtime_survey.process_biology_data()
# NOTE: Generate population estimates (or pass if there are no acoustic data)
# NOTE: `working_dataset = Literal["acoustic", "biology"]`
realtime_survey.estimate_population(working_dataset="biology")
# NOTE: String-representation via `LiveSurvey.__repr__`:
# NOTE: Lists current files being processed and linked databases (WIP)
realtime_survey
##################################################################################################
# TEST: `LiveSurvey` --[`files_processed`]--> `Echodataflow`
# NOTE: `LiveSurvey.meta` attribute
# ---- ACOUSTIC
realtime_survey.meta["provenance"]["acoustic_files"]
# ---- BIOLOGICAL
realtime_survey.meta["provenance"]["biology_files"]
# NOTE: SQL function query from database file [cumulative list]
# ---- ACOUSTIC
SQL(db_file=realtime_survey.config["database"]["acoustics"],
    command="select", table_name="files_processed")
dat = SQL(db_file=realtime_survey.config["database"]["acoustics"],command="select",
table_name="files_processed")
# ---- BIOLOGICAL
SQL(db_file=realtime_survey.config["database"]["biology"],command="select",
table_name="files_processed")
##################################################################################################
# TEST: `LiveSurvey` --[(key) SQL tables]--> Users
# !!! The SQL functions will fail if the tables have not yet been created/initialized
# ---- ACOUSTICS
# NOTE: Mean linear backscatter coefficient (`sigma_bs`) keyed for each haul and stratum
SQL(realtime_survey.config["database"]["biology"], "select", table_name="sigma_bs_mean_df")
SQL(realtime_survey.config["database"]["biology"], "select", table_name="specimen_df")
.latitude.max()
realtime_survey.input["spatial"]["strata"]
# NOTE: Along-track acoustically-derived number/biomass densities and NASC
SQL(realtime_survey.config["database"]["acoustics"], "select", table_name="survey_data_df")
# ---- BIOLOGICAL
# NOTE: Fitted (discretized) length-weight relationship
SQL(realtime_survey.config["database"]["biology"], "select", table_name="weight_fitted_df")
# NOTE: Quantized length-binned weights (summed)
SQL(realtime_survey.config["database"]["biology"], "select", table_name="length_weight_df")
# NOTE: Average weights per stratum
SQL(realtime_survey.config["database"]["biology"], "select", table_name="weight_stratum_df")
# NOTE: Stratum summary tables
SQL(realtime_survey.config["database"]["biology"], "select", table_name="strata_summary_df")
##################################################################################################
# FROM THE `LiveSurvey` object !
# ---- Convert to a Panel
import panel as pn

# ---- Either have the db file already called in as a `pandas.DataFrame`, or query the table
survey_data_db = Path(realtime_survey.config["database"]["acoustics"])
grid_db = Path(realtime_survey.config["database"]["grid"])
coast_db = grid_db
biology_db = Path(realtime_survey.config["database"]["biology"])
projection = realtime_survey.config["geospatial"]["projection"]
# NOTE: PLOTS
# Ensure Panel is initialized
pn.extension()
# ---- Helper function
def plt_to_pn(fig):
    # Convert to a panel object
    panel = pn.panel(fig)
    # Display
    panel.show() # OR panel.servable() if you want to serve it in a Panel server
# ---- PLOT GRID
fig = elv.plot_livesurvey_grid(grid_db, projection, coast_db)
fig.show()
plt_to_pn(fig)
# ---- PLOT TRACK
from echopop.live.live_visualizer import plot_livesurvey_track

fig1 = plot_livesurvey_track(survey_data, projection, coast_db)
fig1.show()
plt_to_pn(fig1)
# ---- PLOT DISTRIBUTIONS
weight_table = SQL(biology_db, "select",
                   table_name="length_weight_df")
stratum_table = SQL(biology_db, "select",
                    table_name="strata_summary_df")
specimen_table = SQL(biology_db, "select",
                     table_name="specimen_data_df")
length_table = SQL(biology_db, "select",
                   table_name="length_df")
fig2 = elv.plot_livesurvey_distributions(weight_table, stratum_table, specimen_table,
length_table)
plt_to_pn(fig2)
### MULTIPANEL
panel0 = pn.panel(fig, name='Gridded population estimates')
panel1 = pn.panel(fig1, name='Alongtrack population estimates')
panel2 = pn.panel(fig2, name='Length and weight distributions')

def serve_panels():
    # Create links to each panel
    home = pn.Column(
        pn.pane.Markdown("# Main Page"),
        pn.pane.Markdown("[Gridded population estimates](gridded_population_estimates)",
sizing_mode="stretch_width"),
        pn.pane.Markdown("[Alongtrack population estimates](alongtrack_population_estimates)",
sizing_mode="stretch_width"),
        pn.pane.Markdown("[Length and weight distributions](length_weight_distributions)",
sizing_mode="stretch_width")
    )

    # Serve the home page and individual panels
    pn.serve({
        'Main Page': home,
        'gridded_population_estimates': panel0,
        'alongtrack_population_estimates': panel1,
        'length_weight_distributions': panel2
    },  show=True)
# Run the function to serve panels
serve_panels()
