from threading import Thread
from flask import Flask, request, jsonify, render_template
from structure_final import *
import atexit
import os
import json

## Initialize Flask
app = Flask(__name__)

## Function to initialize the program with past data  
def initialize_data():
    controller.transfer_and_clear_log()  # Ensure all data is consolidated into main.json
    load_main_json_into_data_structures()
    controller.transfer_and_clear_log_vote()
    load_main_vote_json_into_data_structures()

## Function to load main json file to rebuild tree structure
def load_main_json_into_data_structures():
    main_file_path = 'main.json'
    # Check if the file exists and is not empty
    if os.path.isfile(main_file_path) and os.path.getsize(main_file_path) > 0:
        with open(main_file_path, 'r') as main_file:
            try:
                main_data = json.load(main_file)
                # Ensure that main_data is not empty and is a list (as expected)
                if main_data and isinstance(main_data, list):
                    for destination in main_data:
                        # Extract destination information including user_id
                        user_id = destination.get('user_id')
                        name = destination.get('name')
                        country = destination.get('country')
                        destination_type = destination.get('destination_type')
                        review = destination.get('review')
                        vote_count = destination.get('vote_count', 1)  # Default to 1 if vote_count is not provided
                        # Call add_destination_from_json with all extracted information
                        controller.add_destination_from_json(user_id, name, country, destination_type, review, vote_count)
                        votes.add((user_id, name))
            except json.JSONDecodeError:
                # Handle case where the file is not a valid JSON (corrupted or incorrectly formatted)
                print("Error reading main.json: File is not a valid JSON.")
    else:
        # Handle case where main.json does not exist or is empty
        print("main.json does not exist or is empty. No data to load.")

## Function to load voting count to the data structure
def load_main_vote_json_into_data_structures():
    main_file_path = 'main_vote.json'
    # Check if the file exists and is not empty
    if os.path.isfile(main_file_path) and os.path.getsize(main_file_path) > 0:
        with open(main_file_path, 'r') as main_file:
            try:
                main_data = json.load(main_file)
                # Ensure that main_data is not empty and is a list (as expected)
                if main_data and isinstance(main_data, list):
                    for destination in main_data:
                        # Extract destination information including user_id
                        user_id = destination.get('user_id')
                        name = destination.get('name')
                        country = destination.get('country') 
                        #vote_count = destination.get('vote_count')
                        # Call add_destination_from_json with all extracted information
                        controller.add_vote_from_json(name, country, user_id,)
                        votes.add((user_id, name))
            except json.JSONDecodeError:
                # Handle case where the file is not a valid JSON (corrupted or incorrectly formatted)
                print("Error reading main.json: File is not a valid JSON.")
    else:
        # Handle case where main.json does not exist or is empty
        print("main_vote.json does not exist or is empty. No data to load.")

## Record User ID in txt file
def user_id_counter_func():
    with open('user_id_counter.txt', 'w') as file:
        file.write(str(user_id_counter))

## Function to start schedule transfer and clearing of files
def start_scheduled_transfer():
    controller.schedule_transfer()

#%%
# Route to serve interface.html
@app.route('/')
def home():
    return render_template('Interface.html')

## Route to get user id
@app.route('/get_user_id', methods=['GET'])
def get_user_id():
    global user_id_counter
    user_id = user_id_counter
    user_id_counter += 1

    return jsonify({"user_id": user_id}), 200

## Route to get all destinations information
@app.route('/get_destinations', methods=['GET'])
def get_all_destinations():
    destinations = controller.get_all_destinations()
    return jsonify(destinations)

## Route to add new destination
@app.route('/submit', methods=['POST'])
def add_destination():
    try:
        # Extract destination details from the request's JSON body
        data = request.json
        user_id = data.get('user_id')
        name = data.get('name')
        country = data.get('country')
        destination_type = data.get('destination_type')
        review = data.get('review')
        
        controller.add_destination(user_id, name, country, destination_type, review)
        votes.add((user_id, name))
        return jsonify({'message': 'Destination added successfully'}), 201

    except Exception as e:
        # Catching any exceptions and returning an error message
        return jsonify({"message": f"Error: {str(e)}"}), 500

## Route to check if user have voted the place before
@app.route('/checkVote/<userId>/<place_name>', methods=['GET'])
def check_vote(userId, place_name):
    has_voted = (userId, place_name) in votes
    return jsonify({'hasVoted': has_voted})

## Route to add user vote
@app.route('/vote/<userId>/<country>/<place_name>', methods=['POST'])
def vote(userId, country, place_name):
    print(f"Received vote request for {place_name}")
    controller.add_vote(place_name, country, userId)
    votes.add((userId, place_name))
    return jsonify({"message": "Vote successful"})

## Route to write new user id to backend
@app.route('/userid', methods=['POST'])
def submit_user_id():
    try:
        data = request.get_json()
        user_id = data['user_id']

        return jsonify({"message": "User ID submitted successfully"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

## Route to send user voting history to front end
@app.route('/getUserHistory', methods = ['POST'])
def get_voting_history():
    try:
        data = request.json
        user_id = data.get('user_id')
        ## Get information about the voted destinations places
        voted_destinations = controller.get_user_voting_history(user_id)
        all_nodes = controller.get_all_destinations()
        if voted_destinations is not None:
            voting_history = []
            for node in all_nodes:
                for place in voted_destinations:
                    if place == node[0]:
                        voting_history.append((node[0], node[1], node[2], node[3], node[4]))
            return jsonify({'voting_history': voting_history}), 200
        
        if voted_destinations is None:
            print('ID not found')
            return jsonify({'no_users': 'User ID is not found'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Internal Server error: {str}'}), 500

    
#%%
# Admin Section
# Route to go to the Admin page
@app.route('/admin')
def admin_page():
    return render_template('interface_admin_final.html')

# Route to get top destinations
@app.route('/admin/top_destinations', methods=['GET'])
def get_top_destinations():
    try:
        num_destinations = int(request.args.get('num', 5))  # Default to fetching top 5 destinations
        ## get_top_destinations does not exist in controller ##
        top_destinations = controller.get_top_destinations(num_destinations)
        return jsonify({"topDestinations": top_destinations}), 200
    
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


#%%
## Initialize the data structure
controller = destination_tree_controller()
votes = set()

initialize_data()
atexit.register(user_id_counter_func)


# Initialize user ID counter
try:
    with open('user_id_counter.txt', 'r') as file:
        user_id_counter = int(file.read())
except FileNotFoundError:
    user_id_counter = 1


if __name__ == '__main__':
    transfer_thread = Thread(target=start_scheduled_transfer)
    transfer_thread.daemon = True  # This makes the thread exit when the main program exits
    transfer_thread.start()
    
    app.run(debug=False, port=5050, host='localhost')
