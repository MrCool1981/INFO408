import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
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

############ FUNCTIONS ########################

def create_database(client, DATABASE_ID, CONTAINER_ID_METABOLITES, CONTAINER_ID_USERS):
    """
    Database to create database and containers
    """
    try:
        # setup database for this sample
        try:
            db = client.create_database(id=DATABASE_ID)
            print('Database with id \'{0}\' created'.format(DATABASE_ID))

        except exceptions.CosmosResourceExistsError:
            db = client.get_database_client(DATABASE_ID)
            print('Database with id \'{0}\' was found'.format(DATABASE_ID))

        # setup container for metabolites
        try:
            container_metabolites = db.create_container(id=CONTAINER_ID_METABOLITES, partition_key=PartitionKey(path='/id', kind='Hash'))
            print('Container with id \'{0}\' created'.format(CONTAINER_ID_METABOLITES))

        except exceptions.CosmosResourceExistsError:
            container_metabolites = db.get_container_client(CONTAINER_ID_METABOLITES)
            print('Container with id \'{0}\' was found'.format(CONTAINER_ID_METABOLITES))
        
        # setup container for users
        try:
            container_users = db.create_container(id=CONTAINER_ID_USERS, partition_key=PartitionKey(path='/id', kind='Hash'))
            print('Container with id \'{0}\' created'.format(CONTAINER_ID_USERS))

        except exceptions.CosmosResourceExistsError:
            container_users = db.get_container_client(CONTAINER_ID_USERS)
            print('Container with id \'{0}\' was found'.format(CONTAINER_ID_USERS))
        
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
            print(f'The following error occured: {e}')

    except exceptions.CosmosHttpResponseError as e:
        print('\nThere was an error creating database. {0}'.format(e.message))

    finally:
            print("\nDatabase create function is complete\n")
            return db, container_metabolites, container_users

# function to create item in the container
def upload_item(container, document):
    container.upsert_item(body=document)


def read_item(container, doc_id, partition_key):
    response = container.read_item(item=doc_id, partition_key=partition_key)
    return response

# create a document with a new schema
def create_new_document(doc):
    new_doc = dict() # initialize a new dictionary for a document
    new_doc['id'] = doc['accession'] # assign id
    new_doc['common_name'] = doc['name'] # assign name
    new_doc['description'] = doc['description'] # add description
    # add the following fields if they exist:
    #  Chemical Formula
    new_doc['formula'] = doc['chemical_formula']
    # Average Molecular Weight
    new_doc['average_molecular_weight'] = float(doc['average_molecular_weight']) if doc['average_molecular_weight'] is not None else None
    # Monoisotopic Molecular Weight
    new_doc['monoisotopic_molecular_weight'] = float(doc['monisotopic_molecular_weight']) if doc['monisotopic_molecular_weight'] is not None else None
    # IUPAC Name
    new_doc['iupac_name'] = doc['iupac_name']      
    # Traditional Name
    new_doc['traditional_iupac_name'] = doc['traditional_iupac']         
    # CAS Registry Number
    new_doc['cas_registry_number'] = doc['cas_registry_number']
    # SMILES
    new_doc['smiles'] = doc['smiles']
    # InChI Identifier
    new_doc['inchi_identifier'] = doc['inchi']
    # InChI Key
    new_doc['inchi_key'] = doc['inchikey']             
    if doc['taxonomy'] is not None:
        # Kingdom
        new_doc['taxonomy'] = dict()
        new_doc['taxonomy']['kingdom'] = doc['taxonomy']['kingdom']          
        # Super Class
        new_doc['taxonomy']['super_class'] = doc['taxonomy']['super_class']
        # Class
        new_doc['taxonomy']['class'] = doc['taxonomy']['class']
        # Sub Class
        new_doc['taxonomy']['sub_class'] = doc['taxonomy']['sub_class']
        # Direct Parent
        new_doc['taxonomy']['direct_parent'] = doc['taxonomy']['direct_parent']
        # Molecular Framework
        new_doc['taxonomy']['molecular_framework'] = doc['taxonomy']['molecular_framework']
    else:
        new_doc['taxonomy'] = None
    # PubChem Compound
    new_doc['pubchem_compound_id'] = doc.get('pubchem_compound_id')
    
    return new_doc

# function to check if user exists in database
def user_exists(container, email):
    if get_user(container, email):
        return True
    else:
        return False

# function to get user from database
def get_user(container, email):
    try:
        query = f"SELECT * FROM c WHERE c.email = '{email}'"  
        user = list(container.query_items(query=query, enable_cross_partition_query=True))[0]
        return user
    except:
        return False