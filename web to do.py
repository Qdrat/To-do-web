# Flask Task Manager with SQLAlchemy, HTML/CSS

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    tasks = db.relationship('Task', backref='category', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(10), nullable=False, default='Medium')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    completed = db.Column(db.Boolean, default=False)


# Home page: list, search, filter, add
@app.route('/', methods=['GET', 'POST'])
def index():
    # Add new task
    if request.method == 'POST' and 'add_task' in request.form:
        title = request.form['title']
        description = request.form.get('description')
        priority = request.form.get('priority', 'Medium')
        category_id = request.form.get('category_id')
        if category_id == 'None':
            category_id = None
        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            category_id=category_id if category_id else None
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))

    # Filters
    search = request.args.get('search', '')
    filter_category = request.args.get('category', '')
    filter_priority = request.args.get('priority', '')
    show_completed = request.args.get('show_completed', 'all')

    query = Task.query
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))
    if filter_category:
        query = query.filter(Task.category_id == int(filter_category))
    if filter_priority:
        query = query.filter(Task.priority == filter_priority)
    if show_completed == 'completed':
        query = query.filter(Task.completed == True)
    elif show_completed == 'active':
        query = query.filter(Task.completed == False)
    tasks = query.order_by(Task.id.desc()).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template('task.html',
        tasks=tasks, categories=categories
    )
# base_template + """
#         {% block content %}
#         <h1>Task Manager</h1>
#         <form class="filter-form" method="get">
#             <input type="text" name="search" placeholder="Search..." value="{{ request.args.get('search', '') }}">
#             <select name="category">
#                 <option value="">All Categories</option>
#                 {% for cat in categories %}
#                     <option value="{{ cat.id }}" {% if request.args.get('category', type=int) == cat.id %}selected{% endif %}>{{ cat.name }}</option>
#                 {% endfor %}
#             </select>
#             <select name="priority">
#                 <option value="">All Priorities</option>
#                 {% for p in ['High','Medium','Low'] %}
#                     <option value="{{p}}" {% if request.args.get('priority') == p %}selected{% endif %}>{{p}}</option>
#                 {% endfor %}
#             </select>
#             <select name="show_completed">
#                 <option value="all" {% if request.args.get('show_completed','all')=='all' %}selected{% endif %}>All</option>
#                 <option value="active" {% if request.args.get('show_completed')=='active' %}selected{% endif %}>Active</option>
#                 <option value="completed" {% if request.args.get('show_completed')=='completed' %}selected{% endif %}>Completed</option>
#             </select>
#             <button type="submit">Filter</button>
#             <a href="{{ url_for('index') }}">Reset</a>
#         </form>
#         <form class="add-form" method="post">
#             <input type="hidden" name="add_task" value="1">
#             <input type="text" name="title" placeholder="New Task Title" required>
#             <select name="priority">
#                 {% for p in ['High','Medium','Low'] %}
#                     <option value="{{p}}">{{p}}</option>
#                 {% endfor %}
#             </select>
#             <select name="category_id">
#                 <option value="None">No Category</option>
#                 {% for cat in categories %}
#                     <option value="{{cat.id}}">{{cat.name}}</option>
#                 {% endfor %}
#             </select>
#             <input type="text" name="description" placeholder="Description">
#             <button type="submit">Add Task</button>
#         </form>
#         <a href="{{ url_for('categories') }}">Manage Categories</a>
#         <hr>
#         {% for task in tasks %}
#             <div class="task {% if task.completed %}completed{% endif %}">
#                 <span class="priority-{{task.priority}}">[{{task.priority}}]</span>
#                 <strong>{{task.title}}</strong>
#                 {% if task.category %}<span class="category">({{task.category.name}})</span>{% endif %}
#                 <div>{{task.description}}</div>
#                 <div class="actions">
#                     <a href="{{ url_for('edit_task', task_id=task.id) }}">Edit</a> |
#                     <form action="{{ url_for('delete_task', task_id=task.id) }}" method="post" style="display:inline;">
#                         <button type="submit" onclick="return confirm('Delete this task?')">Delete</button>
#                     </form> |
#                     <form action="{{ url_for('toggle_complete', task_id=task.id) }}" method="post" style="display:inline;">
#                         <button type="submit">{% if task.completed %}Mark Active{% else %}Mark Completed{% endif %}</button>
#                     </form>
#                 </div>
#             </div>
#         {% else %}
#             <p>No tasks found.</p>
#         {% endfor %}
#         {% endblock %}
#         """,
# Edit Task
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description')
        task.priority = request.form.get('priority', 'Medium')
        category_id = request.form.get('category_id')
        if category_id == 'None':
            task.category_id = None
        else:
            task.category_id = int(category_id)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template(
        'task_edit.html',
        task=task, categories=categories
    )

# Delete Task
@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

# Toggle Complete
@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_complete(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('ta'))

# Category management
@app.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name and not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
            db.session.commit()
        return redirect(url_for('categories'))
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        'categories.html',
        categories=categories
    )

@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    # Set category_id of tasks to None before deleting category
    for task in category.tasks:
        task.category_id = None
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('categories'))

# Initialize DB
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
