from pprint import pprint
from typing import Any, Optional, Dict
from unittest import result
from numpy import isin
from pymongo import MongoClient
import json
from clang.cindex import TokenKind, CursorKind
from urllib.parse import quote_plus

from lib.CodeAnalysis import SrcRange


class MongoDB():
    def __init__(self) -> None:

        with open('database_config.json', 'r') as db_config_file:
            db_config = json.load(db_config_file)

            uri = "mongodb://%s:%s@%s/?authMechanism=DEFAULT" % (
                quote_plus(db_config['username']), quote_plus(db_config['password']), db_config['host'])

            self.client = MongoClient(uri)
            self.db = self.client[db_config['database_name']]

    def get_commit(self, commit_id: str) -> Optional[Dict[str, Any]]:
        result = self.db.commits.find_one(
            {'_id': commit_id}
        )
        return result

    @staticmethod
    def make_obj_serializable(obj: object) -> object:
        if isinstance(obj, dict):
            return {MongoDB.make_obj_serializable(k): MongoDB.make_obj_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list) or isinstance(obj, set):
            return [MongoDB.make_obj_serializable(v) for v in obj]
        elif isinstance(obj, SrcRange) or isinstance(obj, TokenKind) or isinstance(obj, CursorKind):
            return str(obj)
        else:
            return obj

    def store_extracted_pattern(self, commit_id: str, single_line_changes) -> None:

        # make single line changes serialisable

        single_line_changes = self.make_obj_serializable(single_line_changes)
        result = self.db.commits.update_one(
            {
                '_id': commit_id
            },
            {
                '$set': {'single_line_changes': single_line_changes}
            }
        )
        # print(result.raw_result)


def test():
    m = MongoDB()

    m.get_commits('aFarkas/lazysizes_c4571fec36b56fa066014f1cb2ad7c1eea4e8428')
