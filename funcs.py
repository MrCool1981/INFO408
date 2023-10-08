import azure.cosmos.exceptions as exceptions
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash, redirect, url_for
from flask_login import UserMixin, current_user
from functools import wraps  
import os
from dotenv import load_dotenv
load_dotenv()

god_user = os.environ.get("ADMIN_EMAIL")

############ DEFINE CLASSES ###################

class User(UserMixin):  
    def __init__(self, id, email, pw_hash, role):  
        self.id = id  
        self.email = email  
        self.pw_hash = pw_hash
        self.role = role
  
    def set_pwd(self, pwd):  
        self.pw_hash = generate_password_hash(pwd)  
  
    def check_pwd(self, pwd):  
        return check_password_hash(self.pw_hash, pwd)
        
    def get_id(self):  
        return str(self.id)  

############ DECORATOR FUNCTIONS ##############
  
def role_required(role):  
    def decorator(f):  
        @wraps(f)  
        def decorated_function(*args, **kwargs):  
            if not current_user.is_authenticated or current_user.role != role:  
                flash('You do not have permission to access this page.', 'danger')  
                return redirect(url_for('home'))  
            return f(*args, **kwargs)  
        return decorated_function  
    return decorator

############ FUNCTIONS ########################

def set_up_database(client, DATABASE_ID, CONTAINER_ID_METABOLITES, CONTAINER_ID_USERS):
    """
    return dabase client and containers
    """
    try:
        # get database client
        try:
            db = client.get_database_client(DATABASE_ID)
            print('Database with id \'{0}\' was found'.format(DATABASE_ID))

        except Exception as e:
            print(f'An error when getting database client occured: {e}')

        # get container for metabolites
        try:
            container_metabolites = db.get_container_client(CONTAINER_ID_METABOLITES)
            print('Container with id \'{0}\' was found'.format(CONTAINER_ID_METABOLITES))

        except Exception as e:
            print(f'An error when getting metabolites container occured: {e}')
        
        # get container for users
        try:
            container_users = db.get_container_client(CONTAINER_ID_USERS)
            print('Container with id \'{0}\' was found'.format(CONTAINER_ID_USERS))

        except Exception as e:
            print(f'An error when getting user container occured: {e}')
        
        # setup admin user
        try:
            password = os.environ.get("ADMIN_PASSWORD")
            email = god_user
            if user_exists(container_users, email):
                print(f'Admin user with email "{email}" already exists')
            else:
                user = User(id=email, email=email, pw_hash=None, role='admin')  # Set default role to 'user'   
                user.set_pwd(password)  
                container_users.upsert_item(user.__dict__)
                print(f'Admin user with email "{email}" created')

        except Exception as e:
            print(f'An error occured when creating admin user: {e}')

    except exceptions.CosmosHttpResponseError as e:
        print('\nThere was an error connecting to the database. {0}'.format(e.message))

    finally:
            print("\nDatabase connection function is complete\n")
            return db, container_metabolites, container_users

def upload_item(container, document):
    # create item in the container
    container.upsert_item(body=document)

def read_item(container, doc_id, partition_key):
    # We can do an efficient point read lookup on partition key and id
    response = container.read_item(item=doc_id, partition_key=partition_key)
    return response

def user_exists(container, email):
    if get_user(container, email):
        return True
    else:
        return False

def get_user(container, email):
    try:
        query = f"SELECT * FROM c WHERE c.email = '{email}'"  
        user = list(container.query_items(query=query, enable_cross_partition_query=True))[0]
        return user
    except:
        return False

def add_user(container, email, password, role='user'):
    try:
        user = User(id=email, email=email, pw_hash=None, role=role)  # Set default role to 'user'   
        user.set_pwd(password)  
        container.upsert_item(user.__dict__)
        flash(f'User "{email}" added to database')
    except Exception as e:
        flash(f'The following error occured: {e}')

def delete_user(container, email):
    try:
        delete_item(container, email)
        flash(f'Deleted user "{email}')
    except Exception as e:
        flash(f'The following error occured: {e}')

def update_user_role(container, user_id, role):
    user = get_user(container, user_id)
    user['role'] = role
    container.upsert_item(user)
    flash(f'User "{user_id}" role updated to "{role}"')

def delete_item(container, doc_id):
    try:
        container.delete_item(item=doc_id, partition_key=doc_id)
    except Exception as e:
        flash(f'The following error occured while deleting a document: {e}')

def build_SQL_query(user_selected_attributes):
    query_string = f"""SELECT c.id AS ID, c.common_name AS "Metabolite name", c.formula AS "Chemical formula", c.average_molecular_weight AS "Average MW", c.pubchem_compound_id AS "PubChem ID" FROM c WHERE """

    if user_selected_attributes['Min weight'] != [''] and user_selected_attributes['Max weight'] != ['']:
        query_string += f"c.average_molecular_weight BETWEEN {user_selected_attributes['Min weight'][0]} AND {user_selected_attributes['Max weight'][0]}"
    elif user_selected_attributes['Min weight'] != [''] and user_selected_attributes['Max weight'] == ['']:
        query_string += f"c.average_molecular_weight >= {user_selected_attributes['Min weight'][0]}"
    elif user_selected_attributes['Min weight'] == [''] and user_selected_attributes['Max weight'] != ['']:
        query_string += f"c.average_molecular_weight <= {user_selected_attributes['Max weight'][0]}"

    return query_string

def query_database(container, query):
    """
    Query the database
    """
    try:
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        return items
    except Exception as e:
        return e.args