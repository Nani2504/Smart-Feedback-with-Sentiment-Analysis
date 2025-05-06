import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
# Ensure vader_lexicon is downloaded
nltk.download('vader_lexicon')

# Initialize the VADER sentiment intensity analyzer
sid = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    # Get sentiment scores
    scores = sid.polarity_scores(text)
    if 'but' in text or 'however' in text or 'although' in text: 
            return "neutral" 
    # Adjust thresholds for better classification of mixed feedback
    if scores['compound'] >= 0.1:  # Positive sentiment
        return "positive"
    elif scores['compound'] <= -0.1:  # Negative sentiment
        return "negative"
    else:  # Neutral sentiment for compound scores between -0.1 and 0.1
        return "neutral" 


