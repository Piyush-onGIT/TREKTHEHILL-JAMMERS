# from email import message
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
# import csv
# from csv import writer
from datetime import date
import sqlite3                   #importing sqlite database

# Create your views here.


def index(request):
    return render(request, 'index.html')


def teacher(request):
    if request.user.is_anonymous:
        return render(request, 'teacher_signin.html')
    return render(request, 'teacher.html')


def student(request):
    return render(request, 'student.html')


def sets(request):
    return render(request, 'set.html')


def check(request):
    return render(request, 'check.html')


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


'''# ================== creating a student login function ======================

def login_student(request):
    if request.method == 'POST':                   
        user = request.POST.get('username')        # storing the value of username in username variable
        passw = request.POST.get('password')       # storing value of the password in the password variable
        
    # ============ authentication =================
        user = authenticate(username = user, password = passw)           # creating instance for aunthentication from models 
        if user is not None :                                            # checking if user is not none 
            login(request, user)                                         # calling login function by passing request and the instance of authentication
            return render(request, "student.html")                       # redirecting to the student webpage on succesful authentication
        else:                                                            
            return render(request, "index.html")                         #returning to homepage 

    return render(request, "index.html")'''


# ==================== creating Teacher login function =========================
def login_teacher(request):
    if request.method == 'POST':
        user = request.POST.get('username')        # Getting the username 
        passw = request.POST.get('password')       # Geeting password 

        # ======== authentication ===========

        user = authenticate(username=user, password=passw)
        if user is not None:

            return render(request, "teacher.html")

        else:
            messages.error(request, "Please check your username or password , contact admin if problem persists")   # returning a message on invalid input
    
    else:
        messages.error(request, "")           
    return render(request, "teacher_signin.html")    # returning to login page if method is not post

# ========================= function for making exam paper =====================

def makePaper(request):                            
    data = request.GET
    subCode = data['code'].upper()
    sem = data['sem'].upper()
    sec = data['sec'].upper()
    link = data['link']

    splits = link.split("/")

    today = date.today()
    d1 = today.strftime("%d%m%Y")
    # today's data + subject code + semester + section
    paperCode = d1 + subCode + sem + sec

    sqliteConnection = sqlite3.connect('papers.sqlite3')
    cursor = sqliteConnection.cursor()

    sqlite_insert_query = """INSERT INTO papers
                          (code, link) 
                           VALUES 
                          (?,?)"""
    data_tuple = (paperCode, splits[6])

    try:
        cursor.execute(sqlite_insert_query, data_tuple)
    except:
        cursor.close()
        # this paper has been submitted before
        return render(request, 'teacher.html', {'code': 3})
    sqliteConnection.commit()
    cursor.close()

    return render(request, 'teacher.html', {'code': paperCode})


def logout(request):
    data = request.POST
    print(data)
    roll = data['roll']
    code = data['code']

    # check for any session
    conn0 = sqlite3.connect("sessions.sqlite3")
    cur0 = conn0.cursor()
    cur0.execute("SELECT * FROM sessions")

    sessions = cur0.fetchall()       # list of tuples
    for i in sessions:
        if str(i[1]) == roll:
            if str(i[2]) == code:
                if str(i[3]) == "0":
                    # already logged out
                    return render(request, 'student.html', {'code': 4})
                else:
                    query = """UPDATE sessions set online = 0 where roll = ? and code = ?"""
                    cur0.execute(query, (roll, code))
                    conn0.commit()
                    cur0.close()
                    # logged out successfully
                    return render(request, 'student.html', {'code': 5})

    return render(request, 'student.html', {'code': 4})


def startTest(request):
    data = request.POST
    code = data['code']             # paper code
    roll = data['roll']             # roll number
    
    conn = sqlite3.connect("submissions.sqlite3")      # Setting up sqlite connection 
    cur = conn.cursor()                                # creating a cursor for sqlite
    cur.execute("SELECT * FROM submissions")

    rows = cur.fetchall()           # list of tuples

    conn1 = sqlite3.connect("papers.sqlite3")
    cur1 = conn1.cursor()
    cur1.execute("SELECT * FROM papers")

    rows1 = cur1.fetchall()           # list of tuples

    # check if the student has entered the correct paper code or not
    codeFlag = 0
    for i in rows1:
        if str(i[1]) != code:
            codeFlag = 1
        else:
            codeFlag = 0
            break

    if codeFlag == 1 or len(rows1) == 0:
        # invalid paper code
        return render(request, 'student.html', {"code": 3})

    # check for online session
    conn0 = sqlite3.connect("sessions.sqlite3")
    cur0 = conn0.cursor()
    cur0.execute("SELECT * FROM sessions")

    sessions = cur0.fetchall()       # list of tuples
    for i in sessions:
        if str(i[1]) == roll:
            if str(i[2]) == code:
                if str(i[3]) == "1":
                    # multiple session found
                    return render(request, 'student.html', {'code': 2})
                else:
                    break

    # control comes here this means multiple sessions not found

    link = ''
    for i in rows1:
        if str(i[1]) == code:
            link = i[2]

    # check if the student has appeared for the paper
    flag = 0
    for i in rows:
        if str(i[1]) == roll:
            if str(i[2]) == code:
                if str(i[3]) == '1':
                    # paper submitted by this roll number
                    flag = 1
                    break
                else:
                    flag = 0
                    break

    if (flag == 1):
        # paper submitted
        return render(request, 'test.html', {'code': 1, 'roll': data['roll'], 'paperCode': code})
    else:
        # paper not submitted
        # so set this session online
        query = """INSERT INTO sessions
                (roll, code, online)
                VALUES
                (?,?,?)"""

        for i in sessions:
            if str(i[1]) == roll:
                if str(i[2]) == code:
                    query = """UPDATE sessions set online = 1 where roll = ? and code = ?"""
                    cur0.execute(query, (roll, code))
                    conn0.commit()
                    cur0.close()
                    break
        else:
            data_tuple = (roll, code, 1)
            cur0.execute(query, data_tuple)
            conn0.commit()
            cur0.close()
        return render(request, 'test.html', {'code': code, 'roll': data['roll'], 'paperCode': link})


def submitted(request, roll, code):
    url = (request.path).split("/")
    roll = int(url[2])

    conn0 = sqlite3.connect("sessions.sqlite3")
    cur0 = conn0.cursor()
    query = """UPDATE sessions set online = 0 where roll = ? and code = ?"""
    cur0.execute(query, (roll, code))
    conn0.commit()
    cur0.close()

    sqliteConnection = sqlite3.connect('submissions.sqlite3')
    cursor = sqliteConnection.cursor()

    cursor.execute("SELECT * FROM submissions")
    rows = cursor.fetchall()

    for i in rows:
        if str(i[1]) == str(roll) and str(i[2]) == str(code):
            return render(request, 'test.html', {'code': 1})

    sqlite_insert_query = """INSERT INTO submissions
                          (roll, code, submit) 
                           VALUES 
                          (?,?,?)"""
    data_tuple = (roll, code, 1)
    cursor.execute(sqlite_insert_query, data_tuple)
    sqliteConnection.commit()
    cursor.close()

    return render(request, 'test.html', {'code': 1})
