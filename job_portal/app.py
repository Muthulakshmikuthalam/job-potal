from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Job, Application
from config import Config
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# -------------------------------------------------
# Resume Upload Configuration
# -------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'resumes')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# -------------------------------------------------
# Initialize Database
# -------------------------------------------------
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------------------------
# Create Database + Default Admin
# -------------------------------------------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(email="admin@gmail.com").first():
        admin = User(
            name="Admin",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------
@app.route('/')
def home():
    return render_template("home.html")

# -------------------------------------------------
# AVAILABLE JOBS PAGE (Search + Filters)
# -------------------------------------------------
@app.route('/jobs')
def jobs():
    search = request.args.get("search")
    location = request.args.get("location")
    category = request.args.get("category")

    query = Job.query

    if search:
        query = query.filter(Job.title.contains(search))

    if location:
        query = query.filter(Job.location.contains(location))

    if category:
        query = query.filter(Job.category.contains(category))

    jobs = query.order_by(Job.date_posted.desc()).all()

    return render_template("jobs.html", jobs=jobs)

# -------------------------------------------------
# REGISTER
# -------------------------------------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        if User.query.filter_by(email=email).first():
            flash("Email already exists!")
            return redirect(url_for('register'))

        user = User(name=name, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        flash("Registered Successfully")
        return redirect(url_for('login'))

    return render_template('register.html')

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash("Invalid credentials")

    return render_template('login.html')

# -------------------------------------------------
# DASHBOARD (Role Based)
# -------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == "employer":
        jobs = Job.query.filter_by(employer_id=current_user.id).all()
        return render_template("employer_dashboard.html", jobs=jobs)

    elif current_user.role == "jobseeker":
        applications = Application.query.filter_by(user_id=current_user.id).all()
        return render_template("jobseeker_dashboard.html", applications=applications)

    elif current_user.role == "admin":
        users = User.query.all()
        jobs = Job.query.all()
        applications = Application.query.all()

        total_users = User.query.count()
        total_jobs = Job.query.count()
        total_applications = Application.query.count()

        return render_template("admin.html",
                               users=users,
                               jobs=jobs,
                               applications=applications,
                               total_users=total_users,
                               total_jobs=total_jobs,
                               total_applications=total_applications)

    return redirect(url_for('login'))






# -------------------------------------------------
# POST JOB
# -------------------------------------------------
@app.route('/post_job', methods=['GET','POST'])
@login_required
def post_job():

    if current_user.role != 'employer':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            description=request.form['description'],
            salary=request.form['salary'],
            location=request.form['location'],
            category=request.form['category'],
            employer_id=current_user.id,
            date_posted=datetime.utcnow()
        )

        db.session.add(job)
        db.session.commit()
        flash("Job Posted Successfully")

        return redirect(url_for('dashboard'))

    return render_template('post_job.html')

# -------------------------------------------------
# EDIT JOB
# -------------------------------------------------
@app.route('/edit_job/<int:id>', methods=['GET','POST'])
@login_required
def edit_job(id):

    job = Job.query.get_or_404(id)

    if current_user.id != job.employer_id:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.salary = request.form['salary']
        job.location = request.form['location']
        job.category = request.form['category']

        db.session.commit()
        flash("Job Updated Successfully")

        return redirect(url_for('dashboard'))

    return render_template('edit_job.html', job=job)

# -------------------------------------------------
# DELETE JOB
# -------------------------------------------------
@app.route('/delete_job/<int:id>')
@login_required
def delete_job(id):

    job = Job.query.get_or_404(id)

    if current_user.id != job.employer_id and current_user.role != "admin":
        return redirect(url_for('dashboard'))

    db.session.delete(job)
    db.session.commit()
    flash("Job Deleted Successfully")

    return redirect(url_for('dashboard'))

# -------------------------------------------------
# APPLY FOR JOB
# -------------------------------------------------
@app.route('/apply/<int:job_id>', methods=['GET','POST'])
@login_required
def apply(job_id):

    if current_user.role != 'jobseeker':
        flash("Only jobseekers can apply!")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        existing = Application.query.filter_by(
            user_id=current_user.id,
            job_id=job_id
        ).first()

        if existing:
            flash("Already Applied!")
            return redirect(url_for('dashboard'))

        file = request.files.get('resume')

        if not file or file.filename == "":
            flash("Please upload a resume")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        application = Application(
            user_id=current_user.id,
            job_id=job_id,
            resume=filename,
            date_applied=datetime.utcnow(),
            status="Pending"
        )

        db.session.add(application)
        db.session.commit()

        flash("Applied Successfully")

        return redirect(url_for('dashboard'))

    return render_template('apply.html', job_id=job_id)

# -------------------------------------------------
# VIEW APPLICATIONS (Employer)
# -------------------------------------------------
@app.route('/view_applications/<int:job_id>')
@login_required
def view_applications(job_id):

    if current_user.role != "employer":
        return redirect(url_for('dashboard'))

    applications = Application.query.filter_by(job_id=job_id).all()

    return render_template("view_applications.html",
                           applications=applications,
                           job_id=job_id)

# -------------------------------------------------
# UPDATE APPLICATION STATUS
# -------------------------------------------------
@app.route('/update_status/<int:app_id>/<string:status>')
@login_required
def update_status(app_id, status):

    application = Application.query.get_or_404(app_id)

    if current_user.role != "employer":
        flash("Access denied")
        return redirect(url_for('home'))

    application.status = status
    db.session.commit()

    flash("Application status updated")

    return redirect(url_for('dashboard'))

# -------------------------------------------------
# ADMIN PANEL
# -------------------------------------------------
@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash("Access Denied")
        return redirect(url_for('home'))

    users = User.query.all()
    jobs = Job.query.all()
    applications = Application.query.all()

    return render_template('admin.html',
                           users=users,
                           jobs=jobs,
                           applications=applications)

# -------------------------------------------------
# LOGOUT (FIXED)
# -------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
