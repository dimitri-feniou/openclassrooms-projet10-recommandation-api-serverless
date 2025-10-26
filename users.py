# users.py - Users endpoint handler
import json
import logging
import azure.functions as func
from data_loader import data_loader

class UsersFunction:
    """Handler for users endpoint"""

    def handle(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Handle users list request

        Query parameters:
        - limit (optional): Limit number of results
        - offset (optional): Offset for pagination
        """
        try:
            # Try to load data
            try:
                data_loader.load_data()
            except Exception as load_error:
                logging.error(f"Failed to load data: {str(load_error)}")
                # Return error with helpful message
                return func.HttpResponse(
                    json.dumps({
                        "error": "Data loading failed",
                        "details": str(load_error),
                        "message": "The application is running on a Consumption plan with limited memory. Please consider upgrading to a Premium plan or reducing data size."
                    }),
                    status_code=503,
                    mimetype="application/json"
                )

            # Get pagination parameters
            limit = req.params.get("limit")
            offset = req.params.get("offset", 0)

            if limit:
                limit = int(limit)
            if offset:
                offset = int(offset)

            # Get user stats
            df_stats = data_loader.df_user_stats

            # Apply pagination if requested
            if limit:
                df_stats = df_stats.iloc[offset:offset + limit]

            # Convert to list of dictionaries
            users_data = df_stats.to_dict("records")

            logging.info(f"Returning {len(users_data)} users")

            return func.HttpResponse(
                json.dumps(users_data),
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Error in users endpoint: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({"error": "Internal server error", "details": str(e), "trace": traceback.format_exc()}),
                status_code=500,
                mimetype="application/json"
            )
