import pandas as pd
import numpy as np
import warnings
import pybaseball
from pybaseball import statcast

warnings.filterwarnings('ignore')

def process_statcast_data(start_date, end_date, output_path):
    # Load statcast data
    all_play_data2 = statcast(start_date, end_date)
    all_play_data = pd.concat([all_play_data2])

    # Subset only first inning
    fi_2022 = all_play_data[all_play_data['inning'] == 1]

    # Subset only last pitch of AB
    fi_ab_2022 = fi_2022[fi_2022['events'].notnull()]
    fi_ab_2022['barrel'] = fi_ab_2022.apply(
        lambda row: np.nan if pd.isna(row['launch_speed']) or pd.isna(row['launch_angle']) else (1 if row['launch_speed'] > 98.0 and 25.9 <= row['launch_angle'] <= 30.1 else 0), axis=1)

    # Create dummy variable for all possible events
    fi_ab_events_2022 = pd.concat([fi_ab_2022, pd.get_dummies(fi_ab_2022['events'])], axis=1)

    # Columns for home and away teams
    fi_ab_events_2022["fielding_team"] = np.where(fi_ab_events_2022["inning_topbot"] == "Bot", 
                                                  fi_ab_events_2022["away_team"], fi_ab_events_2022["home_team"])

    # One row for each half inning
    grouped = fi_ab_events_2022.groupby(['game_pk', 'inning_topbot'])
    fi_grouped_2022 = grouped.agg({
        'game_date': 'first',
        'player_name': 'first',
        'pitcher': 'first',
        'home_team': 'first',
        'away_team': 'first',
        'p_throws': 'first',
        'fielding_team': 'first',
        'launch_speed': 'mean',
        'estimated_woba_using_speedangle': 'mean',
        'estimated_ba_using_speedangle': 'mean',
        'home_score': 'max',
        'away_score': 'max',
        'delta_run_exp': 'sum',
        'strikeout': 'sum',
        'grounded_into_double_play': 'sum',
        'single': 'sum',
        'double': 'sum',
        'triple': 'sum',
        'home_run': 'sum',
        'walk': 'sum',
        'field_out': 'sum',
        'fielders_choice_out': 'sum',
        'hit_by_pitch': 'sum',
        'sac_fly': 'sum',
        'field_error': 'sum',
        'caught_stealing_2b': 'sum',
        'catcher_interf': 'sum',
        'fielders_choice': 'sum',
        'double_play': 'sum',
        'sac_bunt': 'sum',
        'caught_stealing_home': 'sum',
        'caught_stealing_3b': 'sum',
        'other_out': 'sum',
        'barrel': 'mean'
    }).reset_index()

    # Create variables for hitting team and runs scored
    fi_grouped_2022["hitting_team"] = np.where(fi_grouped_2022["inning_topbot"] == "Bot",
                                               fi_grouped_2022["home_team"], fi_grouped_2022["away_team"])
    fi_grouped_2022["hitting_runs"] = np.where(fi_grouped_2022["inning_topbot"] == "Bot",
                                               fi_grouped_2022["home_score"], fi_grouped_2022["away_score"])

    # Add derived variables
    fi_grouped_2022['hits'] = fi_grouped_2022['single'] + fi_grouped_2022['double'] + fi_grouped_2022['triple'] + fi_grouped_2022['home_run']
    fi_grouped_2022['outs'] = fi_grouped_2022['strikeout'] + fi_grouped_2022['grounded_into_double_play'] + fi_grouped_2022['field_out'] + fi_grouped_2022['fielders_choice_out'] + fi_grouped_2022['field_error'] + fi_grouped_2022['fielders_choice'] + fi_grouped_2022['double_play']
    fi_grouped_2022['walks'] = fi_grouped_2022['walk'] + fi_grouped_2022['hit_by_pitch']
    fi_grouped_2022['xbh'] = fi_grouped_2022['double'] + fi_grouped_2022['triple'] + fi_grouped_2022['home_run']

    # Create basic statistics
    fi_grouped_2022['avg'] = fi_grouped_2022['hits'] / (fi_grouped_2022['hits'] + fi_grouped_2022['outs'])
    fi_grouped_2022['era'] = fi_grouped_2022['hitting_runs'] * 9
    fi_grouped_2022['slg'] = (fi_grouped_2022['single'] + 2 * fi_grouped_2022['double'] + 3 * fi_grouped_2022['triple'] + 4 * fi_grouped_2022['home_run']) / (fi_grouped_2022['hits'] + fi_grouped_2022['outs'])
    fi_grouped_2022['obp'] = (fi_grouped_2022['hits'] + fi_grouped_2022['walks']) / (fi_grouped_2022['hits'] + fi_grouped_2022['walks'] + fi_grouped_2022['outs'])
    fi_grouped_2022['ops'] = fi_grouped_2022['slg'] + fi_grouped_2022['obp']
    fi_grouped_2022['whip'] = fi_grouped_2022['hits'] + fi_grouped_2022['walks']
    fi_grouped_2022['games_played'] = 1
    fi_grouped_2022['hr9'] = (fi_grouped_2022['home_run'] / fi_grouped_2022['games_played']) * 9

    # Fix data types for modeling
    fi_grouped_2022['era'] = fi_grouped_2022['era'].astype('float')
    fi_grouped_2022['strikeout'] = fi_grouped_2022['strikeout'].astype('float')
    fi_grouped_2022['home_run'] = fi_grouped_2022['home_run'].astype('float')
    fi_grouped_2022['whip'] = fi_grouped_2022['whip'].astype('float')
    fi_grouped_2022['launch_speed'] = fi_grouped_2022['launch_speed'].astype('float')
    fi_grouped_2022['estimated_woba_using_speedangle'] = fi_grouped_2022['estimated_woba_using_speedangle'].astype('float')
    fi_grouped_2022['estimated_ba_using_speedangle'] = fi_grouped_2022['estimated_ba_using_speedangle'].astype('float')
    fi_grouped_2022['hitting_runs'] = fi_grouped_2022['hitting_runs'].astype('float')

    # Sort by game_date
    fi_grouped_2022 = fi_grouped_2022.sort_values(by='game_date')

    # Save the DataFrame to a CSV file
    fi_grouped_2022.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}")

# Example usage:
process_statcast_data('2024-3-20', '2024-10-01', 'fi_grouped_2022.csv')
