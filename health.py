# health.py - Health check endpoint handler
import json
import logging
import azure.functions as func
from data_loader import data_loader

class HealthFunction:
    """Handler for health check endpoint"""

    def handle(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Handle health check request

        Returns system status and statistics
        """
        try:
            # Check if data is loaded (but don't load it during health check)
            is_loaded = data_loader.cb_model is not None

            # Get statistics
            stats = {
                "status": "healthy",
                "data_loaded": is_loaded,
                "total_users": len(data_loader.user_ids) if is_loaded and data_loader.user_ids else 0,
                "total_articles": len(data_loader.df_articles) if is_loaded and data_loader.df_articles is not None else 0,
                "total_ratings": len(data_loader.df_ratings) if is_loaded and data_loader.df_ratings is not None else 0
            }

            return func.HttpResponse(
                json.dumps(stats),
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Error in health endpoint: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "error": str(e),
                    "trace": traceback.format_exc()
                }),
                status_code=500,
                mimetype="application/json"
            )
