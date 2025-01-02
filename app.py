from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector as _mysql_connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = '5949'  # Change this to a random secret key

# Regular expressions for validating email and phone number
email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
phone_pattern = re.compile(r'^(0|91)?[789]\d{9}$')

# Step 1: Define your database credentials
DB_USERNAME = 'newuser'  # Replace with your actual DB username
DB_PASSWORD = 'root'      # Replace with your actual DB password
# Step 2: Define the function to connect to the database
def connect_to_database(username, password):
    try:
        con = _mysql_connector.connect(
            user=username,
            password=password,
            host='localhost',  # or the appropriate host
            database='employees'  # or your database name
        )
        print("Database connection established.")
        return con
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
# Global connection variable
con = None
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        global con
        username = request.form['username']
        password = request.form['password']
        # Connect to the database
        con = connect_to_database(DB_USERNAME, DB_PASSWORD)
        if con is None:
            flash('Database connection failed. Please check your credentials.')
            return redirect(url_for('index'))
        cursor = con.cursor()
        cursor.execute('SELECT id, password, role FROM users WHERE username = %s', (username,))
        user_record = cursor.fetchone()
        print(f"User  Record: {user_record}")  # Debugging output
        # Check if the user exists and the password matches
        if user_record and user_record[1] == password:  # Direct comparison for simplicity
            session['user_id'] = user_record[0]
            session['role'] = user_record[2]
            return redirect(url_for('menu'))
        else:
            print("Login failed for username:", username)  # Debugging output
            flash('Login failed. Please try again.')
            return redirect(url_for('index'))
    
    # Render the login page for GET requests
    return render_template('index.html')
    
@app.route('/menu')
def menu():
    return render_template('menu.html', role=session.get('role'))

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if session.get('role') != 'admin':  # Check if the user is not an admin
        flash('Access denied.')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        emp_name = request.form['emp_name']
        email_id = request.form['email_id']
        phone_no = request.form['phone_no']
        address = request.form['address']
        post = request.form['post']
        salary = request.form['salary']

        if not re.fullmatch(email_regex, email_id):
            flash('Invalid Email')
            return redirect(url_for('menu'))

        if not phone_pattern.match(phone_no):
            flash('Invalid Phone Number')
            return redirect(url_for('menu'))

        cursor = con.cursor()
        
        if check_employee(emp_id):
            flash('Employee ID Already Exists')
            return redirect(url_for('menu'))

        if check_employee_name(emp_name):
            flash('Employee Name Already Exists')
            return redirect(url_for('menu'))

        sql = 'INSERT INTO empdata (Id, Name, email_id, phone_no, Address, Post, Salary, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        data = (emp_id, emp_name, email_id, phone_no, address, post, salary, session['user_id'])  # Associate with logged-in user

        try:
            cursor.execute(sql, data)
            con.commit()
            flash('Successfully Added Employee Record')
        except Exception as e:
            con.rollback()
            flash(f'Error: {e}')

        return redirect(url_for('menu'))
    
    return render_template('add_employee.html')

@app.route('/display_employees')
def display_employees():
    cursor = con.cursor()
    if session.get('role') == 'admin':  # Admin can see all employees
        cursor.execute('SELECT * FROM empdata')
    else:  # Employees can only see their own info
        cursor.execute('SELECT * FROM empdata WHERE user_id = %s', (session['user_id'],))
    records = cursor.fetchall()
    return render_template('display_employees.html', records=records)
@app.route('/update_employee', methods=['GET', 'POST'])
def update_employee():
    if session.get('role') != 'admin':  # Check if the user is not an admin
        flash('Access denied.')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        email_id = request.form['email_id']
        phone_no = request.form['phone_no']
        address = request.form['address']

        if not check_employee(emp_id):
            flash('Employee Record Not Exists')
            return redirect(url_for('menu'))

        if not re.fullmatch(email_regex, email_id):
            flash('Invalid Email')
            return redirect(url_for('menu'))

        if not phone_pattern.match(phone_no):
            flash('Invalid Phone Number')
            return redirect(url_for('menu'))

        sql = 'UPDATE empdata SET email_id = %s, phone_no = %s, Address = %s WHERE Id = %s'
        data = (email_id, phone_no, address, emp_id)
        cursor = con.cursor()
        cursor.execute(sql, data)
        con.commit()
        flash('Updated Employee Record')
        return redirect(url_for('menu'))
    
    return render_template('update_employee.html')

@app.route('/promote_employee', methods=['GET', 'POST'])
def promote_employee():
    if session.get('role') != 'admin':  # Check if the user is not an admin
        flash('Access denied.')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        amount = request.form['amount']

        if not check_employee(emp_id):
            flash('Employee Record Not Exists')
            return redirect(url_for('menu'))

        cursor = con.cursor()
        sql = 'SELECT Salary FROM empdata WHERE Id=%s'
        cursor.execute(sql, (emp_id,))
        current_salary = cursor.fetchone()

        if current_salary is None:
            flash('Employee Record Not Exists')
            return redirect(url_for('menu'))

        new_salary = current_salary[0] + int(amount)

        sql = 'UPDATE empdata SET Salary = %s WHERE Id = %s'
        cursor.execute(sql, (new_salary, emp_id))
        con.commit()
        flash('Employee Promoted')
        return redirect(url_for('menu'))
    
    return render_template('promote_employee.html')

