from remote_cmds import *
from datetime import datetime

import os
import paramiko
import conf.app_config as app_config
import datasets_service as dsutil


def get_user_list():
    try:
        # Initialize the SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect using the PEM file for authentication
        ssh_client.connect(app_config.REMOTE_HOST, username=app_config.SSH_USERNAME, key_filename=app_config.PEM_LOC)

        # Run a command to list directories under USER_DIR_PATH
        stdin, stdout, stderr = ssh_client.exec_command(f'sudo ls -d {app_config.HOME_DIRS}/*')
        user_dirs = stdout.read().decode().splitlines()

        # Extract user names from directory paths
        users = [user_dir.split('/')[-1] for user_dir in user_dirs]
        
        # Close the SSH connection
        ssh_client.close()
        return users

    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

# Function to get user details (expiry date and datasets) from the remote server
def get_user_details(username):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(app_config.REMOTE_HOST, username=app_config.SSH_USERNAME, key_filename=app_config.PEM_LOC)

        user_details = {
            'username': username,
            'expiry': '',
            'datasets': [],
            'filenames': []
        }

        # Retrieve the expiry date using chage command
        stdin, stdout, stderr = ssh_client.exec_command(f'sudo chage -l {username}')
        chage_output = stdout.read().decode().splitlines()

        for line in chage_output:
            if "Account expires" in line:
                user_details['expiry'] = convert_date_format(line.split(":")[1].strip())
                # user_details['expiry'] = '2024-11-30'
                break

        # Retrieve the list of datasets by listing symbolic links in .http_historical
        http_historical_path = f"{app_config.HOME_DIRS}/{username}/{app_config.USER_HISTORICAL_DIR}"
        stdin, stdout, stderr = ssh_client.exec_command(f'find {http_historical_path} -type l ! -xtype l -exec basename {{}} \;')
        filelinks = stdout.read().decode().splitlines()
        user_details['filenames'] = filelinks

        m = dsutil.get_dataset_reverse_map()
        for f in filelinks:
            prefix = "_".join(f.split("_")[:-2])
            dataset = m.get(prefix)
            user_details['datasets'].append(dataset)

        ssh_client.close()
        return user_details
    except Exception as e:
        print(f"Error fetching user details: {e}")
        return None


def add_user(username, expiry=None):
    create_user(username, expiry)
    newpass = generate_password()
    print(newpass)
    change_user_pwd(username, newpass)
    make_historical_dir(username)
    hashpass = get_encrypted_pass(newpass)
    print(hashpass)
    create_htaccess(username)
    insert_into_table(username, hashpass, expiry)
    change_owner(username)
    change_mod(username)
    return newpass, hashpass


def add_user_with_datasets(username, datasets, expiry=None):
    rm_local_tmp_index_html()
    (newpass, hashpass) = add_user(username, expiry)
    create_symlinks(username, datasets)
    homefile.indexfile_create(datasets)
    scp_local_index_file()
    mv_remote_index_file_to_home_dir(username)
    change_owner(username)
    return (newpass, hashpass)


def register_user_with_datasets(username, selected_datasets, expiry):
    try:
        (newpass, hashpass) = add_user_with_datasets(username, selected_datasets, expiry)
        return  (True, newpass, hashpass)
    except Exception as e:
        print(f"Error adding user: {e}")
        return (False, None, None)


def update_user_datasets(username, datasets):
    rm_local_tmp_index_html()
    userdetails = get_user_details(username)
    existing_datasets = userdetails['datasets']
    datasets_to_add = list()
    for d in datasets:
        if d not in existing_datasets:
            datasets_to_add.append(d)
    create_symlinks(username, datasets_to_add)
    download_index_file(username)
    homefile.indexfile_update(datasets_to_add)
    scp_local_index_file()
    mv_remote_index_file_to_home_dir(username)
    change_owner(username)


def rm_local_tmp_index_html():
    if os.path.exists('tmp/index.html'):
        os.remove('tmp/index.html')
        print('removed tmp/index.html')


def convert_date_format(date_str):
    formatted_date = datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")
    return formatted_date
