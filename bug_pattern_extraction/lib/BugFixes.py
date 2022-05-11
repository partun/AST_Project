from turtle import st
from typing import Any, Optional, Dict
from pymongo import MongoClient
import json
from urllib.parse import quote_plus


class MongoDB():
    def __init__(self) -> None:

        with open('/Users/dominic/eth/01_SS22/AST_AutomatedSoftwareTesting/Project/SemSeed/database_config.json', 'r') as db_config_file:
            db_config = json.load(db_config_file)

            uri = "mongodb://%s:%s@%s/?authMechanism=DEFAULT" % (
                quote_plus(db_config['username']), quote_plus(db_config['password']), db_config['host'])

            self.client = MongoClient(uri)
            self.db = self.client[db_config['c_database_name']]

    def get_commit(self, commit_id: str) -> Optional[Dict[str, Any]]:
        result = self.db.commits.find_one(
            {'_id': commit_id}
        )
        return result


def test():
    m = MongoDB()

    m.get_commits('aFarkas/lazysizes_c4571fec36b56fa066014f1cb2ad7c1eea4e8428')
