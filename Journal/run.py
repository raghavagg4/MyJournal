from flask_app import create_app

app = create_app()

# This is needed for Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True)
