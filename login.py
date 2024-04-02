from flask import Flask, flash, request, render_template, url_for, redirect, session
import bcrypt
import cv2
import numpy as np
from io import BytesIO
import requests
import os
import base64
import moviepy.editor as mpy
import imageio

app = Flask(__name__,static_folder='./static')
app.secret_key = 'secret_key'
import pymysql
db = pymysql.connect(
    host='localhost',
    user='arman-03',
    password='Arman@14'
)
cur = db.cursor()
sql_D="create database if not exists `picsysnap`"
cur.execute(sql_D)
db.commit()
cur.close()
db.close()
conn = pymysql.connect(
    host='localhost',
    user='arman-03',
    password='Arman@14',
    database='picsysnap'  
)
pt= conn.cursor()

SCREEN_SIZE = (1980,1080)
def clipGenerator(base64_string,SCREEN_SIZE,clip_duration):
    if base64_string.find(';base64,'):
        find_idx = base64_string.find(';base64,')
        base64_string = base64_string[find_idx+8:]
    imgdata = base64.b64decode(base64_string)
    img = imageio.imread(imgdata)#path
    image = mpy.ImageClip(img).\
        set_position(('center', 'center')).\
        resize(width=SCREEN_SIZE[1])
    clip = mpy.CompositeVideoClip([image], size=SCREEN_SIZE).set_duration(clip_duration)
    return clip

def VideoCreator(audio,VDLINKS):
    input_data=VDLINKS.split("$")
    input_data.pop()
    audio_path = f"static/audio/{audio}"
    print(audio_path)
    clips=list()
    for item in input_data:
        base64_string = item
        #transition_option = item[1]
        clip_duration = 3;
        # print(base64_string)
        pureClip = clipGenerator(base64_string,SCREEN_SIZE,clip_duration)
        #modifiedClip = transitions(pureClip,transition_option,Duration,clip_duration)
        clips.append(pureClip)
    finalclip = mpy.concatenate_videoclips(clips)
    audio_clip = mpy.AudioFileClip(audio_path)
    video_duration = 3*len(input_data)
    
    # Calculate how many times to repeat the audio
    audio_duration = audio_clip.duration

    repeat_count = max(1, video_duration / audio_duration)
    if type(repeat_count) is not int:
        repeat_count = int(repeat_count)+1
    repeated_audio_clip = mpy.concatenate_audioclips([audio_clip] * repeat_count)
    
    # Trim audio to match video duration
    repeated_audio_clip = repeated_audio_clip.subclip(0, video_duration)
    
    # Set audio for the final clip
    finalclip = finalclip.set_audio(repeated_audio_clip)
    
    # Write video file
    finalclip.write_videofile("static/images/video.mp4", fps=10)
    
    return True


def TableCheck(tbl_name):
    sql_comand=f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema ='picsysnap' AND table_name = '{tbl_name}'"
    pt.execute(sql_comand)
    tbl_check=pt.fetchall()[0][0]
    return tbl_check
tbl=['User','photos']
if TableCheck(tbl[0])==0:
    sql_cmd=f"create table {tbl[0]}( id int NOT NULL AUTO_INCREMENT,name varchar(40) NOT NULL, email varchar(255) UNIQUE,password varchar(255),PRIMARY KEY (id))"
    pt.execute(sql_cmd)
    conn.commit()
if TableCheck(tbl[1])==0:
    sql_cmd=f"create table {tbl[1]}( id int NOT NULL AUTO_INCREMENT,username varchar(40),photo_name varchar(255),photo LONGBLOB,photo_dimensions VARCHAR(255),PRIMARY KEY (id))"
    pt.execute(sql_cmd)
    conn.commit()
class User:
    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
@app.route('/dashboard')
def dashboard():
    if 'mail' in session:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM User WHERE email = %s', (session['mail'],))
            data = cursor.fetchone()
            user = User(data[2],data[3],data[1])
            return render_template('dashboard.html', user=user)
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        with conn.cursor() as cursor:
            # Check if user with the same email exists
            cursor.execute('SELECT * FROM User WHERE email = %s', (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('A user with this email already exists. Please log in or use a different email.')
                return redirect(url_for('register'))
            else:
                # Create new user
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute('INSERT INTO User (name, email, password) VALUES (%s, %s, %s)', (name, email, hashed_password))
                conn.commit()
                session['mail'] = email
                return redirect(url_for('dashboard'))
    return render_template('login.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'mail' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('Email')
        password = request.form.get('Password')
        with conn.cursor() as cursor:
            # Check if user exists and verify password
            cursor.execute(f"SELECT * FROM User WHERE email = '{email}'")
            user = cursor.fetchone()
            if user :
                if not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                    flash('Invalid email or password. Please try again.')
                    return redirect(url_for('login'))
                else :# Set session
                    session['mail'] = email
                    return redirect(url_for('dashboard'))
            else :
                flash('User not found!. please register')
                return redirect(url_for('login'))
            
    return render_template('login.html')
@app.route('/home')
@app.route('/')
def index():
    user_logged_in = 'mail' in session
    return render_template('home.html', user_logged_in=user_logged_in)

@app.route('/imageUpload',methods=['GET','POST'])
def image():
    if request.method == "POST":
        links = None
        data = request.form.get('data')
        if data!=None :
            links = data.split("$")
            links.pop()
            Username = session['mail']
            photo_name ="default"
            photo_dimensions = "default"
            for i in links:
                STR =f"INSERT INTO photos(username,photo_name,photo,photo_dimensions) VALUES('{Username}','{photo_name}','{i}','{photo_dimensions}')"
                pt.execute(STR)
                conn.commit()
            return redirect(url_for("display"))
    return render_template('image.htm')



@app.route('/display',methods=['GET','POST'])
def display():
    link = ""  
    if request.method=="GET":
        username=session['mail']
        if username !="":
            STR =f"SELECT photo FROM `photos` WHERE username ='{username}'"
            pt.execute(STR)
            data = pt.fetchall()
            for i in data:
                link+=i[0].decode("utf-8")+"$"
        else:
            #session doesn't exist
            pass
        return render_template('display.html',link=link)
    if request.method=="POST":
        ID = request.form.get('data')
        audio ,imagelinks = ID.split("$")[0],ID.split("$")[1:]
        print(audio)
        # imagelinks = imagelinks.split("$").pop()
        imagelinks = "$".join(imagelinks)
        completed = VideoCreator(audio,imagelinks)
        # imagelinks = imagelinks.split("$")
        # for i in imagelinks:
        #     print(i[:30])
        if completed:
            return redirect(url_for('video')) 

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/logout')
def logout():
    session.pop('mail', None)
    return redirect('/login')
    
if __name__ == '__main__':
    app.run(debug=True)