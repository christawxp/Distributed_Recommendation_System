# data_processing.py

import json

def process_local_file(file_content):
    
    followers_id_mapping = {}

    # Iterate through each dictionary in the list
    for entry in file_content:
        # Extract 'id' and 'followers' from the dictionary
        entry_id = entry.get('id')
        followers = entry.get('followers', set())

        # Update the mapping in the new dictionary
        for follower in followers:
            if follower not in followers_id_mapping:
                followers_id_mapping[follower] = {entry_id}
            else:
                followers_id_mapping[follower].add(entry_id)

    return followers_id_mapping
