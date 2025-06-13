import hashlib
import os
from flask import send_file, request, make_response
from flask_caching import Cache

from conf import envs, ks, pathCache
from util import log

lg = log.get(__name__)

TIMEOUT = (60 * 60 * 24) * 30  #30day

CacheBrowserSecs = 60


def regBy(app):
    import db

    dirCache = os.path.abspath(os.path.join(pathCache, 'imgs'))

    cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': dirCache,
        'CACHE_DEFAULT_TIMEOUT': TIMEOUT,
        'CACHE_THRESHOLD': 300,
    })

    noimg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/noimg.png")


    #----------------------------------------------------------------
    # serve for Image
    #----------------------------------------------------------------
    @app.server.route('/api/img/<aid>')
    def serve_image(aid):
        try:
            photoQ = request.args.get('q', ks.db.thumbnail)

            cache_key = f"{aid}_{photoQ}"
            cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
            cache_path = os.path.abspath(os.path.join(dirCache, f"{cache_hash}.jpg"))

            if os.path.exists(cache_path):
                rep = make_response(send_file(cache_path, mimetype='image/jpeg'))
                rep.headers['Cache-Control'] = f'public, max-age={CacheBrowserSecs}'  # client 1year
                return rep

            with db.pics.mkConn() as conn:
                cursor = conn.cursor()
                cursor.execute("Select thumbnail_path, preview_path, fullsize_path From assets Where autoId = ?", [aid])
                row = cursor.fetchone()

                if row:
                    if photoQ == ks.db.preview: path = row[1]
                    elif photoQ == ks.db.fullsize: path = row[2]
                    else:
                        path = row[0]

                    if path:
                        path = os.path.join(envs.immichPath, path)
                        if os.path.exists(path):
                            # lg.info(f"[api:img] get img cache id[{assetId}] path[{path}]")
                            with open(cache_path, 'wb') as f:
                                with open(path, 'rb') as src: f.write(src.read())

                            rep = make_response(send_file(cache_path, mimetype='image/jpeg'))
                            rep.headers['Cache-Control'] = f'public, max-age={CacheBrowserSecs}'
                            return rep

            return send_file(noimg_path, mimetype='image/png')

        except Exception as e:
            lg.error(f"Error serving image: {str(e)}")
            return send_file(noimg_path, mimetype='image/png')

    #----------------------------------------------------------------
    # serve for LivePhoto Video
    #----------------------------------------------------------------
    @app.server.route('/api/livephoto/<aid>')
    def serve_livephoto(aid):
        try:
            cache_key = f"lp_{aid}"
            cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
            cache_path = os.path.abspath(os.path.join(dirCache, f"{cache_hash}.mov"))

            if os.path.exists(cache_path):
                rep = make_response(send_file(cache_path, mimetype='video/quicktime'))
                rep.headers['Cache-Control'] = f'public, max-age={CacheBrowserSecs}'
                return rep

            with db.pics.mkConn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT livephoto_path FROM assets WHERE autoId = ?", [aid])
                row = cursor.fetchone()

                if row and row[0]:
                    livephoto_path = row[0]
                    full_path = os.path.join(envs.immichPath, livephoto_path)

                    if os.path.exists(full_path):
                        lg.info(f"[api:livephoto] serving livephoto {aid} from {full_path}")

                        with open(cache_path, 'wb') as f:
                            with open(full_path, 'rb') as src:
                                f.write(src.read())

                        rep = make_response(send_file(cache_path, mimetype='video/quicktime'))
                        rep.headers['Cache-Control'] = f'public, max-age={CacheBrowserSecs}'
                        return rep

            lg.warn(f"[api:livephoto] LivePhoto not found for asset {aid}")
            return "", 404

        except Exception as e:
            lg.error(f"Error serving livephoto: {str(e)}")
            return "", 500
