#!/usr/bin/env python3
"""
Sample Flask Application

This demonstrates a basic Flask web application with various features:
- Routes and URL patterns
- Templates
- Forms
- JSON API endpoints
- Error handling
- Static files
- Session management

Run with: python flask_app.py
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
from datetime import datetime
import json

# Create Flask application instance
app = Flask(__name__)

# Configure secret key for sessions (use environment variable in production)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Sample data (in a real app, this would come from a database)
users = [
    {"id": 1, "name": "John Doe", "email": "john@example.com", "role": "Admin"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "role": "User"},
    {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "role": "User"}
]

projects = [
    {"id": 1, "name": "Project Alpha", "status": "Active", "owner": "John Doe"},
    {"id": 2, "name": "Project Beta", "status": "Completed", "owner": "Jane Smith"},
    {"id": 3, "name": "Project Gamma", "status": "On Hold", "owner": "Bob Johnson"}
]

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html', 
                         title='Flask Sample App',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html', title='About')

@app.route('/users')
def list_users():
    """Display list of users"""
    return render_template('users.html', 
                         title='Users', 
                         users=users)

@app.route('/users/<int:user_id>')
def user_detail(user_id):
    """Display user details"""
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        return render_template('user_detail.html', 
                             title=f"User: {user['name']}", 
                             user=user)
    else:
        return render_template('404.html'), 404

@app.route('/projects')
def list_projects():
    """Display list of projects"""
    return render_template('projects.html', 
                         title='Projects', 
                         projects=projects)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # In a real app, you would save this to a database or send an email
        flash(f'Thank you {name}! Your message has been received.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', title='Contact Us')

@app.route('/search')
def search():
    """Search functionality"""
    query = request.args.get('q', '')
    results = []
    
    if query:
        # Search users and projects
        for user in users:
            if query.lower() in user['name'].lower() or query.lower() in user['email'].lower():
                results.append({
                    'type': 'user',
                    'title': user['name'],
                    'subtitle': user['email'],
                    'url': url_for('user_detail', user_id=user['id'])
                })
        
        for project in projects:
            if query.lower() in project['name'].lower():
                results.append({
                    'type': 'project',
                    'title': project['name'],
                    'subtitle': f"Status: {project['status']}",
                    'url': '#'
                })
    
    return render_template('search.html', 
                         title='Search Results', 
                         query=query, 
                         results=results)

# API Routes (JSON endpoints)
@app.route('/api/users')
def api_users():
    """API endpoint to get all users"""
    return jsonify({
        'status': 'success',
        'data': users,
        'count': len(users)
    })

@app.route('/api/users/<int:user_id>')
def api_user_detail(user_id):
    """API endpoint to get specific user"""
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        return jsonify({
            'status': 'success',
            'data': user
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404

@app.route('/api/projects')
def api_projects():
    """API endpoint to get all projects"""
    return jsonify({
        'status': 'success',
        'data': projects,
        'count': len(projects)
    })

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '')
    results = []
    
    if query:
        for user in users:
            if query.lower() in user['name'].lower():
                results.append({
                    'type': 'user',
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email']
                })
        
        for project in projects:
            if query.lower() in project['name'].lower():
                results.append({
                    'type': 'project',
                    'id': project['id'],
                    'name': project['name'],
                    'status': project['status']
                })
    
    return jsonify({
        'status': 'success',
        'query': query,
        'results': results,
        'count': len(results)
    })

@app.route('/session')
def session_demo():
    """Demonstrate session usage"""
    # Initialize visit count
    if 'visits' not in session:
        session['visits'] = 0
    
    session['visits'] += 1
    session['last_visit'] = datetime.now().isoformat()
    
    return render_template('session.html', 
                         title='Session Demo',
                         visits=session['visits'],
                         last_visit=session.get('last_visit'))

@app.route('/clear-session')
def clear_session():
    """Clear session data"""
    session.clear()
    flash('Session cleared!', 'info')
    return redirect(url_for('session_demo'))

# Error handlers
@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

# Template filters
@app.template_filter('datetime')
def datetime_filter(date_string):
    """Format datetime string"""
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return date_string

# Context processors (make data available to all templates)
@app.context_processor
def inject_globals():
    """Inject global variables into templates"""
    return {
        'app_name': 'Flask Sample App',
        'current_year': datetime.now().year,
        'user_count': len(users),
        'project_count': len(projects)
    }

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
        os.makedirs('static/css')
        os.makedirs('static/js')
    
    print("Starting Flask application...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint:20} {rule.rule}")
    
    # Run the application
    app.run(
        host='127.0.0.1',  # Listen on localhost
        port=5000,         # Port number
        debug=True,        # Enable debug mode (auto-reload on changes)
        threaded=True      # Handle multiple requests concurrently
    )
