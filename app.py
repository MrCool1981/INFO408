from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from dotenv import load_dotenv
from funcs import * # import the function from the package
import azure.cosmos.cosmos_client as cosmos_client
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

app = Flask(__name__)

####################### SET UP ENVIRONMENT #######################
load_dotenv()

app.secret_key = os.environ.get("APP_SECRET_KEY")

# get CosmosDB settings
HOST = f'https://{os.environ.get("COSMOSDB_HOST")}.documents.azure.com:443/'
MASTER_KEY = os.environ.get("COSMOSDB_KEY") # Master Key for CosmosDB
DATABASE_ID = os.environ.get("COSMOSDB_DATABASE_ID") # CosmosDB database
CONTAINER_ID_METABOLITES = os.environ.get("COSMOSDB_METABOLITES_CONTAINER_ID") # CosmosDB container for file records
CONTAINER_ID_METADATA = os.environ.get("COSMOSDB_METADATA_CONTAINER_ID") # CosmosDB container for metadata records
CONTAINER_ID_USERS = os.environ.get("COSMOSDB_USERS_CONTAINER_ID") # CosmosDB container for user records
cosmosdb_client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="INFO408", user_agent_overwrite=True)
database, container_metabolites, container_users = set_up_database(cosmosdb_client, DATABASE_ID, CONTAINER_ID_METABOLITES, CONTAINER_ID_USERS)

###################### LOGIN FUNCTIONS #########################
login_manager = LoginManager()  
login_manager.init_app(app)  
login_manager.login_message = "Please log in to access this page."  
login_manager.login_view = 'login'

@login_manager.user_loader  
def load_user(id):
    try:  
        user_data = container_users.read_item(item=id, partition_key=id)  
        return User(user_data['id'], user_data['email'], user_data['pw_hash'], user_data['role']) 
    except Exception as e:  
        flash(f"Error loading user: {e}")  
        return None  


@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:  
        return redirect(url_for('home'))    
  
    if request.method == 'POST':  
        email = request.form['email']  
        user = get_user(container_users, email)        
        if user:  

            user = User(user['id'], user['email'], user['pw_hash'], user['role'])  
            
            if user.check_pwd(request.form['password']):
                login_user(user)  
                return redirect(url_for('home'))
            else:
                flash('Incorrect password. Please try again.')
                return redirect(url_for('login'))
        else:
            flash(f'User with email "{email}" does not exist. Please try again.')
            return redirect(url_for('login'))
  
    return render_template('login.html')  

@app.route('/logout')
def logout():  
    logout_user()  
    return redirect(url_for('login'))   

######################  ROUTE FUNCTIONS   ######################

@app.context_processor  
def inject_current_user():  
    return {'current_user': current_user}

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    # search is submitted
    session['search_items'] = None
    if request.method == 'POST':
        user_selected_attributes = {}
        for Attribute in request.form.keys():
            if request.form.getlist(Attribute) == ['']:
                continue
            else:
                user_selected_attributes[Attribute] = request.form.getlist(Attribute)

        if len(user_selected_attributes) == 0:
            flash('Please select at least one attribute')
            return render_template('search.html')

        query_string = build_SQL_query(user_selected_attributes)

        if int(user_selected_attributes['Min weight'][0]) > int(user_selected_attributes['Max weight'][0]):
            flash('Minimum weight cannot be greater than maximum weight.')
            return render_template('search.html')
        else:        
            items = query_database(container_metabolites, query_string)

        if type(items) != list:
            flash(f"""Something went wrong. Please try again. Error: \n{items}""")
            return render_template('search.html')
        elif len(items) == 0:
            flash('No results found. Please try again.')
            return render_template('search.html')        
        
        return render_template('search_results.html', items=items)
    
    else:
        return render_template('search.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

######################### ADMIN ROUTE FUNCTIONS ###############################

@app.route('/users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def users():
    all_users = query_database(container_users, "SELECT c.email, c.role FROM c")
    if request.method == 'POST':

        if request.form['delete'] == 'True':
            if request.form['user_id'] == current_user.id:
                flash('You cannot delete yourself.')
                return render_template('users.html', users=all_users)
            elif request.form['user_id'] == god_user:
                flash('You cannot delete the God user.')
                return render_template('users.html', users=all_users)
            delete_user(container_users, request.form['user_id'])            
            return render_template('users.html', users=all_users)
        else:
            user_id = request.form['user_id']
            if user_id == god_user:
                flash('You cannot update the God user.')
                return render_template('users.html', users=all_users)            
            role = request.form[f'role_{user_id}']
            update_user_role(container_users, user_id, role)
            all_users = query_database(container_users, "SELECT c.email, c.role FROM c")
            return render_template('users.html', users=all_users)
    else:
        return render_template('users.html', users=all_users)
    
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if user_exists(container_users, email):
            flash(f'User with {email} email address already exists.')
            return render_template('add_user.html') 

        add_user(container_users, email, password, role)
        
        return render_template('add_user.html')
    else:
        return render_template('add_user.html')

######################### END ROUTE FUNCTIONS #################################


if __name__ == '__main__':  
    app.run(debug=True)  