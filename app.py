from flask import Flask,render_template
import sqlite3
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index')
def home():
    return index()

@app.route('/movie')
def movie():
    datalist = []
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    data = cursor.execute('select * from top250')
    for row in data:
        datalist.append(row)
    cursor.close()
    conn.close()
    return render_template('movie.html',movies=datalist)

@app.route('/score')
def score():
    score =[]
    num =[]
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    data = cursor.execute("select score,count(score) from top250 group by score")
    for item in data:
        score.append(item[0])
        num.append(item[1])
    cursor.close()
    conn.close()
    return render_template('score.html',score=score,num=num)

@app.route('/word')
def word():
    return render_template('word.html')

@app.route('/team')
def team():
    return render_template('team.html')

if __name__ == '__main__':
    app.run()
