# AirtableManager.py

from airtable import Airtable

from .config import Config


class AirtableManager(object):
    def __init__(self):
        self.api_key = Config.AIRTABLE_KEY
        self.table_key = Config.AIRTABLE_TABLE

        self.tables = {}
        self.tables["pers_table"] = Config.AIRTABLE_PERSON

    def get_all_rec(self, table, max_records=10000):
        table = Airtable(
            self.table_key,
            self.tables[table],
            self.api_key,
        )
        list_air_rec = table.get_all(max_records=max_records)

        return list_air_rec

    def get_rec_by_id(self, table, record_id):
        table = Airtable(
            self.table_key,
            self.tables[table],
            self.api_key,
        )
        air_rec = table.get(record_id=record_id)

        return air_rec

    def add_rec(self, table, rec):
        table = Airtable(
            self.table_key,
            self.tables[table],
            self.api_key,
        )
        p = table.insert(rec)

        return p

    def update_rec(self, table, uid, rec):
        table = Airtable(
            self.table_key,
            self.tables[table],
            self.api_key,
        )
        table.update(uid, rec)
