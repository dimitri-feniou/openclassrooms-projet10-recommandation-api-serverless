# data_loader.py - Data loading and model initialization
import os
import io
import pickle
import logging
import numpy as np
import pandas as pd
from azure.storage.blob import BlobServiceClient
from content_based import ContentBasedRecommender

class DataLoader:
    """
    Singleton class to load and cache data from Azure Blob Storage
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not DataLoader._initialized:
            self.cb_model = None
            self.df_ratings = None
            self.df_articles = None
            self.df_user_stats = None
            self.user_ids = None
            DataLoader._initialized = True

    def load_data(self):
        """
        Load data from Azure Blob Storage and initialize recommendation model
        """
        if self.cb_model is not None:
            logging.info("Data already loaded, using cached version")
            return

        logging.info("=" * 60)
        logging.info("STARTING DATA LOAD PROCESS")
        logging.info("=" * 60)

        try:
            # Get Azure Storage connection details from environment variables
            connection_string = os.environ.get("AzureWebJobsStorage")
            container_name = os.environ.get("STORAGE_CONTAINER", "data")

            if not connection_string:
                raise ValueError("AzureWebJobsStorage connection string not found")

            logging.info(f"Connecting to Azure Blob Storage, container: {container_name}")

            # Initialize blob service client
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(container_name)

            # Check if we should limit data for memory constraints
            limit_data = os.environ.get("LIMIT_DATA_SIZE", "false").lower() == "true"

            # Load clicks data
            logging.info("Loading clicks data...")
            df_clicks = self._load_csv_from_blob(container_client, "clicks.csv")

            if limit_data:
                logging.warning("LIMIT_DATA_SIZE is enabled - loading subset of data")
                # Limit to top users by activity
                top_users = df_clicks["user_id"].value_counts().head(500).index
                df_clicks = df_clicks[df_clicks["user_id"].isin(top_users)]
                logging.info(f"Limited to {len(top_users)} most active users")

            # Load articles metadata
            logging.info("Loading articles metadata...")
            df_articles = self._load_csv_from_blob(container_client, "articles_metadata.csv")

            # Load embeddings
            logging.info("Loading article embeddings...")
            try:
                embeddings = self._load_pickle_from_blob(container_client, "articles_embeddings_reduced.pickle")
                logging.info(f"Embeddings loaded: type={type(embeddings)}")
            except MemoryError as e:
                logging.error(f"MemoryError loading embeddings: {str(e)}")
                raise Exception("Not enough memory to load embeddings. Consider upgrading to Azure Functions Premium plan.")

            # Prepare ratings data
            logging.info("Preparing ratings data...")
            df_ratings = self._prepare_ratings(df_clicks)

            # Prepare embeddings matrix
            logging.info("Preparing embeddings matrix...")
            article_ids, emb_matrix, indices = self._prepare_embeddings(embeddings, df_articles)

            # Initialize and train model
            logging.info("Initializing recommendation model...")
            cb_model = ContentBasedRecommender(emb_matrix, indices, article_ids)
            cb_model.fit(df_ratings)

            # Calculate user statistics
            logging.info("Calculating user statistics...")
            df_user_stats = self._calculate_user_stats(df_ratings)

            # Store in instance variables
            self.cb_model = cb_model
            self.df_ratings = df_ratings
            self.df_articles = df_articles
            self.df_user_stats = df_user_stats
            self.user_ids = sorted(df_ratings["user_id"].unique().tolist())

            logging.info(f"Data loaded successfully! {len(self.user_ids)} users, {len(df_articles)} articles")
            logging.info("=" * 60)
            logging.info("DATA LOAD COMPLETE")
            logging.info("=" * 60)

        except Exception as e:
            logging.error("=" * 60)
            logging.error(f"CRITICAL ERROR LOADING DATA: {str(e)}")
            logging.error("=" * 60)
            import traceback
            logging.error(traceback.format_exc())
            raise

    def _load_csv_from_blob(self, container_client, blob_name):
        """Load CSV file from blob storage"""
        try:
            blob_client = container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            data = io.BytesIO(download_stream.readall())
            df = pd.read_csv(data)
            logging.info(f"Loaded {blob_name}: {len(df)} rows")
            return df
        except Exception as e:
            logging.error(f"Error loading {blob_name}: {str(e)}")
            raise

    def _load_pickle_from_blob(self, container_client, blob_name):
        """Load pickle file from blob storage"""
        try:
            blob_client = container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            binary_data = download_stream.readall()
            data = pickle.loads(binary_data)
            logging.info(f"Loaded {blob_name}, type: {type(data)}")
            return data
        except Exception as e:
            logging.error(f"Error loading {blob_name}: {str(e)}")
            raise

    def _prepare_ratings(self, df_clicks):
        """Create implicit ratings from click data"""
        df = df_clicks.copy()
        df["session_size"] = pd.to_numeric(df["session_size"], errors="coerce")
        df.dropna(subset=["session_size"], inplace=True)
        df["log_session_size"] = np.log1p(df["session_size"])
        q25, q75 = df["log_session_size"].quantile([0.25, 0.75])

        df_ratings = df[["user_id", "article_id"]].copy()
        df_ratings["rating"] = df["log_session_size"].apply(
            lambda x: 1 if x <= q25 else 2 if x <= q75 else 3
        )

        logging.info(f"Prepared {len(df_ratings)} ratings")
        return df_ratings

    def _prepare_embeddings(self, embeddings, df_articles):
        """Prepare embeddings matrix and indices"""
        if isinstance(embeddings, dict):
            article_ids = list(embeddings.keys())
            matrix = np.vstack(list(embeddings.values()))
        elif isinstance(embeddings, pd.DataFrame):
            article_ids = embeddings.index.astype(int).tolist()
            matrix = embeddings.values
        else:
            article_ids = df_articles["article_id"].tolist()
            matrix = embeddings

        indices = {aid: i for i, aid in enumerate(article_ids)}
        logging.info(f"Embeddings matrix shape: {matrix.shape}")

        return article_ids, matrix, indices

    def _calculate_user_stats(self, df_ratings):
        """Calculate statistics per user"""
        stats = (df_ratings
                .groupby("user_id")
                .agg(
                    n=("article_id", "count"),
                    avg_rating=("rating", "mean")
                )
                .reset_index())
        stats["avg_rating"] = stats["avg_rating"].round(2)
        logging.info(f"Calculated stats for {len(stats)} users")
        return stats

# Global instance
data_loader = DataLoader()
