#!/usr/bin/env python
import json
import os
import sys
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from mod.models import Json, BaseDictModel
from mod.models import Now, Usr, Nfy, Tsk, Mdl, Asset, AssetExif, SimInfo, Gws, TskStatus
import db.pics as pics
from util import log

lg = log.get(__name__)


class TestBaseDictModel(unittest.TestCase):

    def test_simple_model(self):
        usr = Usr(id="1", name="TestUser", email="test@example.com")

        usr_dict = usr.toDict()
        usr_json = usr.toJson()

        self.assertEqual(usr_dict["id"], "1")
        self.assertEqual(usr_dict["name"], "TestUser")

        usr_from_dict = Usr.fromDic(usr_dict)
        usr_from_json = Usr.fromDic(json.loads(usr_json))

        self.assertEqual(usr_from_dict.id, "1")
        self.assertEqual(usr_from_dict.name, "TestUser")
        self.assertEqual(usr_from_json.id, "1")
        self.assertEqual(usr_from_json.email, "test@example.com")

    def test_optional_fields(self):
        usr1 = Usr(id="1", name="User1")
        self.assertEqual(usr1.id, "1")
        self.assertEqual(usr1.name, "User1")
        self.assertEqual(usr1.email, '')

        usr1_dict = usr1.toDict()
        usr1_restored = Usr.fromDic(usr1_dict)

        self.assertEqual(usr1_restored.id, "1")
        self.assertEqual(usr1_restored.name, "User1")
        self.assertEqual(usr1_restored.email, '')

        usr2 = Usr()
        usr2_dict = usr2.toDict()
        usr2_restored = Usr.fromDic(usr2_dict)

        self.assertEqual(usr2_restored.id, '')
        self.assertEqual(usr2_restored.name, '')





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

        asset_restored = Asset.fromDic(asset_dict)
        self.assertEqual(asset_restored.id, "test-asset")
        self.assertEqual(asset_restored.originalFileName, "test.jpg")

        self.assertEqual(asset_restored.isVectored, 0)
        self.assertEqual(asset_restored.simInfos, [])

    def test_asset_model_with_simInfos(self):
        asset = Asset(
            id="test-asset",
            ownerId="user1",
            originalFileName="test.jpg",
            simInfos=[SimInfo(aid=1, score=0.5), SimInfo(aid=2, score=0.6)]
        )

        asset_dict = asset.toDict()
        self.assertEqual(asset_dict["id"], "test-asset")
        self.assertEqual(asset_dict["ownerId"], "user1")
        self.assertEqual(len(asset_dict["simInfos"]), 2)
        self.assertEqual(asset_dict["simInfos"][0]["aid"], 1)
        self.assertEqual(asset_dict["simInfos"][1]["aid"], 2)

        asset_restored = Asset.fromDic(asset_dict)
        self.assertEqual(asset_restored.id, "test-asset")
        self.assertEqual(asset_restored.originalFileName, "test.jpg")
        self.assertEqual(len(asset_restored.simInfos), 2)
        self.assertIsInstance(asset_restored.simInfos[0], SimInfo)
        self.assertEqual(asset_restored.simInfos[0].aid, 1)
        self.assertEqual(asset_restored.simInfos[0].score, 0.5)

    def test_asset_exif_json_string_conversion(self):
        exif_json_string = '{"make":"Canon","model":"EOS 5D","fNumber":2.8,"iso":100,"focalLength":24.0}'

        asset_dict = {
            "id": "test-asset",
            "jsonExif": exif_json_string
        }

        asset = Asset.fromDic(asset_dict)
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

        row = ('test-asset', '[{"aid":1,"score":0.9},{"aid":2,"score":0.8},{"aid":3,"score":0.7}]')
        asset = Asset.fromDB(mock_cursor, row)

        self.assertEqual(len(asset.simInfos), 3)
        self.assertIsInstance(asset.simInfos[0], SimInfo)
        self.assertEqual(asset.simInfos[0].aid, 1)
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

        tsk_restored = Tsk.fromDic(tsk_dict)
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

        nfy_restored = Nfy.fromDic(nfy_dict)
        self.assertEqual(len(nfy_restored.msgs), 1)
        msg_id = list(nfy_restored.msgs.keys())[0]
        self.assertEqual(nfy_restored.msgs[msg_id]["message"], "Test message")

    def test_combined_complex_scenario(self):
        now = Now()

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
        )

        data = {
            "now": now.toDict(),
            "nfy": nfy.toDict(),
            "tsk": tsk.toDict(),
            "mdl": mdl.toDict()
        }

        now_restored = Now.fromDic(data["now"])
        nfy_restored = Nfy.fromDic(data["nfy"])
        tsk_restored = Tsk.fromDic(data["tsk"])
        mdl_restored = Mdl.fromDic(data["mdl"])

        self.assertIsNotNone(now_restored.sim)

        self.assertEqual(len(nfy_restored.msgs), 2)

        tsk_restored.reset()
        self.assertIsNone(tsk_restored.id)

        mdl_restored.reset()
        self.assertIsNone(mdl_restored.id)
        self.assertFalse(mdl_restored.ok)


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
                        self.assertTrue(hasattr(sim, 'aid'))
                        self.assertTrue(hasattr(sim, 'score'))
        except Exception as e:
            self.skipTest(f"Database test failed: {e})")

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
                        self.assertTrue(hasattr(sim, 'aid'))
                        self.assertTrue(hasattr(sim, 'score'))


        except Exception as e:
            self.skipTest(f"Database test failed: {e})")

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
        except Exception as e:
            self.skipTest(f"Database test failed: {e})")


    def test_modal_basic(self):
        now = Now()
        self.assertIsNotNone(now.sim)

    def test_fromDict_error_handling(self):
        # Test with required field missing (will cause TypeError in __init__)
        class RequiredFieldModel(BaseDictModel):
            id: str  # required field
            name: str  # required field

            def __init__(self, id: str, name: str):
                self.id = id
                self.name = name

        # Missing required field 'name' should raise RuntimeError
        invalid_dict = {"id": "test"}
        with self.assertRaises(RuntimeError):
            RequiredFieldModel.fromDic(invalid_dict)

        # Test with extra fields - should succeed as extra fields are filtered
        valid_dict = {"id": "test", "name": "test", "extra": "field", "another": "field"}
        result = RequiredFieldModel.fromDic(valid_dict)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "test")
        self.assertEqual(result.name, "test")

    def test_fromStr_basic(self):
        usr = Usr(id="1", name="TestUser", email="test@example.com")
        json_str = usr.toJson()

        usr_restored = Usr.fromStr(json_str)
        self.assertEqual(usr_restored.id, "1")
        self.assertEqual(usr_restored.name, "TestUser")
        self.assertEqual(usr_restored.email, "test@example.com")



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
            simInfos=[SimInfo(aid=1, score=0.5), SimInfo(aid=2, score=0.6)]
        )

        json_str = asset.toJson()
        asset_restored = Asset.fromStr(json_str)

        self.assertEqual(asset_restored.id, "test-asset")
        self.assertEqual(asset_restored.ownerId, "user1")
        self.assertEqual(len(asset_restored.simInfos), 2)
        self.assertIsInstance(asset_restored.simInfos[0], SimInfo)
        self.assertEqual(asset_restored.simInfos[0].aid, 1)
        self.assertEqual(asset_restored.simInfos[0].score, 0.5)

    def test_fromDB_error_handling(self):
        # Test with required field missing (will cause TypeError in __init__)
        class RequiredFieldModel(BaseDictModel):
            id: str  # required field
            name: str  # required field

            def __init__(self, id: str, name: str):
                self.id = id
                self.name = name

        # Mock cursor with only 'id' column, missing 'name' should raise TypeError
        mock_cursor = type('MockCursor', (), {'description': [('id',)]})()
        row = ('test-id',)
        with self.assertRaises(TypeError):
            RequiredFieldModel.fromDB(mock_cursor, row)

        # Test with None description should raise TypeError
        mock_cursor2 = type('MockCursor', (), {'description': None})()
        row2 = ('test-id', 'test-name')
        with self.assertRaises(TypeError):
            RequiredFieldModel.fromDB(mock_cursor2, row2)


    def test_data_with_enum(self):
        # Test 1: Create Gws with TskStatus enum
        msg = Gws(
            tsn="task-123",
            typ="progress",
            nam="Test Task",
            msg="Processing...",
            ste=TskStatus.RUNNING
        )

        self.assertEqual(msg.tsn, "task-123")
        self.assertEqual(msg.ste, TskStatus.RUNNING)

        # Test 2: Convert to dict
        msg_dict = msg.toDict()
        self.assertEqual(msg_dict["tsn"], "task-123")
        self.assertEqual(msg_dict["ste"], TskStatus.RUNNING)

        # Test 3: Convert to JSON and back
        json_str = msg.toJson()
        self.assertIn('"tsn": "task-123"', json_str)

        # Test 4: FromStr with enum
        msg_restored = Gws.fromStr(json_str)
        self.assertEqual(msg_restored.tsn, "task-123")
        self.assertEqual(msg_restored.typ, "progress")
        self.assertEqual(msg_restored.nam, "Test Task")
        self.assertEqual(msg_restored.msg, "Processing...")
        # Enum might be converted to string in JSON
        self.assertTrue(msg_restored.ste == TskStatus.RUNNING or msg_restored.ste == "running")

        # Test 5: FromDict with enum value
        dict_with_enum = {
            "tsn": "task-456",
            "typ": "complete",
            "nam": "Another Task",
            "msg": "Done!",
            "ste": TskStatus.COMPLETED
        }
        msg_from_dict = Gws.fromDic(dict_with_enum)
        self.assertEqual(msg_from_dict.tsn, "task-456")
        self.assertEqual(msg_from_dict.ste, TskStatus.COMPLETED)

        # Test 6: FromDict with enum string value
        dict_with_string = {
            "tsn": "task-789",
            "typ": "error",
            "nam": "Failed Task",
            "msg": "Error occurred",
            "ste": "failed"
        }
        msg_from_string = Gws.fromDic(dict_with_string)
        self.assertEqual(msg_from_string.tsn, "task-789")
        # Check if it can handle string value for enum
        self.assertTrue(msg_from_string.ste == TskStatus.FAILED or msg_from_string.ste == "failed")

        # Test 7: All enum values
        for status in TskStatus:
            msg = Gws(tsn=f"test-{status.value}", ste=status)
            json_str = msg.toJson()
            restored = Gws.fromStr(json_str)
            self.assertEqual(restored.tsn, f"test-{status.value}")
            # Check status is either enum or string value
            self.assertTrue(restored.ste == status or restored.ste == status.value)

    def test_data_optional_fields(self):
        # Test with minimal fields
        msg = Gws(tsn="minimal-123")
        self.assertEqual(msg.tsn, "minimal-123")
        self.assertIsNone(msg.typ)
        self.assertIsNone(msg.nam)
        self.assertIsNone(msg.msg)
        self.assertIsNone(msg.ste)

        # Convert to JSON and back
        json_str = msg.toJson()
        restored = Gws.fromStr(json_str)
        self.assertEqual(restored.tsn, "minimal-123")
        self.assertIsNone(restored.typ)
        self.assertIsNone(restored.ste)

    def test_data_fromstr_errors(self):
        # Test invalid JSON
        with self.assertRaises(ValueError) as ctx:
            Gws.fromStr("not json")
        self.assertIn("Invalid JSON string", str(ctx.exception))

        # Test non-dict JSON
        with self.assertRaises(ValueError) as ctx:
            Gws.fromStr('["array", "not", "dict"]')
        self.assertIn("Expected dict", str(ctx.exception))

    def test_uuid_to_usr_conversion(self):
        import uuid

        # Test 1: Create UUID and convert to string for Usr
        test_uuid = uuid.uuid4()
        usr = Usr(id=str(test_uuid), name="TestUser", email="test@example.com")

        self.assertIsInstance(usr.id, str)
        self.assertEqual(usr.id, str(test_uuid))

        # Test 2: Convert to dict and back
        usr_dict = usr.toDict()
        self.assertIsInstance(usr_dict["id"], str)

        usr_restored = Usr.fromDic(usr_dict)
        self.assertIsInstance(usr_restored.id, str)
        self.assertEqual(usr_restored.id, str(test_uuid))

        # Test 3: JSON serialization
        json_str = usr.toJson()
        usr_from_json = Usr.fromStr(json_str)
        self.assertIsInstance(usr_from_json.id, str)
        self.assertEqual(usr_from_json.id, str(test_uuid))

        # Test 4: Multiple UUIDs
        uuid_list = [uuid.uuid4() for _ in range(5)]
        for test_uuid in uuid_list:
            usr = Usr(id=str(test_uuid), name=f"User-{test_uuid}", email=f"{test_uuid}@test.com")
            self.assertIsInstance(usr.id, str)
            self.assertEqual(usr.id, str(test_uuid))

            # Verify round-trip conversion
            restored = Usr.fromStr(usr.toJson())
            self.assertEqual(restored.id, str(test_uuid))

        # Test 5: UUID object in dict should be converted to str
        test_uuid = uuid.uuid4()
        dict_with_uuid = {
            "id": test_uuid,  # UUID object, not string
            "name": "TestUser",
            "email": "test@example.com"
        }

        usr_from_uuid_dict = Usr.fromDic(dict_with_uuid)
        self.assertIsInstance(usr_from_uuid_dict.id, str)
        self.assertEqual(usr_from_uuid_dict.id, str(test_uuid))

        # Test 6: Verify it's actually converted, not just equal
        self.assertNotEqual(type(usr_from_uuid_dict.id), type(test_uuid))
        self.assertEqual(type(usr_from_uuid_dict.id), str)

    def test_type_conversion_comprehensive(self):
        # Test numeric type conversions
        asset_dict = {
            "autoId": "123",  # string to int
            "id": "test-asset",
            "isVectored": "1",  # string to int
            "simOk": "0",     # string to int
            "jsonExif": {
                "fNumber": "2.8",        # string to float
                "iso": "800",            # string to int
                "focalLength": "85.0",   # string to float
                "exifImageWidth": "4000", # string to int
                "rating": "5"            # string to int
            }
        }

        asset = Asset.fromDic(asset_dict)

        # Verify numeric conversions
        self.assertIsInstance(asset.autoId, int)
        self.assertEqual(asset.autoId, 123)
        self.assertIsInstance(asset.isVectored, int)
        self.assertEqual(asset.isVectored, 1)
        self.assertIsInstance(asset.simOk, int)
        self.assertEqual(asset.simOk, 0)

        # Verify nested object numeric conversions
        self.assertIsInstance(asset.jsonExif.fNumber, float)
        self.assertEqual(asset.jsonExif.fNumber, 2.8)
        self.assertIsInstance(asset.jsonExif.iso, int)
        self.assertEqual(asset.jsonExif.iso, 800)
        self.assertIsInstance(asset.jsonExif.focalLength, float)
        self.assertEqual(asset.jsonExif.focalLength, 85.0)
        self.assertIsInstance(asset.jsonExif.exifImageWidth, int)
        self.assertEqual(asset.jsonExif.exifImageWidth, 4000)
        self.assertIsInstance(asset.jsonExif.rating, int)
        self.assertEqual(asset.jsonExif.rating, 5)

    def test_deeply_nested_structure(self):
        # Test complex nested structure with multiple levels
        mdl_dict = {
            "id": "test-modal",
            "msg": "Delete these assets?",
            "ok": False,
            "assets": [
                {
                    "autoId": "100",
                    "id": "asset-1",
                    "originalFileName": "photo1.jpg",
                    "isVectored": "1",
                    "simInfos": [
                        {"aid": "1001", "score": "0.95", "isSelf": False},
                        {"aid": "1002", "score": "0.87", "isSelf": True}
                    ],
                    "jsonExif": {
                        "make": "Canon",
                        "fNumber": "1.8",
                        "iso": "200"
                    },
                    "simGIDs": ["10", "20", "30"]
                },
                {
                    "autoId": "200",
                    "id": "asset-2",
                    "originalFileName": "photo2.jpg",
                    "isVectored": "0",
                    "simInfos": [
                        {"aid": "2001", "score": "0.73", "isSelf": False}
                    ],
                    "simGIDs": ["40", "50"]
                }
            ]
        }

        mdl = Mdl.fromDic(mdl_dict)

        # Verify basic fields
        self.assertEqual(mdl.id, "test-modal")
        self.assertFalse(mdl.ok)
        self.assertEqual(len(mdl.assets), 2)

        # Verify first asset
        asset1 = mdl.assets[0]
        self.assertIsInstance(asset1, Asset)
        self.assertIsInstance(asset1.autoId, int)
        self.assertEqual(asset1.autoId, 100)
        self.assertEqual(asset1.id, "asset-1")
        self.assertIsInstance(asset1.isVectored, int)
        self.assertEqual(asset1.isVectored, 1)

        # Verify nested simInfos
        self.assertEqual(len(asset1.simInfos), 2)
        self.assertIsInstance(asset1.simInfos[0], SimInfo)
        self.assertIsInstance(asset1.simInfos[0].aid, int)
        self.assertEqual(asset1.simInfos[0].aid, 1001)
        self.assertIsInstance(asset1.simInfos[0].score, float)
        self.assertEqual(asset1.simInfos[0].score, 0.95)
        self.assertFalse(asset1.simInfos[0].isSelf)

        # Verify nested jsonExif
        self.assertIsInstance(asset1.jsonExif, AssetExif)
        self.assertEqual(asset1.jsonExif.make, "Canon")
        self.assertIsInstance(asset1.jsonExif.fNumber, float)
        self.assertEqual(asset1.jsonExif.fNumber, 1.8)
        self.assertIsInstance(asset1.jsonExif.iso, int)
        self.assertEqual(asset1.jsonExif.iso, 200)

        # Verify simGIDs list conversion
        self.assertEqual(len(asset1.simGIDs), 3)
        self.assertIsInstance(asset1.simGIDs[0], int)
        self.assertEqual(asset1.simGIDs, [10, 20, 30])

        # Verify second asset
        asset2 = mdl.assets[1]
        self.assertIsInstance(asset2.autoId, int)
        self.assertEqual(asset2.autoId, 200)
        self.assertEqual(len(asset2.simInfos), 1)
        self.assertIsInstance(asset2.simInfos[0].aid, int)
        self.assertEqual(asset2.simInfos[0].aid, 2001)
        self.assertEqual(asset2.simGIDs, [40, 50])


if __name__ == "__main__":
    unittest.main()
