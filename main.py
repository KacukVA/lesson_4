from flask import Flask, render_template
import sqlite3
import peewee


app = Flask(__name__)


@app.route('/', methods=['get', 'post'])
def main():
    pass


if __name__ == '__main__':
    app.run(debug=True)
