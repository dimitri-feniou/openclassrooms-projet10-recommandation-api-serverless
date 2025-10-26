# function_app.py - Main Azure Functions application
import os
import json
import logging
import azure.functions as func

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting Azure Functions application initialization...")

try:
    from recommend import RecommendFunction
    logging.info("Successfully imported RecommendFunction")
except Exception as e:
    logging.error(f"Failed to import RecommendFunction: {str(e)}")
    raise

try:
    from users import UsersFunction
    logging.info("Successfully imported UsersFunction")
except Exception as e:
    logging.error(f"Failed to import UsersFunction: {str(e)}")
    raise

try:
    from health import HealthFunction
    logging.info("Successfully imported HealthFunction")
except Exception as e:
    logging.error(f"Failed to import HealthFunction: {str(e)}")
    raise

# Create Function App instance
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logging.info("Function App instance created")

# Initialize function handlers
try:
    recommend_handler = RecommendFunction()
    users_handler = UsersFunction()
    health_handler = HealthFunction()
    logging.info("All function handlers initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize handlers: {str(e)}")
    import traceback
    logging.error(traceback.format_exc())
    raise

@app.route(route="recommend", methods=["GET"])
def recommend(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to get article recommendations for a user

    Query parameters:
    - user_id (required): User ID to get recommendations for
    - n (optional): Number of recommendations to return (default: 5)

    Returns:
    - JSON array of recommended articles with scores
    """
    logging.info('Processing recommendation request')
    return recommend_handler.handle(req)

@app.route(route="users", methods=["GET"])
def users(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to get list of users with statistics

    Returns:
    - JSON array of users with their stats (number of articles, avg rating)
    """
    logging.info('Processing users list request')
    return users_handler.handle(req)

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for health check

    Returns:
    - JSON with system status and statistics
    """
    logging.info('Processing health check request')
    return health_handler.handle(req)
