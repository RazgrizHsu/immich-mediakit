import functools
import traceback
from dash import callback_context
from util import log

lg = log.get(__name__)

def injectCallbacks(app):
    """Add error handling for all Dash callbacks"""

    ocb = app.callback

    def newCB(*args, **kwargs):
        fn = ocb(*args, **kwargs)

        def fnOnWarp(func):
            @functools.wraps(func)
            def wrapped_func(*func_args, **func_kwargs):
                try:
                    return func(*func_args, **func_kwargs)
                except Exception as e:
                    # Get current triggered callback information
                    ctx = callback_context
                    trigger = ctx.triggered[0] if ctx.triggered else "Unknown trigger source"

                    # Log detailed error
                    error_msg = f"Callback error: {str(e)}"
                    stack_trace = traceback.format_exc()
                    lg.error(f"{error_msg}\nTrigger source: {trigger}\n{stack_trace}")

                    # Show notification
                    # notify.error( f"Operation failed: {str( e )}" )

                    # Return no_update to keep UI unchanged
                    from dash import no_update
                    return no_update

            # Apply original decorator to wrapped function
            return fn(wrapped_func)

        return fnOnWarp

    # Replace original callback method
    app.callback = newCB
