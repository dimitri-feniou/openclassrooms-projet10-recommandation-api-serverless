# model/content_based.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ContentBasedRecommender:
    """
    Memory-efficient content-based recommendation system that uses article embeddings
    to recommend articles to users based on their past interactions.
    """
    
    def __init__(self, embeddings, article_indices, article_ids):
        """
        Initialize the Content-Based Recommender without pre-computing similarity matrix.
        
        Parameters:
        ----------
        embeddings : numpy.ndarray
            Matrix of article embeddings where each row corresponds to an article
        article_indices : dict
            Dictionary mapping article_id to index in embeddings matrix
        article_ids : list
            List of article IDs
        """
        self.embeddings = embeddings
        self.article_indices = article_indices
        self.article_ids = article_ids
        self.user_profiles = {}
        
    def fit(self, ratings_df):
        """
        Build user profiles based on their article ratings.
        
        Parameters:
        ----------
        ratings_df : pandas.DataFrame
            DataFrame containing user_id, article_id, and rating columns
        """
        # Group by user_id and create a profile for each user
        for user_id, group in ratings_df.groupby('user_id'):
            # Create user profile as weighted average of article embeddings
            article_weights = {}
            user_vector = np.zeros(self.embeddings.shape[1])
            
            # Calculate weights based on ratings
            total_weight = 0
            
            for _, row in group.iterrows():
                article_id = row['article_id']
                rating = row['rating']
                
                # Skip if article not in our index
                if article_id not in self.article_indices:
                    continue
                
                # Get article embedding
                article_idx = self.article_indices[article_id]
                article_weights[article_id] = rating
                
                # Add weighted article vector to user profile
                user_vector += rating * self.embeddings[article_idx]
                total_weight += rating
            
            # Normalize user vector
            if total_weight > 0:
                user_vector /= total_weight
                
            self.user_profiles[user_id] = {
                'vector': user_vector,
                'article_weights': article_weights
            }
    
    def recommend(self, user_id, ratings_df, n=5):
        """
        Recommend articles for a specific user without using a pre-computed similarity matrix.
        
        Parameters:
        ----------
        user_id : int
            User ID to recommend articles for
        ratings_df : pandas.DataFrame
            DataFrame containing user_id, article_id, and rating columns
        n : int, optional
            Number of recommendations to return (default is 5)
            
        Returns:
        -------
        list
            List of tuples containing (article_id, similarity_score)
        """
        # If user not in profiles, return empty recommendations
        if user_id not in self.user_profiles:
            return []
        
        user_profile = self.user_profiles[user_id]
        user_vector = user_profile['vector']
        
        # Get articles the user has already interacted with
        user_articles = set(ratings_df[ratings_df['user_id'] == user_id]['article_id'].unique())
        
        # Calculate similarity between user profile and candidate articles
        # We'll do this in batches to avoid memory issues
        batch_size = 1000  # Adjust based on available memory
        scores = []
        
        # Process articles in batches
        for i in range(0, len(self.article_ids), batch_size):
            batch_ids = self.article_ids[i:i+batch_size]
            batch_indices = [self.article_indices[aid] for aid in batch_ids 
                            if aid not in user_articles]
            
            if not batch_indices:
                continue
                
            # Get embeddings for this batch
            batch_embeddings = self.embeddings[batch_indices]
            
            # Calculate cosine similarity for this batch
            similarities = cosine_similarity([user_vector], batch_embeddings)[0]
            
            # Add scores for this batch
            for j, idx in enumerate(batch_indices):
                article_id = self.article_ids[i + j]
                if article_id not in user_articles:
                    scores.append((article_id, similarities[j]))
        
        # Sort by similarity score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top n recommendations
        return scores[:n]
    
    # Alternative recommendation method that processes one article at a time
    # Slower but uses minimal memory
    def recommend_low_memory(self, user_id, ratings_df, n=5):
        """
        Ultra-low memory version that processes one article at a time.
        """
        # If user not in profiles, return empty recommendations
        if user_id not in self.user_profiles:
            return []
        
        user_profile = self.user_profiles[user_id]
        user_vector = user_profile['vector']
        
        # Get articles the user has already interacted with
        user_articles = set(ratings_df[ratings_df['user_id'] == user_id]['article_id'].unique())
        
        # Calculate similarity scores one article at a time
        scores = []
        
        for article_id in self.article_ids:
            # Skip articles the user has already interacted with
            if article_id in user_articles:
                continue
            
            article_idx = self.article_indices[article_id]
            article_vector = self.embeddings[article_idx]
            
            # Calculate cosine similarity between user vector and article vector
            # Manual computation to avoid memory overhead
            norm_user = np.linalg.norm(user_vector)
            norm_article = np.linalg.norm(article_vector)
            
            if norm_user > 0 and norm_article > 0:
                similarity = np.dot(user_vector, article_vector) / (norm_user * norm_article)
                scores.append((article_id, similarity))
        
        # Sort by similarity score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top n recommendations
        return scores[:n]