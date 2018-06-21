## Install dependencies

Install core dependencies as follows. Make sure you have root permissions.

```sh
apt install python3-pip nginx sudo

pip3 install virtualenv
````

## Create new UNIX user

```sh
adduser user
```

## Install and create database

Setup PostgreSQL. Ensure you have root permissions.

```bash
# Install Postgres
apt install postgresql postgresql-contrib

# Configure database access for role user
sudo -i -u postgres
# Make sure you use the same name as the user account created above. (in our case "user")
createuser --interactive
createdb pservice

# Change password
su user
psql pservice
# Follow prompts to change password
psql$ \password
```

## Switch to user, configure

```sh
# Login as user
su user

# Create key for user, needed for pull access to data
ssh-keygen -b 4096
```

Assuming the key is placed in `~/.ssh/id_rsa`

Modify `~/.ssh/config` to include the following

```
Host gitlab.prae.me
        HostName gitlab.prae.me
        IdentityFile ~/.ssh/id_rsa
        User git
````

then install this key in Gogs to gain read-only access to the repository.
Afterwards, simply clone and setup the repo.

```sh
git clone git@gitlab.prae.me:apppets/PrivacyService.git
git checkout wsgi

# Setup virtualenv
virtualenv env
source env/bin/activate
# Install requirements
pip3 install -r requirements.txt

# Modify config.py as appropriate. Change DATABASE to PRODUCTION,
# modify the database definition. By default, you might use localhost
# for address and pservice for name.
vim config.py
```

## Systemd service configuration

Write the following service definition to `/etc/systemd/system/pservice.service`

```
[Unit]
Description=Gunicorn instance to serve pservice
After=network.target

[Service]
User=user
Group=www-data
WorkingDirectory=/home/user/PrivacyService
Environment="PATH=/home/user/PrivacyService/env/bin"
ExecStart=/home/user/PrivacyService/env/bin/gunicorn --workers 2 --bind unix:pservice.sock -m 007 pservice:app

[Install]
WantedBy=multi-user.target
```

Start and enable the service using

```sh
systemctl enable pservice
systemctl start pservice
```

## Configure nginx

Create a configuration file at `/etc/nginx/sites-available/pservice`

```
server {
    listen 443;
    server_name services.app-pets.org;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/user/PrivacyService/pservice.sock;
    }
}
```

Then enable the site as follows:

```sh
# Enable the site
ln -s /etc/nginx/sites-available/pservice /etc/nginx/sites-enabled
# Check configuration
nginx -t
# Restart service
systemctl restart nginx
```

## Enabling SSL support

To obtain a certificate:

```sh
sudo add-apt-repository ppa:certbot/certbot
sudo apt update
sudo apt install python-certbot-nginx

# Request certificate
sudo certbot --nginx -d services.app-pets.org
```

To renew the certificate automatically, add a cronjob that calls `certbot renew` automatically.