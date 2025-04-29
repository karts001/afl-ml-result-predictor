import datetime


field_names = [
    "kicks", "marks", "handballs", "disposals", "goals", "behinds", 
    "hitouts", "tackles", "rebound50s", "inside50s", "clearances", 
    "clangers", "free_kicks_for", "free_kicks_against", "brownlow_votes",
    "contested_possessions", "uncontested_possessions", "contested_marks",
    "marks_inside", "one_percenters", "bounces", "goal_assist", "percent_played"
]

name_corrections = {
    "OConnell": ["o", "connell"],
    "OSullivan": ["o", "sullivan"]
}

def convert_date_format(date_str):
    """
    Convert date from DD-MMM-YYYY format to YYYY-MM-DD format
    
    Args:
        d`ate_str (str): Date in format like '16-Mar-2025'
        
    Returns:
        str: Date in format 'YYYY-MM-DD'
    """
    # Parse the date string using datetime
    date_obj = datetime.datetime.strptime(date_str, '%d-%b-%Y')
    
    # Format the date object to the desired format
    formatted_date = date_obj.strftime('%Y-%m-%d')
    
    return formatted_date

def before_second_dot(value: str) -> str:
    """Helper function which extracts relevant data from afl tables website.
    Scores from each quarter are listed in the following format G.B.T
    G stands for goals (6 points), B is for Behinds (1 point), and T is the total
    The original kaggle data ommited the total score from each quarter so to keep the data consistent
    I am ommiting it as well.

    Args:
        value (str): quarter score in B.G.T format

    Returns:
        str: score string with total score removed
    """
    parts = value.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else value