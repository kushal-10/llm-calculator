import pandas as pd
import gradio as gr
import os
from gradio_rangeslider import RangeSlider
import calendar
import datetime

from src.filter_utils import filter, filter_cols
from src.process_data import merge_data
import assets.text_content as tc

# Main Leaderboard containing everything
text_leaderboard = pd.read_csv(os.path.join('assets', 'merged_data.csv'))
text_leaderboard = text_leaderboard.sort_values(by=tc.CLEMSCORE, ascending=False)  

# When displaying latency values
text_leaderboard[tc.LATENCY] = text_leaderboard[tc.LATENCY].round(1)
text_leaderboard[tc.CLEMSCORE] = text_leaderboard[tc.CLEMSCORE].round(1)

open_weight_df = text_leaderboard[text_leaderboard[tc.OPEN_WEIGHT] == True]
if not open_weight_df.empty:  # Check if filtered df is non-empty
    # Get max parameter size, ignoring NaN values
    params = open_weight_df[tc.PARAMS].dropna()
    max_parameter_size = params.max() if not params.empty else 0

# Short leaderboard containing fixed columns
short_leaderboard = filter_cols(text_leaderboard)
# html_table = short_leaderboard.to_html(escape=False, index=False)

## Extract data
langs = []
licenses = []
ip_prices = []
op_prices = []
latencies = []
parameters = []
contexts = []
dates = []

for i in range(len(text_leaderboard)):
    lang_splits = text_leaderboard.iloc[i][tc.LANGS].split(',')
    lang_splits = [s.strip() for s in lang_splits]
    langs += lang_splits
    license_name = text_leaderboard.iloc[i][tc.LICENSE_NAME]

    licenses.append(license_name)
    ip_prices.append(text_leaderboard.iloc[i][tc.INPUT])
    op_prices.append(text_leaderboard.iloc[i][tc.OUTPUT])
    latencies.append(text_leaderboard.iloc[i][tc.LATENCY])
    parameters.append(text_leaderboard.iloc[i][tc.PARAMS])
    contexts.append(text_leaderboard.iloc[i][tc.CONTEXT])
    dates.append(text_leaderboard.iloc[i][tc.RELEASE_DATE])


langs = list(set(langs))
langs.sort()

licenses = list(set(licenses))
licenses.sort()

max_input_price = max(ip_prices)
max_output_price = max(op_prices)
max_latency = text_leaderboard[tc.LATENCY].max().round(3)

min_parameters = 0 if pd.isna(min(parameters)) else min(parameters)
max_parameter = max_parameter_size
parameter_step = 1

min_context = min(contexts)
max_context = max(contexts)
context_step = 8

min_date = min(dates)
max_date = max(dates)

# Date settings
today = datetime.date.today()
end_year = today.year
start_year = tc.START_YEAR

YEARS = list(range(int(start_year), int(end_year)+1))
YEARS = [str(y) for y in YEARS] 
MONTHS = list(calendar.month_name[1:])

TITLE = tc.TITLE

llm_calc_app = gr.Blocks()
with llm_calc_app:

    gr.HTML(TITLE)

    with gr.Row():

        #####################################
        # First Column
        ####################################
        ## Language Select
        with gr.Column(scale=2):

            with gr.Row():
                lang_dropdown = gr.Dropdown(
                    choices=langs,
                    value=[],
                    multiselect=True,
                    label="Languages 🗣️"
                )

            
            ## Release Date range selection
                
            with gr.Row():
                start_year_dropdown = gr.Dropdown(
                    choices = YEARS,
                    value=[],
                    label="Model Release - Year 🗓️"
                )
                start_month_dropdown = gr.Dropdown(
                    choices = MONTHS,
                    value=[],
                    label="Month 📜"
                )

                end_year_dropdown = gr.Dropdown(
                    choices = YEARS,
                    value=[],
                    label="End - Year 🗓️"
                )
                end_month_dropdown = gr.Dropdown(
                    choices = MONTHS,
                    value=[],
                    label="Month 📜"
                )
            
            ## Price selection
            with gr.Row():

                input_pricing_slider = RangeSlider(
                    minimum=0, 
                    maximum=max_input_price, 
                    value=(0, max_input_price), 
                    label="💲/1M input tokens",
                    elem_id="double-slider-3"
                )

                output_pricing_slider = RangeSlider(
                    minimum=0, 
                    maximum=max_output_price, 
                    value=(0, max_output_price), 
                    label="💲/1M output tokens",
                    elem_id="double-slider-4"
                )

            # License selection
            with gr.Row():
                license_checkbox = gr.CheckboxGroup(
                    choices=licenses,
                    value=licenses,
                    label="License 🛡️",
                )    
        
        #############################################################
        # Second Column
        #############################################################
        with gr.Column(scale=1):

            ####### parameters ###########
            with gr.Row():
                parameter_slider = RangeSlider(
                    minimum=0, 
                    maximum=max_parameter, 
                    label=f"Parameters 🔍 {int(min_parameters)}B - {int(max_parameter)}B+",
                    elem_id="double-slider-1",
                    step=parameter_step
                )

                
            ########### Context range ################

            with gr.Row():
                context_slider = RangeSlider(
                    minimum=0, 
                    maximum=max_context, 
                    label="Context (k) 📏",
                    elem_id="double-slider-2",
                    step=context_step
                )

            ############# Modality selection checkbox ###############
            with gr.Row():
                multimodal_checkbox = gr.CheckboxGroup(
                    choices=[tc.SINGLE_IMG, tc.MULT_IMG, tc.AUDIO, tc.VIDEO],
                    value=[],
                    label="Additional Modalities 📷🎧🎬",
                )
                
            
            # ############### Model Type Checkbox ###############
            with gr.Row():
                open_weight_checkbox = gr.CheckboxGroup(
                    choices=[tc.OPEN, tc.COMM],
                    value=[tc.OPEN, tc.COMM],
                    label="Model Type 🔓 💼",
                )    
                
       

    with gr.Row():
        """
        Main Leaderboard Row
        """

        leaderboard_table = gr.Dataframe(
                                value=short_leaderboard,
                                elem_id="text-leaderboard-table",
                                interactive=False,
                                visible=True,
                                datatype=['str', 'number', 'number', 'date', 'number', 'number', 'number', 'number', 'markdown']
                            )
        
        dummy_leaderboard_table = gr.Dataframe(
                                value=text_leaderboard,
                                elem_id="dummy-leaderboard-table",
                                interactive=False,
                                visible=False
                            )
        
        lang_dropdown.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],   
            queue=True
        )

        parameter_slider.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        input_pricing_slider.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        output_pricing_slider.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        multimodal_checkbox.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        open_weight_checkbox.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        context_slider.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        start_year_dropdown.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        start_month_dropdown.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        end_year_dropdown.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        end_month_dropdown.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

        license_checkbox.change(
            filter,
            [dummy_leaderboard_table, lang_dropdown, parameter_slider,
             input_pricing_slider, output_pricing_slider, multimodal_checkbox,
             context_slider, open_weight_checkbox, start_year_dropdown, start_month_dropdown, end_year_dropdown, end_month_dropdown, license_checkbox],
            [leaderboard_table],
            queue=True
        )

    llm_calc_app.load()
llm_calc_app.queue()
llm_calc_app.launch()
