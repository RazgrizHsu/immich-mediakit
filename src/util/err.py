import functools
import traceback
from dash import callback_context, no_update
from util import log

lg = log.get(__name__)

def injectCallbacks(app):

    ocb = app.callback

    def newCB(*args, **kwargs):
        fn = ocb(*args, **kwargs)

        def fnOnWarp(func):
            @functools.wraps(func)
            def wrapped_func(*func_args, **func_kwargs):
                try:
                    return func(*func_args, **func_kwargs)
                except Exception as e:
                    ctx = callback_context
                    trigger = ctx.triggered[0] if ctx.triggered else "Unknown trigger source"

                    error_msg = f"[CallBack] ERR: {str(e)}"
                    stack_trace = traceback.format_exc()
                    lg.error(f"{error_msg}\nTrigger source: {trigger}\n{stack_trace}")


                    return no_update

            return fn(wrapped_func)

        return fnOnWarp

    app.callback = newCB
