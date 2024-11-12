from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from functools import wraps

import remote_cmds as rmtcmd
import conf.app_config as app_config
import users_service as userservice
import datasets_service as dsservice


app = Flask(__name__)

USERNAME = app_config.BASIC_AUTH[0]
PASSWORD = app_config.BASIC_AUTH[1]

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        "Access Denied: Please provide valid credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Apply the authentication decorator to all routes
@app.before_request
@requires_auth
def secure_all_routes():
    pass

#### Index Routes ####

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


@app.route('/addUserFiles/<username>')
def add_user_files(username):
    user_details = userservice.get_user_details(username)
    datasets = dsservice.get_datasets_from_csv()
    return render_template('add_user_files.html', user=user_details, datasets=datasets)


@app.route('/edit_home/<username>')
def edit_home(username):
    user_details = userservice.get_user_details(username)
    try:
        rmtcmd.download_index_file(username)
        with open('tmp/index.html', 'r') as file:
            content = file.read()
        return render_template('edit_home.html', user=user_details, content=content)
    except FileNotFoundError:
        return "Homepage content not found.", 404
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

#### End Index Routes ###


@app.route('/get_user_expiry', methods=['GET'])
def get_user_expiry():
    username = request.args.get('username')
    expiry = userservice.get_user_details(username)['expiry'] # Function to retrieve expiry
    return jsonify({"expiry": expiry})


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


@app.route('/get_files/<dataset>')
def get_files(dataset):
    dataset_filepath_map = dsservice.get_dataset_files_paths()
    filepath = dataset_filepath_map[dataset]

    files = rmtcmd.list_histpack_files(filepath)
    return jsonify(files)


@app.route('/link_files', methods=['POST'])
def link_files():
    data = request.get_json()
    username = data.get("user")  # Get the selected files from the request
    filepaths = data.get('files')

    rmtcmd.create_symlinks_for_files(username, filepaths)
    return jsonify({'status': 'success', 'message': 'Files linked successfully!'})


@app.route('/save_homepage_content', methods=['POST'])
def save_homepage_content():
    try:
        username = request.form['username']
        user_details = userservice.get_user_details(username)
        html_content = request.form['htmlContent']
        with open('tmp/index_e.html', 'w') as file:
            file.write(html_content)
        
        rmtcmd.scp_edited_index_file_to_remote(username)
        return render_template('edit_home.html', success=True, user=user_details, content=html_content)
    except Exception as e:
        return render_template('edit_home.html', user=user_details, content=html_content)


if __name__ == '__main__':
    app.run(debug=True)
