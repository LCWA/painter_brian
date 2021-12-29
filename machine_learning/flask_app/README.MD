
## How to start the application


    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    pip install Flask
    pip install tensorflow-gpu==1.14
    pip install requests
    pip install numpy
    pip install Pillow
    pip install gunicorn
    
    cd flask-app
    gunicorn -b '0.0.0.0:5000' --max-requests=20 --threads=4 wsgi:app

