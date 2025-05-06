from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialize the VADER sentiment intensity analyzer
sid = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    # Get sentiment scores
    scores = sid.polarity_scores(text)
    
    # Determine sentiment based on compound score
    if scores['compound'] >= 0.1:
        return "positive"
    elif scores['compound'] <= -0.1:
        return "negative"
    else:
        return "neutral"

# Example test data with new sentences
test_data = [
    ("The product is an absolute game changer!", "positive"),
    ("I had an awful experience with customer service.", "negative"),
    ("The weather today is neither too hot nor too cold.", "neutral"),
    ("The new smartphone I bought is worth every penny.", "positive"),
    ("I don't care much for this movie, it's just average.", "neutral"),
    ("The project deadline was stressful, and I feel drained.", "negative"),
    ("This restaurant served the best meal I've had in years!", "positive"),
    ("The software update caused more problems than it solved.", "negative"),
    ("I'm undecided about this product, it's okay but not great.", "neutral"),
    ("The concert was absolutely phenomenal, the energy was amazing!", "positive"),
]

# Count correct predictions
correct_predictions = 0

# Loop through test data and check if the predicted sentiment matches the actual sentiment
for sentence, actual_sentiment in test_data:
    predicted_sentiment = analyze_sentiment(sentence)
    if predicted_sentiment == actual_sentiment:
        correct_predictions += 1

# Calculate accuracy
accuracy = correct_predictions / len(test_data) * 100
print(f"Accuracy: {accuracy}%")
