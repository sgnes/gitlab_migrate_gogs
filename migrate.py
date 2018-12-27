import gogs_client
import gitlab
import os
import subprocess
import sys


gitlab_url, gitlab_token, gogs_url, gogs_token, default_user_password = sys.argv[1:]

gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
gl.auth()

token = gogs_client.Token(gogs_token)
api = gogs_client.GogsApi(gogs_url)

group_owner = {}
token_dict = {}

#create user
for user in gl.users.list(all=True):
    if not api.user_exists(user.username):
        api.create_user(token, user.name, user.username, user.email, default_user_password)
        if(user.is_admin == True):
            update = gogs_client.GogsUserUpdate.Builder(user.username,user.email).set_admin(True).build()
            api.update_user(token, user.username, update)
    auth = gogs_client.UsernamePassword(user.username, default_user_password)
    t1 = api.create_token(auth, "my_token", user.username)
    token_dict[user.username] = t1.token
    print("'{0}':'{1}',".format(user.username, t1.token))



# create groups
for grp in gl.groups.list(all=True):
    for user in grp.members.list(all=True):
        if user.access_level == 50:
            owner=user.username
    try:
        group_owner[grp.name] = owner
        org = api.create_organization(token, owner, grp.name, grp.full_name, grp.description)
        team = api.create_organization_team(token, grp.name, "Developer", permission="write")
        for user in grp.members.list(all=True):
            api.add_team_membership(token, team.id, user.username)
    except:
        print("organization already created.")



# create repository
for proj in gl.projects.list(all=True):
    org = proj.namespace["name"]
    proj_name = proj.name

    if org not in group_owner:
        t1 = gogs_client.Token(token_dict[org])
    else:
        t1 = gogs_client.Token(token_dict[group_owner[org]])
    if proj.visibility == "private":
        pri = True
    else:
        pri = False
    if org not in group_owner:
        if not api.repo_exists(token, org, proj_name):
            try:
                api.create_repo(t1, proj_name, private=pri, description=proj.description)
            except:
                print("repo exit")
    else:
        if not api.repo_exists(token, org, proj_name):
            try:
                api.create_repo(t1, proj_name, organization=org, private=pri, description=proj.description)
            except:
                print("repo exit")

local_git_dir = "D:\Temp\g3"

# migrate repository
# step1 clone all repository to local
with open("1.bat") as bat_file:
    for proj in gl.projects.list(all=True):
        org = proj.namespace["name"]
        url = proj.http_url_to_repo
        _, _, _, namespace, name = url.split("/")
        cmd_str = "git clone --mirror {0} {1}\r".format(url, os.path.join(local_git_dir, namespace, name, ".git"))
        #pid = subprocess.Popen([sys.executable, cmd_str], stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE)
        #os.system(cmd_str)
        bat_file.write(cmd_str)
        #git remote add origin http://SHA6-SV00010:3000/TCU_F8AT/TC277_QSPI_Demo.git
        #git push -u origin master
        bat_file.write("cd {0}\r".format(os.path.join(local_git_dir, namespace, name)))
        #os.system("git config --bool core.bare false")
        bat_file.write("git config --bool core.bare false\r")
        bat_file.write("git checkout master\r")
        #os.system("git checkout master")
        cmd1 = "git remote add gogs http://SHA6-SV00010:3000/{0}/{1}\r".format(namespace, name)
        #os.system(cmd1)
        bat_file.write(cmd1)
        bat_file.write("git push --all gogs\r")
        #os.system("git push --all gogs")
        pass





