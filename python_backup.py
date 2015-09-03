#!/usr/bin/env python
# -*- coding: utf-8 -*-

from YaDiskClient import YaDisk
from ftplib import FTP
import os, time, sys, logging, ast, tarfile
from subprocess import Popen, PIPE, STDOUT
from contextlib import closing

UPLOADS_FILES = []

# Check config file
try:
    from config import main_config
except ImportError:
    print('File "./config.py" not found.')
    logging.error('File "./config.py" not found.')
    sys.exit()

DAYS_AGO = 3    # currently set to 3 days ago from when this script starts to run.

# Logs
dir_cur = os.path.abspath(os.path.dirname(__file__)) # current dir
dir_log = dir_cur + os.sep + 'dump.log' # dir for logs
logging.basicConfig(format='%(levelname)-4s [%(asctime)s] %(message)s', level=logging.DEBUG, filename=dir_log)

# Send pass from PATH
def send_pass(config):
    os.putenv('PGPASSWORD', config['postgre']['password'])

# Get x_days_ago
def x_days_ago(days):
    return time.time() - (60 * 60 * 24 * int(days))

# Delete old backup_database
# def del_old_backup(config):
#     # backup_dir, database_name, days_ago
#     try:
#         database_name = database_name.strip()
#         glob_list = glob.glob(backup_dir + database_name + '*' + '.pgdump')
#         for file in glob_list:
#             file_info = os.stat(file)
#             if file_info.st_ctime < days_ago:
#                 logging.info("Unlink: %s" % file)
#                 os.unlink(file)
#         logging.info("backup_database files older than %s deleted." % time.strftime('%c', time.gmtime(days_ago)))
#     except Exception as error:
#         print 'Delete backup_database error...' + '\n' + '{0}'.format(error)
#         logging.error('delete backup_database error...' + '{0}'.format(error))
#         sys.exit()

# Backup database
def backup_database(config):
    databases = config['backups_targets']['databases']
    for database in databases:
        print 'Backup start: ' + database
        try:
            logging.info('dump started for db: %s' % database)
            sql_backup_name = database + '_' + time.strftime('%Y%m%d%H%M') + '.backup'
            sql_backup_path = os.path.abspath(config['backups_dir'] + sql_backup_name)
            upload_file = sql_backup_path + '.gz'
            code = (
                config['postgre']['commands']['dump'] % (
                    config['postgre']['path'],
                    config['postgre']['host'],
                    config['postgre']['port'],
                    config['postgre']['user'],
                    database,
                    sql_backup_path,
                    )
                )
            logging.info("use command : %s" % code)
            print code
            # os.system(code)
            # proc = subprocess.check_output(code, shell=True) # for Python 2.7
            proc = Popen(code, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            output = proc.stdout.read()
            if output == "":
                UPLOADS_FILES.append(upload_file)
                print 'Backup database successful!'
                logging.info('dump database successful finished for db: %s' % database)
            else:
                print 'Dump database error: %s' % output
                logging.info('dump database error: %s' % output)
        except Exception as error:
            print 'Backup database error...' + '\n' + '{0}'.format(error)
            logging.error('dump database error...' + '{0}'.format(error))
            sys.exit()

# Backup files
def backup_files(config):
    for path in config['backups_targets']['dirs']:
        print('Backup directory: ' + path)
        logging.info('Backup directory: %s' % path)
        backup_name = config['backups_dir'] + os.path.basename(os.path.abspath(path)) + \
            '_' + time.strftime('%Y%m%d%H%M') + '.tar.bz2'
        try:
            # with tarfile.open(backup_name, "w:gz") as tar: # for Python 2.7
            with closing(tarfile.open(backup_name, "w:gz")) as tar:
                tar.add(
                    name=path,
                    arcname=os.path.abspath(path),
                    exclude=lambda file: file in config['backups_targets']['dirs_excludes']
                )
        except Exception as error:
            print 'Backup files error...' + '\n' + '{0}'.format(error)
            logging.error('backup files error...' + '{0}'.format(error))
            sys.exit()
        UPLOADS_FILES.append(backup_name)

# Upload to YaDisk
def upload_to_yadisk(uploads_files, config):
    if ast.literal_eval(config['yadisk']['on']):
        yd = YaDisk(config['yadisk']['user'],config['yadisk']['password'])
        try:
            yd.mkdir(config['yadisk']['directory'])
        except Exception as error:
            print '{0}'.format(error)
        for file in uploads_files:
            print 'Upload ' + file + ' to YaDisk'
            try:
                yd.upload(file, '%s/%s' % (
                            config['yadisk']['directory'], os.path.basename(os.path.abspath(file))))
                print 'Upload ' + file + ' successful!'
                logging.info('Upload ' + '{0}' + ' successful finished'.format(file))
            except Exception as error:
                print 'Upload error...' + '\n' + '{0}'.format(error)
                logging.error('upload to YaDisk error...' + '{0}'.format(error))
                sys.exit()

# Upload to FTP
def upload_fo_FTP(upload_files, config):
    if ast.literal_eval(config['ftp']['on']):
        print('Try connect to FTP...')
        logging.info('Try connect to FTP...')
        try:
            ftp = FTP()
            ftp.connect(config['ftp']['host'], 21)
            ftp.login(config['ftp']['user'], config['ftp']['password'])
            ftp.cwd(config['ftp']['dir_destination'])
        except Exception as error:
            print(type(error))
            print(error.args)
            print(error)
            logging.error('error FTP connect...' + '{0}'.format(error))
            ftp.quit()
            # if config['delete_files_after_uploading']:
            #     delete_files_after_uploading(upload_files)
        else:
            for file in upload_files:
                print('Upload file: ' + file)
                logging.info('Upload file: '.format(file))
                try:
                    ftp.storbinary('STOR ' + os.path.basename(os.path.abspath(file)), open(file, 'rb'))
                except Exception as error:
                    # if config['delete_files_after_uploading']:
                    #     delete_files_after_uploading([file])
                    print(type(error))
                    print(error.args)
                    print(error)
                    logging.error('error FTP upload...' + '{0}'.format(error))
                    break
                # else:
                #     ftp.storbinary('STOR ' + os.path.basename(os.path.abspath(file)), open(file, 'rb'))
                    # if config['delete_files_after_uploading']:
                    #     delete_files_after_uploading([file])
        ftp.quit()

def main(config):
    # Check backups_dir or create they
    config['backups_dir'] = os.path.abspath(config['backups_dir']) + os.sep
    if not os.path.exists(config['backups_dir']):
        print('Create folder ' + config['backups_dir'])
        try:
            os.mkdir(config['backups_dir'])
        except Exception as error:
            print 'Error create folder...' + '\n' + '{0}'.format(error)

    logging.info('*** START ***')
    send_pass(config)
    # del_old_backup(config)
    backup_database(config)
    backup_files(config)
    upload_to_yadisk(UPLOADS_FILES, config)
    upload_fo_FTP(UPLOADS_FILES, config)
    logging.info('*** FINISH ***')

if __name__ == '__main__':
    main(main_config)