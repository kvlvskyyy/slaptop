from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    stickers = [
        {"name": "FeedPulse Warrior", "price": 0.99, "image": "images/feedpulse_warrior.jpg"},
    ]
    return render_template('index.html', stickers=stickers)

if __name__ == "__main__":
    app.run(debug=True)