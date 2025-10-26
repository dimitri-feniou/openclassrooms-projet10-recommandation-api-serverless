# recommend.py - Recommendation endpoint handler
import json
import logging
import azure.functions as func
from data_loader import data_loader

class RecommendFunction:
    """Handler for recommendation endpoint"""

    def handle(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Handle recommendation request

        Query parameters:
        - user_id (required): User ID
        - n (optional): Number of recommendations (default: 5)
        - with_meta (optional): Include article metadata (default: false)
        """
        try:
            # Load data if not already loaded
            data_loader.load_data()

            # Get parameters
            user_id = req.params.get("user_id")
            n = int(req.params.get("n", 5))
            with_meta = req.params.get("with_meta", "false").lower() == "true"

            # Validate user_id
            if not user_id:
                return func.HttpResponse(
                    json.dumps({"error": "user_id parameter is required"}),
                    status_code=400,
                    mimetype="application/json"
                )

            user_id = int(user_id)

            # Check if user exists
            if user_id not in data_loader.user_ids:
                return func.HttpResponse(
                    json.dumps({"error": f"User {user_id} not found"}),
                    status_code=404,
                    mimetype="application/json"
                )

            # Get recommendations
            logging.info(f"Getting {n} recommendations for user {user_id}")
            recommendations = data_loader.cb_model.recommend(
                user_id,
                data_loader.df_ratings,
                n=n
            )

            # Format response
            result = []
            for article_id, score in recommendations:
                rec = {
                    "article_id": int(article_id),
                    "score": round(float(score), 4)
                }

                # Add metadata if requested
                if with_meta:
                    article_info = data_loader.df_articles[
                        data_loader.df_articles["article_id"] == article_id
                    ]
                    if not article_info.empty:
                        article_row = article_info.iloc[0]
                        rec["category_id"] = str(article_row.get("category_id", "N/A"))
                        rec["words_count"] = int(article_row.get("words_count", 0))

                result.append(rec)

            logging.info(f"Returning {len(result)} recommendations")

            return func.HttpResponse(
                json.dumps(result),
                mimetype="application/json"
            )

        except ValueError as e:
            logging.error(f"Validation error: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": str(e)}),
                status_code=400,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Error in recommend endpoint: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({"error": "Internal server error", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )
