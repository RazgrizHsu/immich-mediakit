#!/usr/bin/env python
import os
import sys
import json
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from util import log
from mod import models
from conf import ks, co
import db

lg = log.get(__name__)

db.init()

class TestBase(unittest.TestCase):
    def test_base(self):
        lg.info("ok")

    def test_code(self):
        mdl = models.Mdl()

        mdl.id = ks.pg.fetch
        mdl.cmd = ks.cmd.fetch.asset
        mdl.args = {'a': 'what?'}

        tsk = mdl.mkTsk()
        if not tsk: self.fail("no task")

        self.assertEqual(mdl.id, tsk.id)
        self.assertEqual(mdl.cmd, tsk.cmd)
        self.assertEqual(mdl.args, tsk.args)
        lg.info(f"mdl: {mdl}")
        lg.info(f"tsk: {tsk}")

        self.assertEqual(tsk.name, ks.pg.fetch.name)

        tit = ks.pg.find(tsk.id)
        self.assertIsNotNone(tit, f'NotFound id[{tsk.id}]')

        if tit:
            lg.info(f'tit.cmds.fetch: {tit}')


        class a(co.to):
            a = 1
            b = 2

        lg.info(f"a.to: {a.dict()}")


    def test_sim_nonFinish(self):
        asset = db.pics.getAnySimPending()

        lg.info(f"asset: {asset}")

        if not asset:
            return

        for idx, info in enumerate(asset.simInfos):
            aid, score = info.toTuple()
            lg.info(f"  Similar pair {idx + 1}: ID[{aid}], score[{score:.6f}]")

    def test_sim(self):
        asset = db.pics.getAnyNonSim()
        lg.info(f"asset: {asset}")

        infos = db.vecs.findSimiliar(asset.id, 0.8, 1.0)

        simIds = [i.id for i in infos]

        lg.info(f"Found {len(simIds)} similar, ids: {simIds}")

        # select back all simIds assets
        # db.pics.get()

        for idx, info in enumerate(infos):
            aid, score = info.toTuple()
            lg.info(f"  Similar pair {idx + 1}: ID[{aid}], score[{score:.6f}]")


    def test_empty(self):
        # 取得 pending 計數
        pendingCount = db.pics.countSimPending()
        lg.info(f"\ncountSimPending: {pendingCount}")

        # 取得第一頁資料
        pageSize = 10
        page1 = db.pics.getPendingPaged(1, pageSize)
        lg.info(f"\ngetPendingPaged(1, {pageSize}) returned {len(page1)} records")

        # 顯示每個資產的資訊
        for idx, asset in enumerate(page1):
            lg.info(f"\nAsset {idx+1}: {asset.id}")
            lg.info(f"  simInfos count: {len(asset.simInfos)}")
            lg.info(f"  autoId: {asset.autoId}")

            # 顯示 simInfos 的前幾個
            for i, si in enumerate(asset.simInfos[:3]):
                lg.info(f"    simInfo[{i}]: id={si.id}, score={si.score:.3f}, isSelf={si.isSelf}")
            if len(asset.simInfos) > 3:
                lg.info(f"    ... and {len(asset.simInfos) - 3} more")

            # 顯示 relatAssets
            if hasattr(asset, 'relats') and asset.relats:
                lg.info(f"  Related assets ({len(asset.relats)}):")
                for ra in asset.relats[:2]:
                    lg.info(f"    - {ra.id} (simInfos: {len(ra.simInfos)})")
                if len(asset.relats) > 2:
                    lg.info(f"    ... and {len(asset.relats) - 2} more")
            else:
                lg.info("  No related assets")

        # 測試分頁功能
        totalPages = (pendingCount + pageSize - 1) // pageSize
        lg.info(f"\nTotal pages: {totalPages}")

        # 驗證計數與實際資料筆數一致
        allPagedAssets = []
        for page in range(1, min(totalPages + 1, 4)):  # 只測前3頁
            data = db.pics.getPendingPaged(page, pageSize)
            allPagedAssets.extend(data)
            lg.info(f"Page {page}: {len(data)} records")

        # 驗證沒有重複資料
        uniqueIds = set(asset.id for asset in allPagedAssets)
        if len(uniqueIds) != len(allPagedAssets):
            lg.error(f"ERROR: Found duplicate assets in paged results!")
        else:
            lg.info(f"\nSUCCESS: No duplicates in {len(allPagedAssets)} paged records")

        # 驗證排序（simInfos 數量多的在前）
        for i in range(1, len(page1)):
            if len(page1[i-1].simInfos) < len(page1[i].simInfos):
                lg.error(f"ERROR: Sorting issue at index {i}")
                break
        else:
            lg.info("SUCCESS: Records are sorted by simInfos count (descending)")


    def test_simGID_integrity(self):
        lg.info("\n=== Starting simGID integrity test ===")

        conn = db.pics.mkConn()
        c = conn.cursor()

        # 1. 驗證所有 simOk=0 且有 simInfos 的資產都有 simGID
        lg.info("\n1. Checking simGID existence for simOk=0 assets...")
        c.execute("""
            SELECT id, simGID, json_array_length(simInfos) as infoCnt
            FROM assets 
            WHERE simOk = 0 AND json_array_length(simInfos) > 0 AND simGID IS NULL
        """)
        noGID = c.fetchall()
        if noGID:
            lg.error(f"ERROR: Found {len(noGID)} assets with simOk=0 and simInfos but no simGID:")
            for row in noGID[:5]:
                lg.error(f"  - ID: {row[0]}, simInfos count: {row[2]}")
        else:
            lg.info("SUCCESS: All simOk=0 assets with simInfos have simGID")

        # 2. 驗證群組代表存在性
        lg.info("\n2. Checking group representative existence...")
        c.execute("""
            SELECT a.id, a.simGID, a.autoId
            FROM assets a
            WHERE a.simGID IS NOT NULL 
            AND a.simGID != a.autoId
            AND NOT EXISTS (
                SELECT 1 FROM assets rep 
                WHERE rep.autoId = a.simGID
            )
        """)
        orphanGrp = c.fetchall()
        if orphanGrp:
            lg.error(f"ERROR: Found {len(orphanGrp)} assets with non-existent group representative:")
            for row in orphanGrp[:5]:
                lg.error(f"  - ID: {row[0]}, simGID: {row[1]}, autoId: {row[2]}")
        else:
            lg.info("SUCCESS: All group representatives exist")

        # 3. 驗證高相似度連接的群組一致性
        lg.info("\n3. Checking high similarity group consistency...")
        c.execute("""
            SELECT id, simGID, simInfos FROM assets 
            WHERE simOk = 0 AND json_array_length(simInfos) > 1
        """)

        badGrpCnt = 0
        for row in c.fetchall():
            aId, gid, simJson = row
            sims = json.loads(simJson) if simJson else []

            highSimIds = [s['id'] for s in sims if s.get('score', 0) > 0.9 and s.get('id') != aId]
            if not highSimIds: continue

            c2 = conn.cursor()
            ph = ','.join(['?' for _ in highSimIds])
            c2.execute(f"SELECT id, simGID FROM assets WHERE id IN ({ph})", highSimIds)

            for sId, sGid in c2.fetchall():
                if sGid != gid:
                    badGrpCnt += 1
                    if badGrpCnt <= 5:
                        lg.error(f"ERROR: Asset {aId} (GID:{gid}) highly similar to {sId} (GID:{sGid}) but different groups")

        if badGrpCnt:
            lg.error(f"ERROR: Found {badGrpCnt} high similarity pairs in different groups")
        else:
            lg.info("SUCCESS: All high similarity assets are in same groups")

        # 4. 驗證 getPendingPaged 覆蓋性
        lg.info("\n4. Checking getPendingPaged coverage...")

        # 取得所有需要處理的資產總數
        c.execute("""
            SELECT COUNT(*) FROM assets 
            WHERE simOk = 0 AND json_array_length(simInfos) > 1
        """)
        totalNeeded = c.fetchone()[0]

        # 取得透過 getPendingPaged 能覆蓋的資產
        pndCnt = db.pics.countSimPending()
        pageSize = 100
        totalPages = (pndCnt + pageSize - 1) // pageSize

        allCoveredIds = set()
        for page in range(1, totalPages + 1):
            leaders = db.pics.getPendingPaged(page, pageSize)
            for leader in leaders:
                allCoveredIds.add(leader.id)
                for sim in leader.simInfos:
                    if sim.id and not sim.isSelf:
                        allCoveredIds.add(sim.id)

        # 檢查是否有遺漏
        c.execute("""
            SELECT id FROM assets 
            WHERE simOk = 0 AND json_array_length(simInfos) > 1
        """)
        allNeedIds = set(row[0] for row in c.fetchall())

        missed = allNeedIds - allCoveredIds
        if missed:
            lg.error(f"ERROR: getPendingPaged missed {len(missed)} assets:")
            for mId in list(missed)[:5]:
                c.execute("SELECT simGID, autoId FROM assets WHERE id = ?", (mId,))
                row = c.fetchone()
                lg.error(f"  - ID: {mId}, simGID: {row[0]}, autoId: {row[1]}")
        else:
            lg.info(f"SUCCESS: getPendingPaged covers all {len(allNeedIds)} assets needing processing")

        # 總結報告
        lg.info("\n=== Test Summary ===")
        lg.info(f"Total assets needing processing: {totalNeeded}")
        lg.info(f"Group count (countSimPending): {pndCnt}")
        lg.info(f"Coverage through getPendingPaged: {len(allCoveredIds)} assets")

        # 檢查群組分佈
        c.execute("""
            SELECT simGID, COUNT(*) as cnt 
            FROM assets 
            WHERE simGID IS NOT NULL 
            GROUP BY simGID 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        lg.info("\nTop 10 largest groups:")
        for gid, cnt in c.fetchall():
            lg.info(f"  - Group {gid}: {cnt} members")


if __name__ == "__main__":
    unittest.main()
