from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
from flask_restful.utils import cors
from sqlalchemy import (create_engine, MetaData, Table, select, update, and_)

app = Flask(__name__)
api = Api(app)
api.decorators=[cors.crossdomain(origin='*')]

db_connect = create_engine('sqlite:///pud.db')

meta = MetaData()
meta.reflect(bind=db_connect)
        

class AlignmentServerByID(Resource):
    """Returns aligned sentences with alignment and verification
    status with GET. Changes alignment and verification status
    with POST."""
    def get(self, table_name, document_id, sentence_id):
        with db_connect.connect() as conn:
            pud_table = Table(table_name, meta, autoload = True)
            stmt = select([pud_table]).\
                where(
                    and_(
                        pud_table.c.document_id == document_id,
                        pud_table.c.sentence_id == sentence_id
                    )
                )
            rs = conn.execute(stmt)
            return [dict(row) for row in rs.fetchall()]

        
    def post(self, table_name, document_id, sentence_id):
        args = {
            'alignment': None,
            'verified': None
            }
        args.update(request.get_json(force = True))
        if args['alignment'] is None and args['verified'] is None:
            abort(400, message = "No data provided")
        vals = {}
        if not (args['alignment'] is None): # Can be an empty string
            vals['alignment'] = args['alignment']
        if not (args['verified'] is None): # Can be zero
            try:
                vals['verified'] = int(args['verified'])
                if vals['verified'] not in {0,1}:
                    abort(400, message = f"Verification value is must be 0 or 1, is {args['verified']}")
            except ValueError:
                abort(400, message = f"Verification value is invalid: {args['verified']}")
        with db_connect.connect() as conn:
            pud_table = Table(table_name, meta, autoload = True)
            stmt = pud_table.update().\
                where(
                    and_(
                        pud_table.c.document_id == document_id,
                        pud_table.c.sentence_id == sentence_id
                        )
                    ).\
                values(**vals)
            rs = conn.execute(stmt)
            return [] # The status defaults to 200

        
class AlignmentServerGetCorpora(Resource):
    def get(self):
        with db_connect.connect() as conn:
            rs = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [dict(row) for row in rs.fetchall()]


class AlignmentServerGetIDs(Resource):
    def get(self, table_name):
        with db_connect.connect() as conn:
            pud_table = Table(table_name, meta, autoload = True)
            stmt = select([
                pud_table.c.document_id,
                pud_table.c.sentence_id         
            ])
            rs = conn.execute(stmt)
            return [dict(row) for row in rs.fetchall()]


api.add_resource(AlignmentServerGetCorpora, '/corpora')
api.add_resource(AlignmentServerGetIDs, '/getids/<table_name>')
api.add_resource(AlignmentServerByID, '/<table_name>/<document_id>/<sentence_id>')


# Using gunicorn + nginx for production
if __name__ == '__main__':
    print("Starting a toy server...")
    app.run(debug=True)
                            
        



