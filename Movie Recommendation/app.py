from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import random
import json
import os
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Sample movie data with multiple genres
movies = [
    {"id": 1, "title": "The Shawshank Redemption", "genres": ["Drama", "Crime"], "year": 1994, "rating": 9.3},
    {"id": 2, "title": "The Godfather", "genres": ["Crime", "Drama"], "year": 1972, "rating": 9.2},
    {"id": 3, "title": "The Dark Knight", "genres": ["Action", "Crime", "Drama"], "year": 2008, "rating": 9.0},
    {"id": 4, "title": "Pulp Fiction", "genres": ["Crime", "Drama"], "year": 1994, "rating": 8.9},
    {"id": 5, "title": "Inception", "genres": ["Sci-Fi", "Action", "Adventure"], "year": 2010, "rating": 8.8},
    {"id": 6, "title": "The Matrix", "genres": ["Sci-Fi", "Action"], "year": 1999, "rating": 8.7},
    {"id": 7, "title": "Parasite", "genres": ["Drama", "Thriller", "Comedy"], "year": 2019, "rating": 8.6},
    {"id": 8, "title": "The Godfather: Part II", "genres": ["Crime", "Drama"], "year": 1974, "rating": 9.0},
    {"id": 9, "title": "Interstellar", "genres": ["Sci-Fi", "Adventure", "Drama"], "year": 2014, "rating": 8.6},
    {"id": 10, "title": "The Lord of the Rings: The Return of the King", "genres": ["Adventure", "Fantasy", "Action"], "year": 2003, "rating": 8.9},
    {"id": 11, "title": "Fight Club", "genres": ["Drama"], "year": 1999, "rating": 8.8},
    {"id": 12, "title": "The Silence of the Lambs", "genres": ["Crime", "Thriller", "Drama"], "year": 1991, "rating": 8.6},
    {"id": 13, "title": "The Prestige", "genres": ["Drama", "Mystery", "Thriller"], "year": 2006, "rating": 8.5},
    {"id": 14, "title": "The Departed", "genres": ["Crime", "Drama", "Thriller"], "year": 2006, "rating": 8.5},
    {"id": 15, "title": "The Dark Knight Rises", "genres": ["Action", "Adventure"], "year": 2012, "rating": 8.4},
    {"id": 16, "title": "The Social Network", "genres": ["Biography", "Drama"], "year": 2010, "rating": 7.8},
    {"id": 17, "title": "The Grand Budapest Hotel", "genres": ["Adventure", "Comedy", "Drama"], "year": 2014, "rating": 8.1},
    {"id": 18, "title": "Whiplash", "genres": ["Drama", "Music"], "year": 2014, "rating": 8.5},
    {"id": 19, "title": "The Martian", "genres": ["Adventure", "Drama", "Sci-Fi"], "year": 2015, "rating": 8.0},
    {"id": 20, "title": "Mad Max: Fury Road", "genres": ["Action", "Adventure", "Sci-Fi"], "year": 2015, "rating": 8.1}
]

@app.route('/')
def home():
    return render_template('index.html')

# Get all unique genres from the movies
def get_all_genres():
    genres = set()
    for movie in movies:
        for genre in movie['genres']:
            genres.add(genre)
    return sorted(list(genres))

@app.route('/api/movies', methods=['GET'])
def get_movies():
    genre = request.args.get('genre')
    if genre:
        if genre.lower() == 'all':
            return jsonify(movies)
        filtered_movies = [movie for movie in movies if genre.lower() in [g.lower() for g in movie['genres']]]
        return jsonify(filtered_movies)
    return jsonify(movies)

@app.route('/api/genres', methods=['GET'])
def get_genres():
    return jsonify(get_all_genres())

@app.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = next((m for m in movies if m['id'] == movie_id), None)
    if movie:
        return jsonify(movie)
    return jsonify({"error": "Movie not found"}), 404

def calculate_genre_affinity(selected_movie, candidate_movie):
    """Calculate a score based on genre overlap and rating similarity"""
    if selected_movie['id'] == candidate_movie['id']:
        return -1  # Don't recommend the same movie
        
    # Calculate genre overlap (Jaccard similarity)
    selected_genres = set(g.lower() for g in selected_movie['genres'])
    candidate_genres = set(g.lower() for g in candidate_movie['genres'])
    
    intersection = len(selected_genres.intersection(candidate_genres))
    union = len(selected_genres.union(candidate_genres))
    
    if union == 0:
        genre_similarity = 0
    else:
        genre_similarity = intersection / union
    
    # Calculate rating similarity (closer ratings are better)
    rating_diff = abs(selected_movie['rating'] - candidate_movie['rating'])
    rating_similarity = 1 / (1 + rating_diff)  # Convert to 0-1 range
    
    # Calculate year similarity (more recent movies get a small boost)
    year_diff = abs(selected_movie['year'] - candidate_movie['year'])
    year_similarity = 1 / (1 + year_diff / 10)  # Smaller penalty for year difference
    
    # Combine scores with weights
    score = (genre_similarity * 0.6 + 
             rating_similarity * 0.3 + 
             year_similarity * 0.1)
    
    return score

@app.route('/api/recommend/<int:movie_id>', methods=['GET'])
def get_recommendations(movie_id):
    selected_movie = next((m for m in movies if m['id'] == movie_id), None)
    if not selected_movie:
        return jsonify({"error": "Movie not found"}), 404
    
    # Calculate scores for all other movies
    scored_movies = []
    for movie in movies:
        if movie['id'] == movie_id:
            continue
            
        score = calculate_genre_affinity(selected_movie, movie)
        scored_movies.append((movie, score))
    
    # Sort by score in descending order
    scored_movies.sort(key=lambda x: x[1], reverse=True)
    
    # Get top 5 recommendations
    recommendations = [movie for movie, score in scored_movies[:5]]
    
    # If we don't have enough recommendations, add some popular ones
    if len(recommendations) < 5:
        popular_movies = sorted(
            [m for m in movies if m['id'] != movie_id],
            key=lambda x: x['rating'],
            reverse=True
        )
        for movie in popular_movies:
            if len(recommendations) >= 5:
                break
            if movie not in recommendations:
                recommendations.append(movie)
    
    return jsonify(recommendations)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)
