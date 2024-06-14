import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import table

def calculate_nrfi_rating(overall_stats):
    # Weights for each statistic
    weights = {
        'NRFI Record': 0.05,
        'NRFI Streak': 0.05,
        'First-Inning Strikeout Rate (K%)': 0.10,
        'First-Inning Walk Rate (BB%)': 0.10,
        'First-Inning BAA': 0.10,
        'First-Inning OBP': 0.20,
        'First-Inning SLG': 0.15,
        'First-Inning OPS': 0.25
    }
    
    # Normalize the statistics based on their range or inverse range
    try:
        nrfi_record_wins = int(overall_stats['NRFI Record'].split('-')[0])
    except ValueError:
        nrfi_record_wins = 0
    games_played = overall_stats['Games Played']
    
    normalized_stats = {
        'NRFI Record': nrfi_record_wins / games_played if games_played > 0 else 0,  # Normalize by games played
        'NRFI Streak': overall_stats['NRFI Streak'] / games_played if games_played > 0 else 0,  # Normalize by games played
        'First-Inning Strikeout Rate (K%)': overall_stats['First-Inning Strikeout Rate (K%)'] / 100,
        'First-Inning Walk Rate (BB%)': (100 - overall_stats['First-Inning Walk Rate (BB%)']) / 100,  # Inverse
        'First-Inning BAA': 1 - overall_stats['First-Inning BAA'],  # Inverse
        'First-Inning OBP': 1 - overall_stats['First-Inning OBP'],  # Inverse
        'First-Inning SLG': 1 - overall_stats['First-Inning SLG'],  # Inverse
        'First-Inning OPS': 1 - overall_stats['First-Inning OPS']   # Inverse
    }
    
    # Calculate NRFI Rating
    nrfi_rating = sum(weights[stat] * normalized_stats[stat] for stat in weights) * 100
    
    return int(round(nrfi_rating))

def get_pitcher_statistics(file_path, player_name):
    # Load the CSV file
    data = pd.read_csv(file_path)
    
    # Filter data for the given player
    player_data = data[(data['player_name'] == player_name)]
    
    if player_data.empty:
        return {
            'Player Name': player_name,
            'Games Played': 0,
            'First-Innings Pitched': 0,
            'First-Innings Strikeouts': 0,
            'First-Innings Walks': 0,
            'ERA': 0,
            'WHIP': 0,
            'Home Runs Allowed': 0,
            'Hits Allowed': 0,
            'Runs Allowed': 0,
            'NRFI Record': '0-0',
            'NRFI Streak': 0,
            'First-Inning Strikeout Rate (K%)': 0,
            'First-Inning Walk Rate (BB%)': 0,
            'First-Inning BAA': 0,
            'First-Inning OBP': 0,
            'First-Inning SLG': 0,
            'First-Inning OPS': 0,
            'NRFI Rating': 0
        }
    
    # Calculate NRFI record
    nrfi_wins = 0
    nrfi_losses = 0
    
    # Calculate NRFI streak (current ongoing streak)
    player_data_sorted = player_data.sort_values(by='game_date')
    nrfi_streak = 0
    current_streak = 0

    for _, row in player_data_sorted.iterrows():
        if row['hitting_runs'] == 0 or row['hitting_runs'] == 0.0:
            nrfi_wins += 1
            current_streak += 1
        else:
            nrfi_losses += 1
            current_streak = 0
        nrfi_streak = max(nrfi_streak, current_streak)

    nrfi_record = f"{nrfi_wins}-{nrfi_losses}"
    
    # Calculate total batters faced
    total_batters_faced = (
        player_data['outs'].sum() / 3
        + player_data['hits'].sum()
        + player_data['walk'].sum()
        + player_data['home_run'].sum()
        + player_data['hit_by_pitch'].sum()
    )
    
    # Calculate strikeout rate and walk rate
    strikeout_rate = (player_data['strikeout'].sum() / total_batters_faced) * 100 if total_batters_faced > 0 else 0
    walk_rate = (player_data['walk'].sum() / total_batters_faced) * 100 if total_batters_faced > 0 else 0

    # Calculate additional first inning statistics
    first_inning_baa = player_data['hits'].sum() / total_batters_faced if total_batters_faced > 0 else 0
    first_inning_obp = (player_data['hits'].sum() + player_data['walk'].sum() + player_data['hit_by_pitch'].sum()) / total_batters_faced if total_batters_faced > 0 else 0
    first_inning_slg = player_data['slg'].mean() if not player_data['slg'].isnull().all() else 0
    first_inning_ops = player_data['ops'].mean() if not player_data['ops'].isnull().all() else 0
    
    # Calculate overall statistics for pitchers
    overall_stats = {
        'Player Name': player_name,
        'Games Played': len(player_data_sorted),
        'First-Innings Pitched': len(player_data_sorted),  # Each game represents one inning pitched
        'First-Innings Strikeouts': int(player_data['strikeout'].sum()),
        'First-Innings Walks': int(player_data['walk'].sum()),
        'ERA': round(player_data['era'].mean(), 2) if not player_data['era'].isnull().all() else 0,
        'WHIP': round(player_data['whip'].mean(), 2) if not player_data['whip'].isnull().all() else 0,
        'Home Runs Allowed': int(player_data['home_run'].sum()),
        'Hits Allowed': int(player_data['hits'].sum()),
        'Runs Allowed': int(player_data['hitting_runs'].sum()),
        'NRFI Record': nrfi_record,
        'NRFI Streak': nrfi_streak,
        'First-Inning Strikeout Rate (K%)': round(strikeout_rate, 2),
        'First-Inning Walk Rate (BB%)': round(walk_rate, 2),
        'First-Inning BAA': round(first_inning_baa, 3),
        'First-Inning OBP': round(first_inning_obp, 3),
        'First-Inning SLG': round(first_inning_slg, 3),
        'First-Inning OPS': round(first_inning_ops, 3)
    }
    
    overall_stats['NRFI Rating'] = calculate_nrfi_rating(overall_stats)
    
    return overall_stats

# Example usage
file_path = './fi_grouped_2022.csv'
player_names = ['Suárez, Ranger','Bradish, Kyle']

# Collect statistics for multiple players
stats_list = [get_pitcher_statistics(file_path, player) for player in player_names]

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(stats_list)

# Remove the index from the DataFrame
df.index = [''] * len(df)

print(df.to_string())
# Plot the DataFrame and save it as an image
fig, ax = plt.subplots(figsize=(20, 8))  # Set figure size as needed
ax.axis('tight')
ax.axis('off')

tbl = table(ax, df, loc='center', cellLoc='center')
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)

# Adjust column widths to fit the content
for key, cell in tbl.get_celld().items():
    cell.set_width(0.145)
    cell.set_height(0.05)

plt.savefig("./pitcher_stats_adjusted.png", bbox_inches='tight', dpi=300)
print("DataFrame saved as pitcher_stats_adjusted.png")
