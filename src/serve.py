import os
from flask import send_file, request, make_response, Response
from flask_caching import Cache
import redis

from conf import envs, ks
from util import log

lg = log.get(__name__)

TIMEOUT = 2592000 #30day


def regBy(app):
    import db

    cache = Cache(app.server, config={
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': envs.redisUrl,
        'CACHE_DEFAULT_TIMEOUT': TIMEOUT,
        'CACHE_KEY_PREFIX': 'img:'
    })

    redis_client = redis.from_url(envs.redisUrl)

    noimg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/noimg.png")

    #----------------------------------------------------------------
    # serve for viewGrid
    #----------------------------------------------------------------
    @app.server.route('/api/img/<assetId>')
    def serve_image(assetId):
        try:
            photoQ = request.args.get('q', ks.db.thumbnail)
            cache_key = f"img:{assetId}_{photoQ}"

            cached_data = redis_client.get(cache_key)
            if cached_data:
                lg.debug(f"[api:img] cache hit for {assetId}")
                rep = make_response(Response(cached_data, mimetype='image/jpeg'))
                rep.headers['Cache-Control'] = 'public, max-age=31536000'  # client 1year
                return rep

            conn = db.pics.getConn()
            cursor = conn.cursor()
            cursor.execute("Select thumbnail_path, preview_path, fullsize_path From assets Where id = ?", [assetId])
            row = cursor.fetchone()

            if row:
                if photoQ == ks.db.preview: path = row[1]
                elif photoQ == ks.db.fullsize: path = row[2]
                else: path = row[0]

                if path:
                    full_path = os.path.join(envs.immichPath, path)
                    if os.path.exists(full_path):
                        lg.info(f"[api:img] loading img id[{assetId}] path[{full_path}]")

                        with open(full_path, 'rb') as f: img_data = f.read()

                        redis_client.setex(cache_key, TIMEOUT, img_data)

                        rep = make_response(Response(img_data, mimetype='image/jpeg'))
                        rep.headers['Cache-Control'] = 'public, max-age=31536000'
                        return rep

            return send_file(noimg_path, mimetype='image/png')

        except Exception as e:
            lg.error(f"Error serving image: {str(e)}")
            return send_file(noimg_path, mimetype='image/png')


    #----------------------------------------------------------------
    # for clear cache
    #----------------------------------------------------------------
    @app.server.route('/api/cache/clear')
    def clear_cache():
        try:
            pattern = 'img:*'
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                return {'status': 'success', 'cleared': len(keys)}
            return {'status': 'success', 'cleared': 0}
        except Exception as e:
            lg.error(f"Error clearing cache: {str(e)}")
            return {'status': 'error', 'message': str(e)}
