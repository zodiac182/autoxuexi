#! /usr/bin/env python
# encoding=utf8
import sqlite3
import os

def create_db():
    try:
        if not os.path.exists('data/'):
            os.mkdir('data/')

        conn = sqlite3.connect('data/xuexi.db')
        cursor = conn.cursor()

        cursor.execute('create table read_history(id varchar(20) primary key, type varchar(10))')
        return
    except Exception:
        return
    finally:
        cursor.close()
        conn.commit()
        conn.close()


def create_user():
    try:
        if not os.path.exists('data/'):
            os.mkdir('data/')

        conn = sqlite3.connect('data/xuexi.db')
        cursor = conn.cursor()

        cursor.execute('create table read_history(id varchar(20) primary key, type varchar(10))')
        return
    except Exception:
        return
    finally:
        cursor.close()
        conn.commit()
        conn.close()
        print('---')


if __name__ == '__main__':
    create_db()
