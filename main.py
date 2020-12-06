from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math
from datetime import datetime

with open("config.json","r") as c:          # config file og json like dictorary
    params = json.load(c)['params']

local_server = True
app = Flask(__name__)
app.secret_key = 'enurhferfjve biyrf hrfoe'
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']

    )

mail = Mail(app)

if local_server == True:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri'] 
db = SQLAlchemy(app)


class Contacts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    ''' 
    cno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone= db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Post(db.Model):               
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(21), nullable=False)
    img_file = db.Column(db.String(12), nullable=True)



@app.route("/")
def home():
    flash('Welcome the Conding Thunder Website !!',"success")
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    

    # Pagination 
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])] 
    if page==1:
        prev = "#"
        _next = "/?page="+ str(page+1)

    elif page==last:
        _next = "#"
        prev = "/?page="+ str(page - 1)
    else:
        _next = "/?page="+ str(page+1)
        prev = "/?page="+ str(page - 1)

    
    return render_template('index.html',params = params, posts=posts, prev=prev, next=_next)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)



@app.route("/about")
def about(): 
    return render_template('about.html',params = params)



@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ("user" in session) and (session['user'] == params['admin_user']):
        if request.method == 'POST':
            f = request.files['myfile']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "Upload File Successfully"


@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno): 

    if ("user" in session) and (session['user'] == params['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            tagline = request.form.get('tline')
            date = datetime.now()
            

            if sno =='0':
                post = Post(title=title, tagline=tagline, content=content,slug=slug, img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
                
            
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = title
                post.content = content
                post.slug = slug
                post.img_file = img_file
                post.tagline = tagline
                post.date = date
                db.session.commit()
                
                return redirect(f'/edit/{sno}')

        post = Post.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name') 
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone = phone, message = message, date= datetime.now(),email= email)  # giving to database
        db.session.add(entry)
        db.session.commit()

        mail.send_message('New message from ' + name,
                            sender=email,
                            recipients=[params['gmail_user']],
                            body=message+ "\n" + phone + "\n" + email
                        )

        flash('Thank for Your Contacting Us',"success")
    return render_template('contact.html',params = params)
 



@app.route('/login',  methods = ['GET', 'POST'])
def login():
    if ("user" in session) and (session['user'] == params['admin_user']):

        posts = Post.query.filter_by().all()
        return render_template('dashboard.html',params=params,posts=posts)


    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
       
        if (username == params['admin_user'])  and (password == params['admin_password']):
           
            session['user'] = username

            posts = Post.query.filter_by().all()

            return render_template('dashboard.html',params=params, posts=posts)


    return render_template('login.html',params = params)



@app.route('/logout')
def logout():
    flash('You have Successfully Logout',"success")
    session.pop("user")
    return redirect('/login')


@app.route("/delete/<string:sno>",methods=['POST','GET'])
def delete(sno):
    if ("user" in session) and (session['user'] == params['admin_user']):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    
    return redirect('/login')



if __name__ == "__main__":
    app.run(debug=True) 