@app.route('/remove_employee', methods=['GET', 'POST'])
def remove_employee():
    if session.get('role') != 'admin':  # Check if the user is not an admin
        flash('Access denied.')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        emp_id = request.form['emp_id']

        # Check if the database connection is available
        if con is None:
            flash('Database connection is not available.')
            return redirect(url_for('menu'))

        # Check if the employee exists
        if not check_employee(emp_id):
            flash('Employee Record Not Exists')
            return redirect(url_for('menu'))

        cursor = con.cursor(dictionary=True)  # Use a cursor that returns dictionaries

        # Delete the employee from the database
        sql = 'DELETE FROM empdata WHERE Id = %s'
        cursor.execute(sql, (emp_id,))
        con.commit()

        # Reassign IDs to maintain sequential order
        cursor.execute('SELECT * FROM empdata ORDER BY Id')  # Make sure to order by ID
        employees = cursor.fetchall()

        # Reassign IDs
        for index, employee in enumerate(employees):
            new_id = index + 1
            update_sql = 'UPDATE empdata SET Id = %s WHERE Id = %s'
            cursor.execute(update_sql, (new_id, employee['Id']))  # Access by string key

        con.commit()

        flash('Employee Removed and IDs Reassigned')
        return redirect(url_for('menu'))

    return render_template('remove_employee.html')

@app.route('/search_employee', methods=['GET', 'POST'])
def search_employee():
    if request.method == 'POST':
        emp_id = request.form['emp_id']

        # Check if the employee exists
        if not check_employee(emp_id):
            flash('Employee Record Not Exists')
            return redirect(url_for('menu'))

        cursor = con.cursor()
        
        # Allow all users to search for any employee ID
        sql = 'SELECT * FROM empdata WHERE Id = %s'
        cursor.execute(sql, (emp_id,))
        
        record = cursor.fetchone()

        if record is None:
            flash('Employee Record Not Exists')
            return redirect(url_for('menu'))

        return render_template('search_employee.html', record=record)
    
    return render_template('search_employee.html')

#uncharter teretory 




@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if session.get('role') != 'admin':  # Only admins can manage attendance
        flash('Access denied.')
        return redirect(url_for('menu'))

    # Get today's date
    today = date.today()

    # Check if the database connection is available
    if con is None:
        flash("Database connection is not available!")
        return redirect(url_for('menu'))

    cursor = con.cursor()

    if request.method == 'POST':
        # Get list of employee IDs marked as present from the form
        employee_ids = request.form.getlist('attendance')

        # Delete today's attendance records before inserting new ones
        cursor.execute("DELETE FROM attendance WHERE date = %s", (today,))

        # Insert attendance for those present
        for employee_id in employee_ids:
            cursor.execute(
                "INSERT INTO attendance (employee_id, date, status) VALUES (%s, %s, %s)",
                (employee_id, today, 'Present')
            )

        # Fetch all employees from the database
        cursor.execute("SELECT Id FROM empdata")
        all_employees = cursor.fetchall()

        # Mark employees who are absent
        for employee in all_employees:
            if str(employee[0]) not in employee_ids:
                cursor.execute(
                    "INSERT INTO attendance (employee_id, date, status) VALUES (%s, %s, %s)",
                    (employee[0], today, 'Absent')
                )

        con.commit()
        flash('Attendance has been recorded successfully.')
        return redirect(url_for('menu'))

    # Fetch all employees to display in the attendance form
    cursor.execute("SELECT Id, Name FROM empdata")
    employees = cursor.fetchall()

    return render_template('attendance_form.html', employees=employees, today=today)


@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    if session.get('role') != 'admin':  # Only admins can view attendance
        flash('Access denied.')
        return redirect(url_for('menu'))

    # Check if the database connection is available
    if con is None:
        flash("Database connection is not available!")
        return redirect(url_for('menu'))

    cursor = con.cursor()

    if request.method == 'POST':
        # Get the selected date from the form
        selected_date = request.form.get('date')
        cursor.execute(
            """
            SELECT e.Name, a.status 
            FROM attendance a
            INNER JOIN empdata e ON a.employee_id = e.Id 
            WHERE a.date = %s
            """,
            (selected_date,)
        )
        records = cursor.fetchall()
        return render_template('view_attendance.html', records=records, selected_date=selected_date)

    # Default to displaying today's attendance
    today = date.today()
    cursor.execute(
        """
        SELECT e.Name, a.status 
        FROM attendance a
        INNER JOIN empdata e ON a.employee_id = e.Id 
        WHERE a.date = %s
        """,
        (today,)
    )
    records = cursor.fetchall()

    return render_template('view_attendance.html', records=records, selected_date=today)






def check_employee(emp_id):
    cursor = con.cursor()
    sql = 'SELECT * FROM empdata WHERE Id = %s'
    cursor.execute(sql, (emp_id,))
    record = cursor.fetchone()
    return record is not None

def check_employee_name(emp_name):
    cursor = con.cursor()
    sql = 'SELECT * FROM empdata WHERE Name = %s'
    cursor.execute(sql, (emp_name,))
    record = cursor.fetchone()
    return record is not None

if __name__ == "__main__":
    app.run(debug=True)