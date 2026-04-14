from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from database import init_db, hash_password, verify_password
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Initialize database
init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('selection'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('ewaste.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user[3]):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            flash('Login successful!', 'success')
            return redirect(url_for('selection'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('ewaste.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                         (name, email, hash_password(password)))
            conn.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            conn.close()
    
    return render_template('signup.html')

@app.route('/selection')
def selection():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('selection.html')

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        condition = request.form['condition']
        price = request.form['price'] if request.form['price'] else None
        
        item_type = 'donate' if not price else 'sell'
        
        conn = sqlite3.connect('ewaste.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO items (title, description, category, condition, price, type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, category, condition, price, item_type, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('sell'))
    
    return render_template('sell.html')

@app.route('/buy')
def buy():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('ewaste.db')
    cursor = conn.cursor()
    
    # Get sorting and filter params
    sort = request.args.get('sort', 'recent')
    filter_type = request.args.get('filter', 'all')
    
    query = 'SELECT * FROM items'
    params = []
    
    if filter_type != 'all':
        query += ' WHERE type = ?'
        params.append(filter_type)
    
    if sort == 'price_low':
        query += ' ORDER BY price ASC, created_at DESC'
    elif sort == 'price_high':
        query += ' ORDER BY price DESC, created_at DESC'
    elif sort == 'recent':
        query += ' ORDER BY created_at DESC'
    else:  # relevant
        query += ' ORDER BY created_at DESC'
    
    cursor.execute(query, params)
    items = cursor.fetchall()
    conn.close()
    
    return render_template('buy.html', items=items)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    conn = sqlite3.connect('ewaste.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM items 
        WHERE title LIKE ? OR description LIKE ? OR category LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    items = cursor.fetchall()
    conn.close()
    return jsonify(items)

if __name__ == '__main__':
    app.run(debug=True)