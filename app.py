import requests
from flask import Flask,render_template,redirect,session,flash, request, url_for
from models import db, connect_db, User, City
from sqlalchemy.exc import IntegrityError


from forms import LoginForm, RegisterForm


app = Flask(__name__)
app.app_context().push()

app.config["SQLALCHEMY_DATABASE_URI"] = 'postgres://wuqvebps:tK2qW1Cak1hYWylT1PL_QXKcAAjeFz6s@bubble.db.elephantsql.com/wuqvebps'
app.config["SECRET_KEY"] = "mysecretkey"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/weather')
def get_weather():
    cities= City.query.all()

    weather_data = []

    for city in cities:
        
        response = get_weather_data(city.name)
        
        
        weather = {
            'id' : city.id,
            'city' : city.name,
            'temperature' : response['main']['temp'],
            'description' : response['weather'][0]['description'],
            'icon' : response['weather'][0]['icon'],
        }
        
        weather_data.append(weather)

    return render_template('weather.html', weather_data=weather_data)

@app.route('/weather', methods=["POST"])
def post_weather():
    new_city = request.form.get('city')

    err_msg = ''

    if new_city:
        old_city = City.query.filter_by(name=new_city).first()

        if not old_city:
            response = get_weather_data(new_city)
            if response['cod'] == 200:
                new_city_obj = City(name=new_city)

                db.session.add(new_city_obj)
                db.session.commit()
            else:
                err_msg = 'That city doesnt exist.'
        else: 
            err_msg = 'You entered a city that doesnt exist'

    if err_msg:
        flash(err_msg, 'error')
    else: 
        flash('City added', 'success')
        
    return redirect(url_for('get_weather'))

@app.route('/delete/<int:city_id>')
def delete_city(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()

    flash(f'Deleted { city.name }', 'success')
    return redirect(url_for('get_weather'))

def get_weather_data(city):

    url = f'http://api.openweathermap.org/data/2.5/weather?q={ city }&units=imperial&appid=e8be59ed5fc5ed481b05b11c923c5198'

    response = requests.get(url).json()

    return response
   

@app.route('/login', methods=["GET","POST"])
def login():
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session["user_id"] = user.id
            return redirect("/weather")
        else:
            form.username.errors = ["Invalid username/password"]

    return render_template("login.html", form=form)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        new_user = User.register(username, password)

        db.session.add(new_user)

        try:
            db.session.commit()
            session['user_id'] = new_user.id
            flash('Welcome! Successfully Created Your Account!', "success")
            return redirect('/login')
        except IntegrityError:
            db.session.rollback()
            form.username.errors.append('Username taken. Please choose another one.')

    return render_template('register.html', form=form)

     
    
@app.route("/logout", methods=["GET"])
def logout():

    # Logout route
    session.pop("user_id")
    flash("Goodbye", "info")
    return redirect("/login")