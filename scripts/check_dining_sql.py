"""Local-only disposable SQL transfer and dining HTTP checks. Never uses Azure."""
from pathlib import Path
import subprocess
import json
import os
import argparse
import sys


def sql(statement):
    subprocess.run(['docker','compose','exec','-T','sql','python3','/local/bootstrap.py','sql','-Q',statement],check=True,stdout=subprocess.DEVNULL)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--snapshot', type=Path, help='Optional private SQLite COPY with adjacent copied bills/')
args = parser.parse_args()
source_snapshot = None
if args.snapshot:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.transfer_assignment1 import load_snapshot
    source_snapshot = load_snapshot(args.snapshot)

names = ['picky_transfer_restaurants', 'picky_transfer_dining']
created = []
try:
    for name, login in zip(names, ['picky_restaurants','picky_dining']):
        sql(f"CREATE DATABASE [{name}]")
        created.append(name)
        sql(f"USE [{name}]; CREATE USER [{login}] FOR LOGIN [{login}]; ALTER ROLE db_owner ADD MEMBER [{login}]")
    transfer = Path('scripts/transfer_assignment1.py').read_text().split("if __name__ == '__main__':")[0]
    # Execute in the dining image; credentials stay inside compose and no host SQL port is needed.
    code = transfer.replace("sys.path.insert(0, str(Path(__file__).resolve().parents[1]))", '') + '''
from io import BytesIO
from flask import Flask
from services.dining.api import register
from service_runtime.database import migrate
url=os.environ['DATABASE_URL'].rsplit('/',1)[0]+'/picky_transfer_dining'
os.environ['DATABASE_URL']=url
migrate(url,Path('/app/migrations'))
snapshot={'visits':[dict(id=800,saved_restaurant_id=900,visit_date='2026-11-01',rating=4,notes='Synthetic')],
          'visit_items':[dict(id=801,visit_id=800,item_name='Soup',quantity=1,unit_price=3.50)],
          'bills':[dict(id=802,visit_id=800,content=b'%PDF-synthetic\\x00\\xff',media_type='application/pdf',original_name='test.pdf')]}
with closing(connect(url)) as connection:
    transfer_domain(connection,['visits','visit_items','bills'],snapshot)
    transfer_domain(connection,['visits','visit_items','bills'],snapshot)
    snapshot['visits'][0]['notes']='conflicting'
    try:
        transfer_domain(connection,['visits','visit_items','bills'],snapshot)
    except ValueError:
        pass
    else:
        raise AssertionError('Conflicting transfer accepted')
app=Flask('sql-check');register(app);web=app.test_client()
path='/saved-restaurants/900/visits/800'
assert web.get('/saved-restaurants/900/visits').json[0]['notes']=='Synthetic'
assert web.get(path+'/bills/802').data==b'%PDF-synthetic\\x00\\xff'
assert web.get('/saved-restaurants/901/visits/800/bills/802').status_code==404
assert web.post(path+'/items',json={'item_name':'Bread','quantity':2,'unit_price':1.25}).status_code==201
result=web.post(path+'/bills',data={'bill_file':(BytesIO(b'%PDF-upload'),'upload.pdf')})
assert result.status_code==201,result.text
assert web.get(path+'/bills/'+str(result.json['id'])).data==b'%PDF-upload'
assert migrate(url,Path('/app/migrations'))==0
print('Dining SQL: repeat transfer, conflict rollback, identity continuation, scoped items/bills, binary persistence and migration no-op passed')
'''
    if source_snapshot is not None:
        code += f"\nsnapshot={source_snapshot!r}\n" + "with closing(connect(url)) as connection:\n    for _ in range(2):\n        transfer_domain(connection,GROUPS['DINING_DATABASE_URL'],snapshot)\nprint('Private dining copy transferred twice with exact row and bill comparison')\n"
    subprocess.run(['docker','compose','exec','-T','dining','python','-m','service_runtime.local_start','python','-'],input=code,text=True,check=True)
    subprocess.run(['docker','compose','restart','dining'],check=True)
    subprocess.run(['docker','compose','up','-d','--wait','--wait-timeout','180','dining'],check=True)
    persistence = '''
import os
from flask import Flask
from services.dining.api import register
os.environ['DATABASE_URL']=os.environ['DATABASE_URL'].rsplit('/',1)[0]+'/picky_transfer_dining'
app=Flask('restart-check');register(app)
assert app.test_client().get('/saved-restaurants/900/visits/800/bills/802').data==b'%PDF-synthetic\\x00\\xff'
print('Dining restart retained exact SQL bill bytes')
'''
    subprocess.run(['docker','compose','exec','-T','dining','python','-m','service_runtime.local_start','python','-'],input=persistence,text=True,check=True)
    configuration = json.loads(subprocess.check_output(['docker','compose','config','--format','json'],text=True))
    environment = dict(os.environ)
    environment['DATABASE_URL'] = configuration['services']['restaurants']['environment']['DATABASE_URL'].rsplit('/',1)[0]+'/picky_transfer_restaurants'
    schema = Path('services/restaurants/migrations/001_init.sql').read_text()
    code = transfer.replace("sys.path.insert(0, str(Path(__file__).resolve().parents[1]))", '') + f"\nschema={schema!r}\n" + '''
url=os.environ['DATABASE_URL']
snapshot={'restaurants':[dict(id=900,title='Synthetic transfer')],
          'saved_restaurants':[dict(id=900,restaurant_id=900,status='visited')],
          'restaurant_images':[dict(id=901,restaurant_id=900,image_url='https://example.org/test.png')],
          'restaurant_emails':[dict(id=902,restaurant_id=900,email='test@example.org')]}
with closing(connect(url)) as connection:
    connection.cursor().execute(schema);connection.commit()
    for _ in range(2):
        transfer_domain(connection,GROUPS['RESTAURANTS_DATABASE_URL'],snapshot)
    cursor=connection.cursor()
    for table in snapshot:
        cursor.execute(f'SELECT COUNT(*) FROM dbo.{table}')
        assert cursor.fetchone()[0]==1
print('Restaurant SQL: IDs, relationships and repeat transfer passed')
'''
    if source_snapshot is not None:
        code += f"\nsnapshot={source_snapshot!r}\n" + "with closing(connect(url)) as connection:\n    for _ in range(2):\n        transfer_domain(connection,GROUPS['RESTAURANTS_DATABASE_URL'],snapshot)\nprint('Private restaurant copy transferred twice with exact row comparison')\n"
    subprocess.run(['docker','compose','run','--rm','--no-deps','-T','-e','DATABASE_URL','restaurants','python','-'],input=code,text=True,check=True,env=environment)

finally:
    for name in reversed(created):
        sql(f"IF DB_ID('{name}') IS NOT NULL BEGIN ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{name}]; END")
