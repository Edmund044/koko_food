from flask import Flask, render_template, request

app = Flask(__name__)
from random import randint

@app.route("/input")
def hello():
    return render_template("index.html")

@app.route("/prediction", methods=['GET', 'POST'])
def submit():
    if request.method == "POST":
        income = int(request.form["income"])
        limit =  randint(0,20)/100 * income
        # if income > 1000 and income <= 5000:
        #     limit = 1000
        # elif income > 3000 and income <= 50000:
        #     limit = 2000  
        # else:
        #     limit = 0     
        return render_template("prediction.html", n = limit)
       


if __name__ == "__main__":
    app.run(debug=True)    
