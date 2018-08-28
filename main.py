import ets.ets_accredited_uc_file_lib as uc
import argparse
import logger_module
from ets.ets_mysql_lib import MysqlConnection as Mc, value_former, NULL
from os import remove
from os.path import normpath
from datetime import datetime
from config import *
from queries import *

PROGNAME = 'Crypto data to bd parser'
DESCRIPTION = '''Скрипт для импорта данных из xml файла со списком аккредитованных УЦ в БД'''
VERSION = '1.0'
AUTHOR = 'Belim S.'
RELEASE_DATE = '2018-07-31'

tmp_dir = normpath(tmp_dir)
accredited_uc_file = normpath(accredited_uc_file)
certificates_dir = normpath(certificates_dir)

d_minutes = 0


def show_version():
    print(PROGNAME, VERSION, '\n', DESCRIPTION, '\nAuthor:', AUTHOR, '\nRelease date:', RELEASE_DATE)


# обработчик параметров командной строки
def create_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('-v', '--version', action='store_true',
                        help="Показать версию программы")

    parser.add_argument('-u', '--update', action='store_true',
                        help='''Обновить записи в базе данных
                        Аргументы:
                        --force - обновить записи, даже если не обновлялся файл''')

    parser.add_argument('-f', '--force', action='store_true',
                        help='''Обновить записи, даже если не обновлялся файл''')

    parser.add_argument('-r', '--remove', action='store_true',
                        help='''Удалить неактивные записи из базы данных.
                        Аргументы:
                        --minutes - за указанное количество минут (по умолчанию 0, необязательный)''')

    parser.add_argument('-m', '--minutes', type=int, default=d_minutes,
                        help="Установить количество минут")

    return parser

cn = Mc(connection=Mc.MS_CERT_INFO_CONNECT)


def insert_worker(force=False):
    cn.connect()
    insert_datetime = datetime.now()

    f = uc.accredited_uc_file_get(filename=accredited_uc_file)
    uc_f = uc.AccreditedUcFile(f)
    new_file_version = uc_f.get_version()

    actual_file_version = cn.execute_query(get_actual_file_version_query)[0][0]
    actual_file_version = actual_file_version if actual_file_version else 0

    if actual_file_version >= new_file_version and not force:
        info = 'Данные актуальны. Версия файла не изменялась (%s)' % actual_file_version
        print(info)
        logger.info(info)
        cn.disconnect()
        return

    uc_p = uc_f.parse()

    cn.execute_query(update_set_not_active_query)

    for cert in uc_p:
        cert_location = cert.create_cer(dir=certificates_dir)
        cn.execute_query(insert_cert_info_query % (
            new_file_version,
            value_former(cert.subj_key_id) if cert.subj_key_id else NULL,
            value_former(cert.serial),
            value_former(cert.sha1hash),
            value_former(insert_datetime),
            value_former(cert.crl_url),
            value_former(cert_location)))

    cn.disconnect()
    info = 'Данные обновлены. Версия файла %s' % new_file_version
    print(info)
    logger.info(info)
    cn.disconnect()
    return


def delete_worker(minutes=d_minutes):
    cn.connect()
    locations_for_delete = cn.execute_query(get_locations_query % (minutes, minutes))

    for location in locations_for_delete:
        try:
            remove(location[0])
        except:
            pass

    cn.execute_query(delete_old_records_query % minutes)
    cn.disconnect()


# ОСНОВНОЙ КОД
if __name__ == '__main__':

    logger = logger_module.logger()
    try:
        # парсим аргументы командной строки
        my_parser = create_parser()
        namespace = my_parser.parse_args()

        if namespace.version:
            show_version()
            exit(0)

        if namespace.remove:
            delete_worker(minutes=namespace.minutes)
            info = 'Сведения старее %s минут удалены' % namespace.minutes
            print(info)
            logger.info(info)
            exit(0)

        if namespace.update:
            insert_worker(force=namespace.force)
            exit(0)

        show_version()
        print('For more information run use --help')

    # если при исполнении будут исключения - кратко выводим на терминал, остальное - в лог
    except Exception as e:
        logger.fatal('Fatal error! Exit', exc_info=True)
        print('Critical error: %s' % e)
        print('More information in log file')
        exit(1)

    exit(0)




