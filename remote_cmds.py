from datetime import datetime
from dateutil.relativedelta import relativedelta

import os
import secrets
import index_file_service as homefile
import conf.app_config as app_config


ROOT_CMD = f"ssh -i {app_config.PEM_LOC} {app_config.SSH_USERNAME}@{app_config.REMOTE_HOST} "

def create_user(username, expiry):
    if expiry is None:
        expiry = get_next_month()
    cmd = 'sudo useradd %s -d %s/%s -e %s' % (username, app_config.HOME_DIRS, username, expiry)
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)


def change_user_pwd(username, password):
    cmd = '"sudo echo \"%s\" | sudo passwd %s --stdin"' % (password, username)
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)


def make_historical_dir(username):
    user_hist_subdir = get_user_hitorical_subdir_path(username)
    cmd = "sudo mkdir %s" % user_hist_subdir
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)


def insert_into_table(username, hash_pass, expiry):
    hash_pass = hash_pass.replace('$', '\\\\\\$')
    sql = """ "sudo sqlite3 %s \\"INSERT INTO %s (username,password,trial_start_date,trial_end_date) VALUES('%s', '%s', CURRENT_DATE, '%s')\\"  " """ % (app_config.SQLITE_AUTH_DB, app_config.SQLITE_TABLE, username, hash_pass, expiry)
    full_cmd = ROOT_CMD + sql
    print(full_cmd)
    os.system(full_cmd)


def update_table_password(username, hash_pass):
    hash_pass = hash_pass.replace('$', '\\\\\\$')
    sql = """ "sudo sqlite3 %s \\"UPDATE %s SET password = '%s' WHERE username='%s'\\"  " """ % (app_config.SQLITE_AUTH_DB, app_config.SQLITE_TABLE, hash_pass, username)
    full_cmd = ROOT_CMD + sql
    print(full_cmd)
    os.system(full_cmd)


def update_table_expiry(username, expiry):
    sql = """ "sudo sqlite3 %s \\"UPDATE %s SET trial_end_date = '%s' WHERE username='%s'\\"  " """ % (app_config.SQLITE_AUTH_DB, app_config.SQLITE_TABLE, expiry, username)
    full_cmd = ROOT_CMD + sql
    print(full_cmd)
    os.system(full_cmd)


def create_htaccess(username):
    hist_subdir_path = get_user_hitorical_subdir_path(username)
    cmd = '"sudo echo \'Require user %s\' | sudo tee %s/.htaccess > /dev/null"' % (username, hist_subdir_path)
    full_cmd = ROOT_CMD + cmd
    print(full_cmd)
    os.system(full_cmd)


def change_owner(username):
    # USE -h to affect only links not the referenced file
    cmd = "sudo  chown -h -R %s.%s %s/%s/." % (username, username, app_config.HOME_DIRS, username)
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)


def change_mod(username):
    cmd = "sudo chmod +x -R %s/%s" % (app_config.HOME_DIRS, username)
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)


def create_symlinks(username, datasets):
    datafiles = homefile.read_file_with_data_links()
    for dataset in datasets:
        d = datafiles[dataset][1]
        hist_subdir = get_user_hitorical_subdir_path(username)
        cmd = "sudo ln -s %s %s" % (d, hist_subdir)
        full_cmd = ROOT_CMD + cmd
        os.system(full_cmd)


def mv_remote_index_file_to_home_dir(username):
    hist_subdir = get_user_hitorical_subdir_path(username)
    cmd = f"sudo mv /home/{app_config.SSH_USERNAME}/index.html {hist_subdir}"
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)


def update_user_password(username, password=None):
    if password is None:
        password = generate_password()
    change_user_pwd(username, password)


def update_user_expiry(username, expiry=None):
    if expiry is None:
        expiry = get_next_month()
    cmd = '"sudo chage -E %s %s"' % (expiry, username)
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)


def generate_password(password_length=12):
    return secrets.token_urlsafe(password_length)


def get_next_month():
    date_after_month = datetime.today() + relativedelta(months=1)
    return date_after_month.strftime('%Y-%m-%d')


def get_encrypted_pass(password):
    hash_pass = os.popen('openssl passwd -apr1 "%s"' % password).read().strip()
    return hash_pass


def get_user_hitorical_subdir_path(username):
    subdir_name = "%s/%s/%s"  % (app_config.HOME_DIRS, username,  app_config.USER_HISTORICAL_DIR)
    return subdir_name


def scp_local_index_file():
    cmd = f"scp -p -i {app_config.PEM_LOC} tmp/index.html {app_config.SSH_USERNAME}@{app_config.REMOTE_HOST}:/home/{app_config.SSH_USERNAME}/index.html"
    err = os.system(cmd)
    if err:
        print(err)
        raise Exception(err)


def update_user_trial_end(username, expiry):
    update_user_expiry(username, expiry)
    update_table_expiry(username, expiry)


def reset_password(username, password=None):
    if password is None:
        password = generate_password()
    update_user_password(username, password)
    hashpass = get_encrypted_pass(password)
    update_table_password(username, hashpass)
    return (password, hashpass)


def download_index_file(username):
    cmd = "sudo cp %s/index.html tmp/" % get_user_hitorical_subdir_path(username)
    full_cmd = ROOT_CMD + cmd
    os.system(full_cmd)

    cmd = f"scp -i {app_config.PEM_LOC} {app_config.SSH_USERNAME}@{app_config.REMOTE_HOST}:/home/{app_config.SSH_USERNAME}/tmp/index.html tmp/"
    os.system(cmd)



