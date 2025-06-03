#!/usr/bin/env python
import json
import os
import sys
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from mod.models import Now, Usr, Nfy, Tsk, Mdl, Asset, AssetExif, SimInfo, WsMsg, TskStatus
from mod.bse.baseModel import Json, BaseDictModel
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

        usr_from_dict = Usr.fromDict(usr_dict)
        usr_from_json = Usr.fromDict(json.loads(usr_json))

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
        usr1_restored = Usr.fromDict(usr1_dict)

        self.assertEqual(usr1_restored.id, "1")
        self.assertEqual(usr1_restored.name, "User1")
        self.assertIsNone(usr1_restored.email)

        usr2 = Usr()
        usr2_dict = usr2.toDict()
        usr2_restored = Usr.fromDict(usr2_dict)

        self.assertIsNone(usr2_restored.id)
        self.assertIsNone(usr2_restored.name)

    def test_nested_model(self):
        usr = Usr(id="1", name="User1", email="user1@example.com")
        now = Now(usr=usr, useType="test")

        now_dict = now.toDict()
        self.assertEqual(now_dict["usr"]["id"], "1")
        self.assertEqual(now_dict["usr"]["name"], "User1")

        now_restored = Now.fromDict(now_dict)

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

        now_restored = Now.fromDict(now_dict)

        self.assertEqual(len(now_restored.usrs), 2)
        self.assertIsInstance(now_restored.usrs[0], Usr)
        self.assertIsInstance(now_restored.usrs[1], Usr)
        self.assertEqual(now_restored.usrs[0].id, "1")
        self.assertEqual(now_restored.usrs[1].id, "2")

    def test_optional_nested_model(self):
        now1 = Now(useType="test")
        self.assertIsNone(now1.usr)

        now1_dict = now1.toDict()
        now1_restored = Now.fromDict(now1_dict)

        self.assertIsNone(now1_restored.usr)
        self.assertEqual(now1_restored.useType, "test")

        usr = Usr(id="1", name="User1")
        now2 = Now(usr=usr, useType="test")

        now2_dict = now2.toDict()
        now2_restored = Now.fromDict(now2_dict)

        self.assertIsInstance(now2_restored.usr, Usr)
        self.assertEqual(now2_restored.usr.id, "1")

    def test_complex_nested_models(self):
        usr1 = Usr(id="1", name="User1")
        usr2 = Usr(id="2", name="User2")

        now = Now(
            usr=usr1,
            useType="test",
            usrs=[usr1, usr2]
        )

        now_dict = now.toDict()

        now_restored = Now.fromDict(now_dict)

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

        asset_restored = Asset.fromDict(asset_dict)
        self.assertEqual(asset_restored.id, "test-asset")
        self.assertEqual(asset_restored.originalFileName, "test.jpg")

        self.assertEqual(asset_restored.isVectored, 0)
        self.assertEqual(asset_restored.simInfos, [])

    def test_asset_model_with_simInfos(self):
        asset = Asset(
            id="test-asset",
            ownerId="user1",
            originalFileName="test.jpg",
            simInfos=[SimInfo('a', 0.5), SimInfo('b', 0.6)]
        )

        asset_dict = asset.toDict()
        self.assertEqual(asset_dict["id"], "test-asset")
        self.assertEqual(asset_dict["ownerId"], "user1")
        self.assertEqual(len(asset_dict["simInfos"]), 2)
        self.assertEqual(asset_dict["simInfos"][0]["id"], "a")
        self.assertEqual(asset_dict["simInfos"][1]["id"], "b")

        asset_restored = Asset.fromDict(asset_dict)
        self.assertEqual(asset_restored.id, "test-asset")
        self.assertEqual(asset_restored.originalFileName, "test.jpg")
        self.assertEqual(len(asset_restored.simInfos), 2)
        self.assertIsInstance(asset_restored.simInfos[0], SimInfo)
        self.assertEqual(asset_restored.simInfos[0].id, "a")
        self.assertEqual(asset_restored.simInfos[0].score, 0.5)

    def test_asset_exif_json_string_conversion(self):
        exif_json_string = '{"make":"Canon","model":"EOS 5D","fNumber":2.8,"iso":100,"focalLength":24.0}'

        asset_dict = {
            "id": "test-asset",
            "jsonExif": exif_json_string
        }

        asset = Asset.fromDict(asset_dict)
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

    def test_asset_simInfos_from_db(self):
        mock_cursor = type('MockCursor', (), {'description': [('id',), ('simInfos',)]})()

        row = ('test-asset', '[{"id":"id1","score":0.9},{"id":"id2","score":0.8},{"id":"id3","score":0.7}]')
        asset = Asset.fromDB(mock_cursor, row)

        self.assertEqual(len(asset.simInfos), 3)
        self.assertIsInstance(asset.simInfos[0], SimInfo)
        self.assertEqual(asset.simInfos[0].id, "id1")
        self.assertEqual(asset.simInfos[0].score, 0.9)

        row = ('test-asset', '[]')
        asset = Asset.fromDB(mock_cursor, row)
        self.assertEqual(asset.simInfos, [])

        row = ('test-asset', None)
        asset = Asset.fromDB(mock_cursor, row)
        self.assertEqual(asset.simInfos, [])

    def test_datetime_serialization(self):
        test_dt = datetime(2023, 1, 1, 12, 0, 0)
        tsk = Tsk(
            id="task1",
            name="Test Task",
            args={"created_at": test_dt}
        )

        tsk_dict = tsk.toDict()
        tsk_json = tsk.toJson()

        self.assertTrue(isinstance(tsk_dict["args"]["created_at"], datetime))

        tsk_from_json = json.loads(tsk_json)
        self.assertTrue(isinstance(tsk_from_json["args"]["created_at"], str))

        tsk_restored = Tsk.fromDict(tsk_dict)
        self.assertTrue(isinstance(tsk_restored.args["created_at"], datetime))
        self.assertEqual(tsk_restored.args["created_at"].year, 2023)
        self.assertEqual(tsk_restored.args["created_at"].month, 1)

    def test_dict_field(self):
        nfy = Nfy()
        nfy.info("Test message", 3000)

        nfy_dict = nfy.toDict()
        self.assertEqual(len(nfy_dict["msgs"]), 1)

        msg_id = list(nfy_dict["msgs"].keys())[0]
        self.assertEqual(nfy_dict["msgs"][msg_id]["message"], "Test message")
        self.assertEqual(nfy_dict["msgs"][msg_id]["type"], "info")

        nfy_restored = Nfy.fromDict(nfy_dict)
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
        )

        mdl = Mdl(
            id="modal1",
            msg="Confirm delete?",
            cmd="delete",
        )

        data = {
            "now": now.toDict(),
            "nfy": nfy.toDict(),
            "tsk": tsk.toDict(),
            "mdl": mdl.toDict()
        }

        now_restored = Now.fromDict(data["now"])
        nfy_restored = Nfy.fromDict(data["nfy"])
        tsk_restored = Tsk.fromDict(data["tsk"])
        mdl_restored = Mdl.fromDict(data["mdl"])

        self.assertIsInstance(now_restored.usr, Usr)
        self.assertEqual(now_restored.usr.id, "1")

        self.assertEqual(len(now_restored.usrs), 2)
        self.assertIsInstance(now_restored.usrs[0], Usr)

        self.assertEqual(len(nfy_restored.msgs), 2)

        tsk_restored.reset()
        self.assertIsNone(tsk_restored.id)

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
        now_restored = Now.fromDict(now_dict)

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

                self.assertIsInstance(asset.simInfos, list)
                for sim in asset.simInfos:
                    if sim:
                        self.assertIsInstance(sim, SimInfo)
                        self.assertTrue(hasattr(sim, 'id'))
                        self.assertTrue(hasattr(sim, 'score'))
        finally:
            pics.close()

    def test_db_simInfos_functionality(self):
        try:
            pics.init()
            assets = pics.getAll(count=5)

            if not assets:
                self.fail("No assets found in database")

            for ass in assets:
                self.assertIsInstance(ass.simInfos, list)
                for sim in ass.simInfos:
                    if sim:
                        self.assertIsInstance(sim, SimInfo)
                        self.assertTrue(hasattr(sim, 'id'))
                        self.assertTrue(hasattr(sim, 'score'))


        finally:
            pics.close()

    def test_specific_asset_exif_conversion(self):
        try:
            pics.init()
            assets = pics.getAll(count=1)

            if not assets:
                self.skipTest("No assets found in database")

            asset_id = assets[0].id
            asset = pics.getById(asset_id)

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

            self.assertTrue(hasattr(asset, 'simInfos'))
            self.assertIsInstance(asset.simInfos, list)
        finally:
            pics.close()


    def test_modal_basic(self):

        now = Now()

        lg.info( f"pg.sim: {now.sim}" )

    def test_fromDict_error_handling(self):
        # Test with required field missing (will cause TypeError in __init__)
        class RequiredFieldModel(BaseDictModel):
            id: str  # required field
            name: str  # required field

            def __init__(self, id: str, name: str):
                self.id = id
                self.name = name

        # Missing required field 'name'
        invalid_dict = {"id": "test"}
        result = RequiredFieldModel.fromDict(invalid_dict)
        self.assertIsNone(result)

        # Test with wrong number of arguments
        invalid_dict2 = {"id": "test", "name": "test", "extra": "field", "another": "field"}
        result2 = RequiredFieldModel.fromDict(invalid_dict2)
        # This should succeed as extra fields are filtered
        self.assertIsNotNone(result2)

    def test_fromStr_basic(self):
        usr = Usr(id="1", name="TestUser", email="test@example.com", key="test-key")
        json_str = usr.toJson()

        usr_restored = Usr.fromStr(json_str)
        self.assertEqual(usr_restored.id, "1")
        self.assertEqual(usr_restored.name, "TestUser")
        self.assertEqual(usr_restored.email, "test@example.com")
        self.assertEqual(usr_restored.key, "test-key")

    def test_fromStr_with_nested_model(self):
        usr = Usr(id="1", name="User1", email="user1@example.com")
        now = Now(usr=usr, useType="test")

        json_str = now.toJson()
        now_restored = Now.fromStr(json_str)

        self.assertIsInstance(now_restored.usr, Usr)
        self.assertEqual(now_restored.usr.id, "1")
        self.assertEqual(now_restored.usr.name, "User1")
        self.assertEqual(now_restored.useType, "test")

    def test_fromStr_with_list_of_models(self):
        usr1 = Usr(id="1", name="User1")
        usr2 = Usr(id="2", name="User2")
        now = Now(usrs=[usr1, usr2])

        json_str = now.toJson()
        now_restored = Now.fromStr(json_str)

        self.assertEqual(len(now_restored.usrs), 2)
        self.assertIsInstance(now_restored.usrs[0], Usr)
        self.assertIsInstance(now_restored.usrs[1], Usr)
        self.assertEqual(now_restored.usrs[0].id, "1")
        self.assertEqual(now_restored.usrs[1].id, "2")

    def test_fromStr_with_datetime(self):
        test_dt = datetime(2023, 1, 1, 12, 0, 0)
        tsk = Tsk(id="task1", name="Test Task", args={"created_at": test_dt})

        json_str = tsk.toJson()
        tsk_restored = Tsk.fromStr(json_str)

        self.assertEqual(tsk_restored.id, "task1")
        self.assertEqual(tsk_restored.name, "Test Task")
        self.assertIn("created_at", tsk_restored.args)

    def test_fromStr_invalid_json(self):
        with self.assertRaises(ValueError) as ctx:
            Usr.fromStr("not a json string")
        self.assertIn("Invalid JSON string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            Usr.fromStr("{invalid json}")
        self.assertIn("Invalid JSON string", str(ctx.exception))

    def test_fromStr_non_dict_json(self):
        with self.assertRaises(ValueError) as ctx:
            Usr.fromStr("[1, 2, 3]")
        self.assertIn("Expected dict after JSON parse", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            Usr.fromStr('"string value"')
        self.assertIn("Expected dict after JSON parse", str(ctx.exception))

    def test_fromStr_with_complex_model(self):
        asset = Asset(
            id="test-asset",
            ownerId="user1",
            originalFileName="test.jpg",
            simInfos=[SimInfo('a', 0.5), SimInfo('b', 0.6)]
        )

        json_str = asset.toJson()
        asset_restored = Asset.fromStr(json_str)

        self.assertEqual(asset_restored.id, "test-asset")
        self.assertEqual(asset_restored.ownerId, "user1")
        self.assertEqual(len(asset_restored.simInfos), 2)
        self.assertIsInstance(asset_restored.simInfos[0], SimInfo)
        self.assertEqual(asset_restored.simInfos[0].id, "a")
        self.assertEqual(asset_restored.simInfos[0].score, 0.5)

    def test_fromDB_error_handling(self):
        # Test with required field missing (will cause TypeError in __init__)
        class RequiredFieldModel(BaseDictModel):
            id: str  # required field
            name: str  # required field

            def __init__(self, id: str, name: str):
                self.id = id
                self.name = name

        # Mock cursor with only 'id' column, missing 'name'
        mock_cursor = type('MockCursor', (), {'description': [('id',)]})()
        row = ('test-id',)
        result = RequiredFieldModel.fromDB(mock_cursor, row)
        self.assertIsNone(result)

        # Test with exception in processing
        mock_cursor2 = type('MockCursor', (), {'description': None})()  # This will cause AttributeError
        row2 = ('test-id', 'test-name')
        result2 = RequiredFieldModel.fromDB(mock_cursor2, row2)
        self.assertIsNone(result2)


    def test_wsmsg_with_enum(self):
        # Test 1: Create WsMsg with TskStatus enum
        msg = WsMsg(
            tsn="task-123",
            type="progress",
            name="Test Task",
            message="Processing...",
            status=TskStatus.RUNNING
        )

        self.assertEqual(msg.tsn, "task-123")
        self.assertEqual(msg.status, TskStatus.RUNNING)

        # Test 2: Convert to dict
        msg_dict = msg.toDict()
        self.assertEqual(msg_dict["tsn"], "task-123")
        self.assertEqual(msg_dict["status"], TskStatus.RUNNING)

        # Test 3: Convert to JSON and back
        json_str = msg.toJson()
        self.assertIn('"tsn": "task-123"', json_str)

        # Test 4: FromStr with enum
        msg_restored = WsMsg.fromStr(json_str)
        self.assertEqual(msg_restored.tsn, "task-123")
        self.assertEqual(msg_restored.type, "progress")
        self.assertEqual(msg_restored.name, "Test Task")
        self.assertEqual(msg_restored.message, "Processing...")
        # Enum might be converted to string in JSON
        self.assertTrue(msg_restored.status == TskStatus.RUNNING or msg_restored.status == "running")

        # Test 5: FromDict with enum value
        dict_with_enum = {
            "tsn": "task-456",
            "type": "complete",
            "name": "Another Task",
            "message": "Done!",
            "status": TskStatus.COMPLETED
        }
        msg_from_dict = WsMsg.fromDict(dict_with_enum)
        self.assertEqual(msg_from_dict.tsn, "task-456")
        self.assertEqual(msg_from_dict.status, TskStatus.COMPLETED)

        # Test 6: FromDict with enum string value
        dict_with_string = {
            "tsn": "task-789",
            "type": "error",
            "name": "Failed Task",
            "message": "Error occurred",
            "status": "failed"
        }
        msg_from_string = WsMsg.fromDict(dict_with_string)
        self.assertEqual(msg_from_string.tsn, "task-789")
        # Check if it can handle string value for enum
        self.assertTrue(msg_from_string.status == TskStatus.FAILED or msg_from_string.status == "failed")

        # Test 7: All enum values
        for status in TskStatus:
            msg = WsMsg(tsn=f"test-{status.value}", status=status)
            json_str = msg.toJson()
            restored = WsMsg.fromStr(json_str)
            self.assertEqual(restored.tsn, f"test-{status.value}")
            # Check status is either enum or string value
            self.assertTrue(restored.status == status or restored.status == status.value)

    def test_wsmsg_optional_fields(self):
        # Test with minimal fields
        msg = WsMsg(tsn="minimal-123")
        self.assertEqual(msg.tsn, "minimal-123")
        self.assertIsNone(msg.type)
        self.assertIsNone(msg.name)
        self.assertIsNone(msg.message)
        self.assertIsNone(msg.status)

        # Convert to JSON and back
        json_str = msg.toJson()
        restored = WsMsg.fromStr(json_str)
        self.assertEqual(restored.tsn, "minimal-123")
        self.assertIsNone(restored.type)
        self.assertIsNone(restored.status)

    def test_wsmsg_fromstr_errors(self):
        # Test invalid JSON
        with self.assertRaises(ValueError) as ctx:
            WsMsg.fromStr("not json")
        self.assertIn("Invalid JSON string", str(ctx.exception))

        # Test non-dict JSON
        with self.assertRaises(ValueError) as ctx:
            WsMsg.fromStr('["array", "not", "dict"]')
        self.assertIn("Expected dict", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
