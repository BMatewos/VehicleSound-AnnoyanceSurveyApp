from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, Response
from flask_session import Session
from datetime import timedelta, datetime
import os, time
import csv
from io import StringIO

from user import user
from experiments import experiments
from media import media  
from questions import question
from responses import responses   


app = Flask(__name__)

print("Template folder:", app.template_folder)

app.config['SECRET_KEY'] = '5sdghsgRTg'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)

sess = Session()
sess.init_app(app)

@app.route('/')
def home():
    return redirect('/login')

@app.context_processor
def inject_user():
    return dict(me=session.get('user'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = user()
        if u.tryLogin(request.form.get('name'), request.form.get('password')):
            session['user'] = u.data[0]
            session['active'] = time.time()
            return redirect('/main')
        else:
            return render_template('login.html', title='Login', msg='Incorrect username or password.')
    else:
        m = session.pop('msg', 'Type your email and password to continue.')
        return render_template('login.html', title='Login', msg=m)

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html', title='Login', msg='You have logged out.')

@app.route('/main')
def main():
    if not checkSession():
        return redirect('/login')
    return render_template('main.html', title='Main menu')

@app.route('/users/manage', methods=['GET', 'POST'])
def manage_user():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')

    o = user()
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    if action == 'delete' and pkval:
        o.deleteById(pkval)
        return render_template('ok_dialog.html', msg="Deleted.")

    if action == 'insert':
        d = {
            'Fname': request.form.get('Fname'),
            'Lname': request.form.get('Lname'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'password2': request.form.get('password2'),
            'CreatedTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        o.set(d)
        default_dt = datetime.now().strftime('%Y-%m-%dT%H:%M')
        if o.verify_new():
            o.insert()
            return render_template('ok_dialog.html', msg="User added.")
        else:
            return render_template('users/add.html', obj=o, default_dt=default_dt)

    if action == 'update' and pkval:
        o.getById(pkval)
        o.data[0].update({
            'Fname': request.form.get('Fname'),
            'Lname': request.form.get('Lname'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'password2': request.form.get('password2'),
            'CreatedTime': request.form.get('CreatedTime')
        })
        if o.verify_update():
            o.update()
            return render_template('ok_dialog.html', msg="User updated.")
        else:
            return render_template('users/manage.html', obj=o)

    if pkval is None:
        o.getAll()
        return render_template('users/list.html', obj=o)
    elif pkval == 'new':
        o.createBlank()
        default_dt = datetime.now().strftime('%Y-%m-%dT%H:%M')
        return render_template('users/add.html', obj=o, default_dt=default_dt)
    else:
        o.getById(pkval)
        return render_template('users/manage.html', obj=o)

##############################################################################
##########################   Experiments
##############################################################################

from flask import Flask, render_template, request, redirect, session
from datetime import datetime
from experiments import experiments  # Make sure this import is there

@app.route('/experiments/manage', methods=['GET', 'POST'])
def manage_experiments():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')

    e = experiments()
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    # ----------------------------------
    # Create new experiment (empty form)
    # ----------------------------------
    if action == 'new':
        e.createBlank()
        return render_template('experiments/add.html', obj=e)

    # ----------------------------------
    # Delete experiment
    # ----------------------------------
    if action == 'delete' and pkval:
        e.deleteById(pkval)
        return render_template('ok_dialog.html', msg="Experiment deleted.")

    # ----------------------------------
    # Insert new experiment (after filling the add form)
    # ----------------------------------
    if action == 'insert':
        d = {
            'StartDate': request.form.get('StartDate'),
            'EndDate': request.form.get('EndDate'),
            'Description': request.form.get('Description'),
            'Creator_UserID': session['user']['UserID']
            # No need to manually set CreatedTime here! verify_new() does it.
        }

        e.set(d)
        if e.verify_new():
            e.insert()
            experiment_id = e.data[0].get(e.pk)

            if experiment_id:
                # Generate and store experiment code
                experiment_code = e.generate_experiment_code(experiment_id)
                e.data[0]['ExperimentCode'] = experiment_code
                e.update()

                # Redirect to add media for the new experiment
                return redirect(f'/media/manage?pkval=new&experiment_id={experiment_id}')
            else:
                return render_template('error_dialog.html', msg="Experiment ID not found after insert.")
        else:
            return render_template('experiments/add.html', obj=e)

    # ----------------------------------
    # Update existing experiment (after editing)
    # ----------------------------------
    if action == 'update' and pkval:
        e.getById(pkval)
        if e.data:
            d = {
                'ExperimentID': request.form.get('ExperimentID'),
                'StartDate': request.form.get('StartDate'),
                'EndDate': request.form.get('EndDate'),
                'Description': request.form.get('Description')
                # No need to manually set UpdatedDate here! verify_update() does it.
            }
            e.set(d)

            if e.verify_update():
                e.update()
                return render_template('ok_dialog.html', msg="Experiment updated successfully!")
            else:
                return render_template('experiments/manage.html', obj=e)
        else:
            return render_template('error_dialog.html', msg=f"Experiment with ID {pkval} was not found.")

    # ----------------------------------
    # List all experiments or load one for editing
    # ----------------------------------
    if pkval is None:
        e.getAll()
        return render_template('experiments/list.html', obj=e)
    else:
        e.getById(pkval)
        if e.data:
            return render_template('experiments/manage.html', obj=e)
        else:
            return render_template('error_dialog.html', msg=f"Experiment with ID {pkval} was not found.")




##############################################################################
##########################   Media
##############################################################################

from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

@app.route('/media/manage', methods=['GET', 'POST'])
def manage_media():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')

    m = media()
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    if action == 'delete' and pkval:
        m.deleteById(pkval)
        return render_template('ok_dialog.html', msg="Media deleted.")

    if action == 'insert':
        d = {
            'AutomobileType': request.form.get('AutomobileType'),
            'Duration': request.form.get('Duration'),
            'ExperimentID': request.form.get('ExperimentID'),
            'CreatedTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        file = request.files.get('file')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            d['FilePath'] = os.path.join('uploads', filename)
        else:
            d['FilePath'] = ''  # Or you can show an error

        m.set(d)
        if m.verify_new():
            m.insert()

            # 🧠 After inserting, get the new Media ID
            media_id = m.data[0][m.pk]
            experiment_id = d['ExperimentID']

            # 🚀 Redirect to add Question (with experiment_id and media_id)
            return redirect(f'/questions/manage?pkval=new&experiment_id={experiment_id}&media_id={media_id}')
        
        else:
            return render_template('media/add.html', obj=m)

    if action == 'update' and pkval:
        m.getById(pkval)
        if m.data:
            # Update existing fields
            m.data[0].update({
                'AutomobileType': request.form.get('AutomobileType'),
                'Duration': request.form.get('Duration'),
                'ExperimentID': request.form.get('ExperimentID')
            })

            file = request.files.get('file')
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                m.data[0]['FilePath'] = os.path.join('uploads', filename)

            if m.verify_update():
                m.update()
                return render_template('ok_dialog.html', msg="Media updated.")
            else:
                return render_template('media/manage.html', obj=m)
        else:
            return render_template('error_dialog.html', msg=f"Media with ID {pkval} was not found.")

    if pkval is None:
        m.getAll()
        return render_template('media/list.html', obj=m)

    elif pkval == 'new':
        m.createBlank()
        experiment_id = request.args.get('experiment_id')  # 🧠 Accept experiment_id from URL
        if experiment_id:
            m.data[0]['ExperimentID'] = experiment_id  # Pre-fill ExperimentID field
        return render_template('media/add.html', obj=m)

    else:
        m.getById(pkval)
        if m.data:
            return render_template('media/manage.html', obj=m)
        else:
            return render_template('error_dialog.html', msg=f"Media with ID {pkval} was not found.")






##############################################################################
##########################   Survey
##############################################################################
@app.route('/survey', methods=["GET", "POST"])
def survey():
    code = request.args.get('code')
    step = int(request.args.get("step", 0))

    # 🧠 New part: Get user_id from URL or generate if missing
    user_id = request.args.get('user_id')
    if not user_id:
        user_id = int(time.time() % 100000)  # Generate a temporary user id based on time

    if not code:
        return "Invalid survey link."

    # Load experiment
    e = experiments()
    e.getByField('ExperimentCode', code)
    if len(e.data) == 0:
        return "Experiment not found."
    experiment_data = e.data[0]
    experiment_id = experiment_data["ExperimentID"]

    # Get all media
    media_obj = media()
    media_obj.get_by_experiment(experiment_id)
    media_list = media_obj.data

    # Get all questions
    q = question()
    q.select_where("ExperimentID = %s", [experiment_id])
    q.load_choices()
    questions = q.data

    if request.method == "POST":
        current_media = media_list[step]
        media_id = current_media.get("MediaID")

        start_time_str = request.form.get("start_time")
        submitted_time = datetime.now()

        try:
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print("Error parsing start_time:", e)
            start_time = submitted_time

        duration_seconds = int((submitted_time - start_time).total_seconds())

        for ques in questions:
            ans = request.form.get(f"q_{ques['QuestionID']}")
            if ans:
                r = responses()
                r.data = []

                response_dict = {
                    "UserID": user_id,
                    "QuestionID": ques["QuestionID"],
                    "Answer": ans,
                    "ExperimentID": experiment_id,
                    "MediaID": media_id,
                    "Duration": duration_seconds,
                    "CreatedTime": submitted_time.strftime("%Y-%m-%d %H:%M:%S")
                }

                r.set(response_dict)
                if r.verify_new():
                    r.insert()

        step += 1

    if step >= len(media_list):
        return render_template("survey/thank_you.html")

    return render_template("survey/survey_step.html", 
                           experiment=experiment_data, 
                           media=media_list[step], 
                           questions=questions, 
                           step=step, 
                           code=code,
                           user_id=user_id,    # 🧠 Pass it here too!
                           datetime_now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))





##############################################################################
##########################   Questions
##############################################################################



@app.route('/questions/manage', methods=['GET', 'POST'])
def manage_questions():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')

    q = question()
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    # ----------------------------
    # Delete question
    # ----------------------------
    if action == 'delete' and pkval:
        q.deleteById(pkval)
        return render_template('ok_dialog.html', msg="Question deleted.")

    # ----------------------------
    # Insert new question
    # ----------------------------
    # ----------------------------

    if action == 'insert':
        d = {
            'QuestionText': request.form.get('QuestionText'),
            'QuestionType': request.form.get('QuestionType'),
            'Choices': request.form.get('Choices'),
            'ExperimentID': request.form.get('ExperimentID'),
            'MediaID': request.form.get('MediaID'),
            'CreatedTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        q.set(d)
        if q.verify_new():
            q.insert()

            experiment_id = d['ExperimentID']
            media_id = d['MediaID']

            # ✅ After adding a question, loop back to a fresh add form
            return redirect(f"/questions/manage?pkval=new&experiment_id={experiment_id}&media_id={media_id}")

        else:
            # If validation fails, stay on the same form
            return render_template('questions/add.html', obj=q)


    # ----------------------------
    # Update existing question
    # ----------------------------
    if action == 'update' and pkval:
        q.getById(pkval)
        if q.data:
            q.data[0].update({
                'QuestionText': request.form.get('QuestionText'),
                'QuestionType': request.form.get('QuestionType'),
                'Choices': request.form.get('Choices'),
                'ExperimentID': request.form.get('ExperimentID'),
                'MediaID': request.form.get('MediaID'),
            })

            if q.verify_update():
                q.update()
                return render_template('ok_dialog.html', msg="Question updated.")
            else:
                return render_template('questions/manage.html', obj=q)
        else:
            return render_template('error_dialog.html', msg=f"Question with ID {pkval} was not found.")

    # ----------------------------
    # View all questions
    # ----------------------------
    if pkval is None:
        q.getAll()
        return render_template('questions/list.html', obj=q)

    # ----------------------------
    # New question form (with pre-filled experiment/media IDs)
    # ----------------------------
    elif pkval == 'new':
        q.createBlank()
        experiment_id = request.args.get('experiment_id')
        media_id = request.args.get('media_id')

        if experiment_id:
            q.data[0]['ExperimentID'] = experiment_id
        if media_id:
            q.data[0]['MediaID'] = media_id

        return render_template('questions/add.html', obj=q)

    # ----------------------------
    # Edit specific question
    # ----------------------------
    else:
        q.getById(pkval)
        if q.data:
            return render_template('questions/manage.html', obj=q)
        else:
            return render_template('error_dialog.html', msg=f"Question with ID {pkval} was not found.")




##############################################################################
##########################   Responses
##############################################################################

@app.route('/responses/manage', methods=['GET', 'POST'])
def manage_responses():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')

    r = responses()
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    if action == 'delete' and pkval:
        r.deleteById(pkval)
        return render_template('ok_dialog.html', msg="Response deleted.")

    if action == 'insert':
        d = {
            'UserID': request.form.get('UserID'),
            'QuestionID': request.form.get('QuestionID'),
            'Answer': request.form.get('Answer'),
            'CreatedTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        r.set(d)
        if r.verify_new():
            r.insert()
            return render_template('ok_dialog.html', msg="Response added.")
        else:
            return render_template('responses/add.html', obj=r)

    if action == 'update' and pkval:
        r.getById(pkval)
        if r.data:
            r.data[0].update({
                'UserID': request.form.get('UserID'),
                'QuestionID': request.form.get('QuestionID'),
                'Answer': request.form.get('Answer')
            })
            if r.verify_update():
                r.update()
                return render_template('ok_dialog.html', msg="Response updated.")
            else:
                return render_template('responses/manage.html', obj=r)
        else:
            return render_template('error_dialog.html', msg=f"Response with ID {pkval} was not found.")

    if pkval is None:
        r.getAll()
        return render_template('responses/list.html', obj=r)
    elif pkval == 'new':
        r.createBlank()
        return render_template('responses/add.html', obj=r)
    else:
        r.getById(pkval)
        if r.data:
            return render_template('responses/manage.html', obj=r)
        else:
            return render_template('error_dialog.html', msg=f"Response with ID {pkval} was not found.")

##############################################################################
##########################   submit_survey
##############################################################################
        
        
@app.route('/survey_welcome')
def survey_welcome():
    code = request.args.get('code')
    return render_template('survey/survey_welcome.html', code=code)


@app.route('/submit_survey', methods=['POST'])
def submit_survey():
    r = responses()
    user_id = session.get("user", {}).get("UserID", "anonymous")
    submitted_time = datetime.now()

    # Get the survey start time from hidden field
    start_time_str = request.form.get("start_time")
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print("Error parsing start_time:", e)
        start_time = submitted_time

    # Calculate duration in seconds
    duration = (submitted_time - start_time).total_seconds()

    # Get experiment and media info from form
    experiment_id = request.form.get("experiment_id")
    media_id = request.form.get("media_id")
    audio_path = request.form.get("audio_path")

    for key in request.form.keys():
        if key.startswith('q_'):
            question_id = key.split("_")[1]
            answer = request.form.get(key)

            response_data = {
                'UserID': user_id,
                'QuestionID': question_id,
                'Answer': f"{answer} (Audio: {audio_path})",
                'ExperimentID': experiment_id,
                'MediaID': media_id,
                'Duration': int(round(duration)),

                'CreatedTime': submitted_time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Clean None fields
            response_data = {k: v for k, v in response_data.items() if v is not None}

            r.data = []
            r.set(response_data)

            print(">>> Inserting:", r.data[0])

            if r.verify_new():
                r.insert()

    return render_template("ok_dialog.html", msg="✅ Thank you! Your responses have been recorded.")



@app.route('/questions/finish')
def finish_questions():
    experiment_id = request.args.get('experiment_id')

    if not experiment_id:
        return render_template("error_dialog.html", msg="Experiment ID is missing.")

    # Generate experiment code
    exp = experiments()
    experiment_code = exp.generate_experiment_code(experiment_id)

    #  Removed total question count (to avoid AttributeError)

    return render_template("questions/added.html",
                           experiment_id=experiment_id,
                           experiment_code=experiment_code,
                           media_id=None)


####################################################################################################################
###########          Dashboard
####################################################################################################################

@app.route('/dashboard')
def dashboard():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')
    
    exp = experiments()
    ques = question()
    med = media()
    resp = responses()

    # Total counts
    exp.getAll()
    total_experiments = len(exp.data)

    ques.getAll()
    total_questions = len(ques.data)

    med.getAll()
    total_media = len(med.data)

    resp.getAll()
    total_responses = len(resp.data)

    # Top experiments
    sql = '''
        SELECT e.ExperimentCode, e.Description, COUNT(r.ResponseID) AS total_responses
        FROM mm_response r
        JOIN mm_experiment e ON r.ExperimentID = e.ExperimentID
        GROUP BY e.ExperimentCode, e.Description
        ORDER BY total_responses DESC
    '''
    exp.cur.execute(sql)
    top_experiments = exp.cur.fetchall()

    # Recent responses
    sql = '''
        SELECT e.ExperimentCode, q.QuestionText, r.Answer, r.Duration, r.CreatedTime
        FROM mm_response r
        JOIN mm_experiment e ON r.ExperimentID = e.ExperimentID
        JOIN mm_question q ON r.QuestionID = q.QuestionID
        ORDER BY r.CreatedTime DESC
        LIMIT 20
    '''
    resp.cur.execute(sql)
    recent_responses = resp.cur.fetchall()

    return render_template('dashboard.html', total_experiments=total_experiments, total_questions=total_questions,
        total_media=total_media, total_responses=total_responses, top_experiments=top_experiments,
        recent_responses=recent_responses)

@app.route('/download/top_experiments')
def download_top_experiments():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')
    
    exp = experiments()
    sql = '''
        SELECT e.ExperimentCode, COUNT(r.ResponseID) AS total_responses
        FROM mm_response r
        JOIN mm_experiment e ON r.ExperimentID = e.ExperimentID
        GROUP BY e.ExperimentCode
        ORDER BY total_responses DESC
    '''
    exp.cur.execute(sql)
    results = exp.cur.fetchall()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ExperimentCode', 'Total Responses']) 
    for row in results:
        writer.writerow([row['ExperimentCode'], row['total_responses']])

    output = si.getvalue()
    return Response(output,
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=top_experiments.csv"})

@app.route('/download/recent_responses')
def download_recent_responses():
    if not checkSession() or session['user']['role'] != 'admin':
        return redirect('/login')
    resp = responses()
    sql = '''
        SELECT e.ExperimentCode, q.QuestionText, r.Answer, r.Duration, r.CreatedTime
        FROM mm_response r
        JOIN mm_experiment e ON r.ExperimentID = e.ExperimentID
        JOIN mm_question q ON r.QuestionID = q.QuestionID
        ORDER BY r.CreatedTime DESC
        LIMIT 10
    '''
    resp.cur.execute(sql)
    recent_responses = resp.cur.fetchall()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ExperimentCode', 'QuestionText', 'Answer', 'Duration', 'CreatedTime'])
    for row in recent_responses:
        writer.writerow([
            row['ExperimentCode'],
            row['QuestionText'],
            row['Answer'],
            row['Duration'],
            row['CreatedTime']
        ])

    output = si.getvalue()
    return Response(output,
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=recent_responses.csv"})

##############################################################################################################################



@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

def checkSession():
    if 'active' in session:
        if time.time() - session['active'] > 500:
            session['msg'] = 'Your session has timed out.'
            return False
        else:
            session['active'] = time.time()
            return True
    return False

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
