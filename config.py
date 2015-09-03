#!/usr/bin/env python
# -*- coding: utf-8 -*-


# pip install requests
# yum -y install python-devel libffi-devel gcc
# pip install requests[security]
# pip install YaDiskClient

import sys

main_config = {
    # Folder for temporary storage of archives
    'backups_dir': sys.path[0] + '/backups/',

    # Config PostgreSQL
    'postgre': {
        'host': '127.0.0.1',
        'port':'5432',
        'user': 'postgres',
        'password': 'masterkey',
        'path': "c:\\program files\\postgresql\\9.4\\bin\\",    # for Windows
        # 'path': "/usr/bin/",    # for Linux
        # For Windows you must add gzip in PATH (in cmd: setx path "C:\Gzip\bin;%path%")
        'commands': {
            # Console command to dump the database
            'dump': """"%spg_dump" -h %s -p %s -O -F p -c -U %s %s | gzip -c > %s.gz """ # (path, host, port, user, base, archive_name)
            #'dump': """"%spg_dump" -h %s -p 5432 -U %s -C -F p -b -f %s %s """ # (path, host, user, archive_pach + archive_name, base)
        }
    },

    # Yandex Disk settings to upload files
    'yadisk':{
        'on': 'False', # True|False
        'user': '',
        'password': '',
        'directory': '/postgre_backup'
    },

    # FTP server to upload files
    'ftp': {
        'on': 'False', # True|False
        'host': '192.168.0.1',
        'port': 21,
        'user': '',
        'password': '',
        # Folder on the server where the files will be uploaded
        'dir_destination': 'backup_database'
    },

    # Targets backup_database
    'backups_targets': {
        # 'databases': [
        #   'test_db',
        #   'test_2',
        #   ...
        # ]
        'databases': ['crm', 'postgres', 'test'],

        # Databases excludes
        'databases_excludes': [],

        # Absolute path to the folder for backup_database
        # 'dirs': [
        #    '/var/www/site1.com',
        #    '/var/www/site2.com'
        # ],
        'dirs': [
            '/home/backup/backups'
        ],

        # Absolute paths folders excludes
        # 'dirs_excludes': [
        #    '/var/www/site1.com/logs',
        #    '/var/www/site1.com/data/cache/',
        #    '/var/www/site2.com/vendor/',
        #    '/var/www/site2.com/composer.lock',
        # ],
        'dirs_excludes': [
        ],
    }
}
