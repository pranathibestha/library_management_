from flask import Flask, render_template, request, redirect, session, url_for, flash
from datetime import datetime
from config import DATABASE_URI
from models import db, Book, Member, Issue, Admin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "supersecretkey"  # required for sessions

db.init_app(app)

with app.app_context():
    db.create_all()
    # Add default admin (only if not exists)
    if not Admin.query.first():
        admin = Admin(username="admin", password="admin123")  # simple password, can hash later
        db.session.add(admin)
        db.session.commit()
    # Preload books & members (if not exists)
    if not Book.query.first():
        db.session.add_all([
            Book(title="Python Basics", author="John Doe"),
            Book(title="Flask Web Dev", author="Miguel Grinberg"),
            Book(title="Data Science 101", author="Jane Smith")
        ])
        db.session.add_all([
            Member(name="Alice", email="alice@example.com", phone="1234567890"),
            Member(name="Bob", email="bob@example.com", phone="9876543210")
        ])
        db.session.commit()

# ----------------- AUTH DECORATOR -----------------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash("You need to login first", "danger")
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ----------------- ROUTES -----------------

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin'] = admin.username
            return redirect('/dashboard')
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Logged out successfully", "info")
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route('/add-book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        book = Book(title=request.form['title'], author=request.form['author'])
        db.session.add(book)
        db.session.commit()
        return redirect('/view-books')
    return render_template('add_book.html')

@app.route('/view-books')
@login_required
def view_books():
    books = Book.query.all()
    return render_template('view_books.html', books=books)

@app.route('/add-member', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        member = Member(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone']
        )
        db.session.add(member)
        db.session.commit()
        return redirect('/view-members')
    return render_template('add_member.html')

@app.route('/view-members')
@login_required
def view_members():
    members = Member.query.all()
    return render_template('view_members.html', members=members)

@app.route('/issue-book', methods=['GET', 'POST'])
@login_required
def issue_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        member_id = request.form['member_id']
        issue_date = datetime.now().strftime('%Y-%m-%d')
        book = Book.query.get(book_id)
        if book and book.status == "Available":
            book.status = "Issued"
            issue = Issue(book_id=book.id, member_id=member_id, issue_date=issue_date)
            db.session.add(issue)
            db.session.commit()
        return redirect('/view-issued')
    books = Book.query.filter_by(status="Available").all()
    members = Member.query.all()
    return render_template('issue_book.html', books=books, members=members)

@app.route('/view-issued')
@login_required
def view_issued():
    records = db.session.query(
        Issue.id, Book.title, Member.name, Issue.issue_date
    ).join(Book, Issue.book_id == Book.id).join(Member, Issue.member_id == Member.id).filter(Issue.return_date == None).all()
    return render_template('view_issued.html', records=records)

@app.route('/return-book/<int:id>')
@login_required
def return_book(id):
    issue = Issue.query.get(id)
    if issue:
        issue.return_date = datetime.now().strftime('%Y-%m-%d')
        book = Book.query.get(issue.book_id)
        book.status = "Available"
        db.session.commit()
    return redirect('/view-issued')

if __name__ == '__main__':
    app.run(debug=True)
