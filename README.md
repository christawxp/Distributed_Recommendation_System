# Medium Content-Based Recommendation System

## Overview
This project integrates **Google Cloud Storage (GCS)**, **MongoDB**, and **Apache Airflow Composer** to build a content-based recommendation system for Medium. It leverages **machine learning** and **NLP** to recommend articles, writers, and content based on user interests and behavior.

## Features
- **Data Pipeline**: Orchestrated with Airflow to connect GCS and MongoDB for seamless data synchronization.
- **Recommendation Engine**:
  - Article recommendations using **TF-IDF** and **cosine similarity**.
  - Writer and user behavior recommendations leveraging **collaborative filtering**.
- **Predictive Modeling**: Models like **Random Forest** and **Linear Regression** predict engagement metrics (e.g., claps, votes).

## Technologies
- **Cloud**: Google Cloud Storage
- **Orchestration**: Apache Airflow
- **Database**: MongoDB
- **ML/NLP**: Python (TF-IDF, cosine similarity, Random Forest)

## Results
- Built a scalable pipeline for data-driven recommendations.
- Enhanced user engagement with personalized content suggestions.
- Predictive models achieved moderate success, highlighting areas for improvement.
