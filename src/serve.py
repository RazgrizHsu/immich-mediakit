import os
from flask import send_file, request, make_response
from flask_caching import Cache
import hashlib

from conf import envs, Ks, pathCache
from util import log

lg = log.get(__name__)


def regBy(app):
    import db

    cache_dir = os.path.abspath(os.path.join(pathCache, 'imgs'))
    os.makedirs(cache_dir, exist_ok=True)
    lg.info(f"[serve] cacheDir[{cache_dir}]")

    cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': cache_dir,
        'CACHE_DEFAULT_TIMEOUT': 2592000,  # 30 day
        'CACHE_THRESHOLD': 1000
    })

    noimg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/noimg.png")

    # ----------------------------------------------------------------
    # serve for viewGrid
    # ----------------------------------------------------------------
    @app.server.route('/api/img/<assetId>')
    def serve_image(assetId):
        try:
            photoQ = request.args.get('q', Ks.db.thumbnail)

            cache_key = f"{assetId}_{photoQ}"
            cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
            cache_path = os.path.abspath(os.path.join(cache_dir, f"{cache_hash}.jpg"))

            if os.path.exists(cache_path):
                rep = make_response(send_file(cache_path, mimetype='image/jpeg'))
                rep.headers['Cache-Control'] = 'public, max-age=31536000'  # client 1year
                return rep

            conn = db.pics.mkconn()
            cursor = conn.cursor()
            cursor.execute("Select thumbnail_path, preview_path, fullsize_path From assets Where id = ?", [assetId])
            row = cursor.fetchone()

            if row:
                if photoQ == Ks.db.preview: path = row[1]
                elif photoQ == Ks.db.fullsize: path = row[2]
                else:
                    path = row[0]

                if path:
                    path = os.path.join(envs.immichPath, path)
                    if os.path.exists(path):
                        lg.info( f"[api:img] get img cache id[{assetId}] path[{path}]")
                        with open(cache_path, 'wb') as f:
                            with open(path, 'rb') as src:
                                f.write(src.read())

                        rep = make_response(send_file(cache_path, mimetype='image/jpeg'))
                        rep.headers['Cache-Control'] = 'public, max-age=31536000'
                        return rep

            return send_file(noimg_path, mimetype='image/png')

        except Exception as e:
            lg.error(f"Error serving image: {str(e)}")
            return send_file(noimg_path, mimetype='image/png')
