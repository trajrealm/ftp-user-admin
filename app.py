from flask import Flask, render_template, request, redirect, url_for, jsonify

import remote_cmds as rmtcmd
import conf.app_config as app_config
import users_service as userservice
import datasets_service as dsservice


app = Flask(__name__)


@app.route('/get_user_expiry', methods=['GET'])
def get_user_expiry():
    username = request.args.get('username')
    expiry = userservice.get_user_details(username)['expiry'] # Function to retrieve expiry
    return jsonify({"expiry": expiry})


@app.route('/update_user_expiry', methods=['POST'])
def update_user_expiry():
    try:
        username = request.form.get('username')
        new_expiry = request.form.get('expiry_date')
        rmtcmd.update_user_trial_end(username, new_expiry)
        return jsonify({"success": "true"})
    except Exception as e:
        print(f"Error in updating expiry {e}")
        return jsonify({"error":f"{e}"})


@app.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        username = request.args.get('username')
        new_password, hash_pass = rmtcmd.reset_password(username)
        return jsonify({"success": "true", "password": new_password, "userlink": f"http://{username}:{new_password}@{app_config.REMOTE_HOST}/~{username}/"})
    except Exception as e:
        print(f"Error in resetting password {e}")
        return jsonify({"error":f"{e}"})

    
@app.route('/addUserDataset/<username>')
def add_user_dataset(username):
    user_details = userservice.get_user_details(username)
    datasets = dsservice.get_datasets_from_csv()
    return render_template('update_user.html', user=user_details, datasets=datasets)


@app.route('/add', methods=['GET', 'POST'])
def add_user_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        expiry = request.form.get('expiry')
        selected_datasets = request.form.getlist('datasets')

        if not selected_datasets:
            return render_template('add_user.html', datasets=dsservice.get_datasets_from_csv(), error="At least one dataset is required")

        passwds = userservice.register_user_with_datasets(username, selected_datasets, expiry)
        # (newpass, hashpass) = ("asdfqwerasd","123444asdfff")
        success = True if passwds[0] and passwds[1] != None and passwds[2]!= None else False
        newpass = passwds[1]                                                                        
        
        if success:
            user_link = f"http://{username}:{newpass}@{app_config.REMOTE_HOST}/~{username}/"
            datasets = dsservice.get_datasets_from_csv()
            return render_template('add_user.html', datasets=datasets, user_link=user_link, username=username, password=newpass, expiry=expiry, selected_datasets=selected_datasets)
            
        return "Error adding user", 500
    
    datasets = dsservice.get_datasets_from_csv()
    return render_template('add_user.html', datasets=datasets)

@app.route('/update/<username>', methods=['POST'])
def update(username):
    user_details = userservice.get_user_details(username)
    datasets = dsservice.get_datasets_from_csv()
    selected_datasets = request.form.getlist('datasets')
    if not selected_datasets:
        return render_template('update_user.html',user=user_details, datasets=datasets, error="At least one dataset is required")
    else:
        userservice.update_user_datasets(username, selected_datasets)
        user_details = userservice.get_user_details(username)
        return render_template('update_user.html', user=user_details, datasets=datasets) 



@app.route('/')
def search_user():
    query = request.args.get('query', '')  # Get search query from the form
    # users = get_user_list()
    users = None

    # Filter users based on search query
    if query:
        users = userservice.get_user_list()
        users = [user for user in users if query.lower() in user.lower()]

    return render_template('index.html', users=users, query=query)


if __name__ == '__main__':
    app.run(debug=True)
