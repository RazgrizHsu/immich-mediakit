#!/usr/bin/env python
import json
import os
import sys
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from util.models import Now, Usr, AppState, Nfy, Tsk, Mdl, Asset, AssetExif
from util.baseModel import Json
import db.pics as pics
from util import log

lg = log.get(__name__)


class TestBaseDictModel(unittest.TestCase):

    def test_simple_model(self):
        usr = Usr(id="1", name="TestUser", email="test@example.com", key="test-key")

        usr_dict = usr.toDict()
        usr_json = usr.toJson()

        self.assertEqual(usr_dict["id"], "1")
        self.assertEqual(usr_dict["name"], "TestUser")

        usr_from_dict = Usr.fromStore(usr_dict)
        usr_from_json = Usr.fromStore(json.loads(usr_json))

        self.assertEqual(usr_from_dict.id, "1")
        self.assertEqual(usr_from_dict.name, "TestUser")
        self.assertEqual(usr_from_json.id, "1")
        self.assertEqual(usr_from_json.email, "test@example.com")

    def test_optional_fields(self):
        usr1 = Usr(id="1", name="User1")
        self.assertEqual(usr1.id, "1")
        self.assertEqual(usr1.name, "User1")
        self.assertIsNone(usr1.email)
        self.assertIsNone(usr1.key)

        usr1_dict = usr1.toDict()
        usr1_restored = Usr.fromStore(usr1_dict)

        self.assertEqual(usr1_restored.id, "1")
        self.assertEqual(usr1_restored.name, "User1")
        self.assertIsNone(usr1_restored.email)

        usr2 = Usr()
        usr2_dict = usr2.toDict()
        usr2_restored = Usr.fromStore(usr2_dict)

        self.assertIsNone(usr2_restored.id)
        self.assertIsNone(usr2_restored.name)

    def test_nested_model(self):
        usr = Usr(id="1", name="User1", email="user1@example.com")
        now = Now(usr=usr, useType="test")

        now_dict = now.toDict()
        self.assertEqual(now_dict["usr"]["id"], "1")
        self.assertEqual(now_dict["usr"]["name"], "User1")

        now_restored = Now.fromStore(now_dict)

        self.assertIsInstance(now_restored.usr, Usr)
        self.assertEqual(now_restored.usr.id, "1")
        self.assertEqual(now_restored.usr.name, "User1")

    def test_list_of_models(self):
        usr1 = Usr(id="1", name="User1")
        usr2 = Usr(id="2", name="User2")

        now = Now(usrs=[usr1, usr2])

        now_dict = now.toDict()
        self.assertEqual(len(now_dict["usrs"]), 2)
        self.assertEqual(now_dict["usrs"][0]["id"], "1")
        self.assertEqual(now_dict["usrs"][1]["id"], "2")

        now_restored = Now.fromStore(now_dict)

        self.assertEqual(len(now_restored.usrs), 2)
        self.assertIsInstance(now_restored.usrs[0], Usr)
        self.assertIsInstance(now_restored.usrs[1], Usr)
        self.assertEqual(now_restored.usrs[0].id, "1")
        self.assertEqual(now_restored.usrs[1].id, "2")

    def test_optional_nested_model(self):
        now1 = Now(useType="test")
        self.assertIsNone(now1.usr)

        now1_dict = now1.toDict()
        now1_restored = Now.fromStore(now1_dict)

        self.assertIsNone(now1_restored.usr)
        self.assertEqual(now1_restored.useType, "test")

        usr = Usr(id="1", name="User1")
        now2 = Now(usr=usr, useType="test")

        now2_dict = now2.toDict()
        now2_restored = Now.fromStore(now2_dict)

        self.assertIsInstance(now2_restored.usr, Usr)
        self.assertEqual(now2_restored.usr.id, "1")

    def test_complex_nested_models(self):
        usr1 = Usr(id="1", name="User1")
        usr2 = Usr(id="2", name="User2")

        now = Now(
            usr=usr1,
            useType="test",
            cntPic=10,
            cntVec=5,
            usrs=[usr1, usr2]
        )

        now_dict = now.toDict()

        now_restored = Now.fromStore(now_dict)

        self.assertIsInstance(now_restored.usr, Usr)
        self.assertEqual(now_restored.usr.id, "1")

        self.assertEqual(len(now_restored.usrs), 2)
        self.assertIsInstance(now_restored.usrs[0], Usr)
        self.assertEqual(now_restored.usrs[0].id, "1")
        self.assertEqual(now_restored.usrs[1].id, "2")

    def test_json_class(self):
        json_str = '{"make":"Canon","model":"EOS 5D"}'
        json_obj1 = Json(json_str)
        self.assertEqual(json_obj1["make"], "Canon")
        self.assertEqual(json_obj1["model"], "EOS 5D")

        json_dict = {"make": "Nikon", "model": "D850"}
        json_obj2 = Json(json_dict)
        self.assertEqual(json_obj2["make"], "Nikon")
        self.assertEqual(json_obj2["model"], "D850")

        json_obj2["make"] = "Sony"
        self.assertEqual(json_obj2["make"], "Sony")

        json_obj2["year"] = 2023
        self.assertEqual(json_obj2["year"], 2023)

    def test_asset_model(self):
        asset = Asset(
            id="test-asset",
            ownerId="user1",
            originalFileName="test.jpg"
        )

        asset_dict = asset.toDict()
        self.assertEqual(asset_dict["id"], "test-asset")
        self.assertEqual(asset_dict["ownerId"], "user1")

        asset_restored = Asset.fromStore(asset_dict)
        self.assertEqual(asset_restored.id, "test-asset")
        self.assertEqual(asset_restored.originalFileName, "test.jpg")

        self.assertEqual(asset_restored.isVectored, 0)
        
    def test_asset_exif_json_string_conversion(self):
        exif_json_string = '{"make":"Canon","model":"EOS 5D","fNumber":2.8,"iso":100,"focalLength":24.0}'
        
        asset_dict = {
            "id": "test-asset",
            "jsonExif": exif_json_string
        }
        
        asset = Asset.fromStore(asset_dict)
        self.assertIsInstance(asset.jsonExif, AssetExif)
        self.assertEqual(asset.jsonExif.make, "Canon")
        self.assertEqual(asset.jsonExif.model, "EOS 5D")
        self.assertEqual(asset.jsonExif.fNumber, 2.8)
        self.assertEqual(asset.jsonExif.iso, 100)
        self.assertEqual(asset.jsonExif.focalLength, 24.0)
        
    def test_asset_exif_from_db(self):
        mock_cursor = type('MockCursor', (), {'description': [('id',), ('jsonExif',)]})()
        row = ('test-asset', '{"make":"Nikon","model":"D850","fNumber":4.0,"iso":200,"focalLength":70.0}')
        
        asset = Asset.fromDB(mock_cursor, row)
        self.assertIsInstance(asset.jsonExif, AssetExif)
        self.assertEqual(asset.jsonExif.make, "Nikon")
        self.assertEqual(asset.jsonExif.model, "D850")
        self.assertEqual(asset.jsonExif.fNumber, 4.0)
        self.assertEqual(asset.jsonExif.iso, 200)
        self.assertEqual(asset.jsonExif.focalLength, 70.0)

    def test_datetime_serialization(self):
        test_dt = datetime(2023, 1, 1, 12, 0, 0)
        state = AppState(
            current_page="photos",
            last_updated=test_dt
        )

        state_dict = state.toDict()
        state_json = state.toJson()

        self.assertTrue(isinstance(state_dict["last_updated"], datetime))

        state_from_json = json.loads(state_json)
        self.assertTrue(isinstance(state_from_json["last_updated"], str))

        state_restored = AppState.fromStore(state_dict)
        self.assertTrue(isinstance(state_restored.last_updated, datetime))
        self.assertEqual(state_restored.last_updated.year, 2023)
        self.assertEqual(state_restored.last_updated.month, 1)

    def test_dict_field(self):
        nfy = Nfy()
        nfy.info("Test message", 3000)

        nfy_dict = nfy.toDict()
        self.assertEqual(len(nfy_dict["msgs"]), 1)

        msg_id = list(nfy_dict["msgs"].keys())[0]
        self.assertEqual(nfy_dict["msgs"][msg_id]["message"], "Test message")
        self.assertEqual(nfy_dict["msgs"][msg_id]["type"], "info")

        nfy_restored = Nfy.fromStore(nfy_dict)
        self.assertEqual(len(nfy_restored.msgs), 1)
        msg_id = list(nfy_restored.msgs.keys())[0]
        self.assertEqual(nfy_restored.msgs[msg_id]["message"], "Test message")

    def test_combined_complex_scenario(self):
        usr1 = Usr(id="1", name="User1")
        usr2 = Usr(id="2", name="User2")

        now = Now(
            usr=usr1,
            useType="test",
            usrs=[usr1, usr2]
        )

        nfy = Nfy()
        nfy.info("System message")
        nfy.warn("Warning message")

        tsk = Tsk(
            id="task1",
            name="Process task",
            args={"model": "Now", "action": "update"}
        )

        mdl = Mdl(
            id="modal1",
            msg="Confirm delete?",
            cmd="delete",
            args={"targetId": "1"}
        )

        data = {
            "now": now.toDict(),
            "nfy": nfy.toDict(),
            "tsk": tsk.toDict(),
            "mdl": mdl.toDict()
        }

        now_restored = Now.fromStore(data["now"])
        nfy_restored = Nfy.fromStore(data["nfy"])
        tsk_restored = Tsk.fromStore(data["tsk"])
        mdl_restored = Mdl.fromStore(data["mdl"])

        self.assertIsInstance(now_restored.usr, Usr)
        self.assertEqual(now_restored.usr.id, "1")

        self.assertEqual(len(now_restored.usrs), 2)
        self.assertIsInstance(now_restored.usrs[0], Usr)

        self.assertEqual(len(nfy_restored.msgs), 2)

        tsk_restored.reset()
        self.assertIsNone(tsk_restored.id)
        self.assertEqual(tsk_restored.args, {})

        mdl_restored.reset()
        self.assertIsNone(mdl_restored.id)
        self.assertFalse(mdl_restored.ok)

    def test_switch_usr_function(self):
        usr1 = Usr(id="1", name="User1")
        usr2 = Usr(id="2", name="User2")

        now = Now(usrs=[usr1, usr2])

        self.assertIsNone(now.usr)

        now.switchUsr("1")
        self.assertIsInstance(now.usr, Usr)
        self.assertEqual(now.usr.id, "1")

        now.switchUsr("2")
        self.assertIsInstance(now.usr, Usr)
        self.assertEqual(now.usr.id, "2")

        now.switchUsr("3")
        self.assertIsNone(now.usr)

        now.switchUsr("1")
        now_dict = now.toDict()
        now_restored = Now.fromStore(now_dict)

        self.assertIsInstance(now_restored.usr, Usr)
        self.assertEqual(now_restored.usr.id, "1")

        now_restored.switchUsr("2")
        self.assertIsInstance(now_restored.usr, Usr)
        self.assertEqual(now_restored.usr.id, "2")
        
    def test_db_assets_exif_conversion(self):
        try:
            pics.init()
            assets = pics.getAll(count=5)
            
            if not assets:
                self.skipTest("No assets found in database")
                
            for asset in assets:
                if asset.jsonExif is not None:
                    self.assertIsInstance(asset.jsonExif, AssetExif)
                    
                    if hasattr(asset.jsonExif, 'make') and asset.jsonExif.make:
                        self.assertIsInstance(asset.jsonExif.make, str)
                    if hasattr(asset.jsonExif, 'model') and asset.jsonExif.model:
                        self.assertIsInstance(asset.jsonExif.model, str)
                    if hasattr(asset.jsonExif, 'fNumber') and asset.jsonExif.fNumber:
                        self.assertIsInstance(asset.jsonExif.fNumber, float)
                    if hasattr(asset.jsonExif, 'iso') and asset.jsonExif.iso:
                        self.assertIsInstance(asset.jsonExif.iso, int)
                    if hasattr(asset.jsonExif, 'dateTimeOriginal') and asset.jsonExif.dateTimeOriginal:
                        self.assertIsInstance(asset.jsonExif.dateTimeOriginal, str)
        finally:
            pics.close()
            
    def test_specific_asset_exif_conversion(self):
        try:
            pics.init()
            assets = pics.getAll(count=1)
            
            if not assets:
                self.skipTest("No assets found in database")
                
            asset_id = assets[0].id
            asset = pics.getAssetInfo(asset_id)
            
            self.assertIsNotNone(asset)
            self.assertEqual(asset.id, asset_id)
            
            if asset.jsonExif is not None:
                self.assertIsInstance(asset.jsonExif, AssetExif)
                
                if hasattr(asset.jsonExif, 'make') and asset.jsonExif.make:
                    self.assertIsInstance(asset.jsonExif.make, str)
                if hasattr(asset.jsonExif, 'model') and asset.jsonExif.model:
                    self.assertIsInstance(asset.jsonExif.model, str)
                if hasattr(asset.jsonExif, 'fNumber') and asset.jsonExif.fNumber:
                    self.assertIsInstance(asset.jsonExif.fNumber, float)
                if hasattr(asset.jsonExif, 'iso') and asset.jsonExif.iso:
                    self.assertIsInstance(asset.jsonExif.iso, int)
                if hasattr(asset.jsonExif, 'dateTimeOriginal') and asset.jsonExif.dateTimeOriginal:
                    self.assertIsInstance(asset.jsonExif.dateTimeOriginal, str)
        finally:
            pics.close()


if __name__ == "__main__":
    unittest.main()
