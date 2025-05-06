from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sentiment_analyzer import analyze_sentiment  # You must create this module
import os
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import google.generativeai as genai  # Gemini API
import csv
from flask import Response
import smtplib
from email.message import EmailMessage

# === Gemini API Key ===
genai.configure(api_key="AIzaSyCXR-ExkW3f52gP9M_4bCDQvGBLhbzXaCs")  # Replace with your real key
gemini_model = genai.GenerativeModel("gemini-2.0-flash")


def extract_actions(text):
    prompt = (
        "Analyze the following user feedback and extract key action items as concise bullet points.\n"
        "Each point should be short (2–5 words) and describe a specific, actionable improvement. Avoid full sentences.\n\n"
        f"Feedback:\n{text}\n\n"
        "Bullet point actions:"
    )
    try:
        response = gemini_model.generate_content(prompt)
        cleaned_text = response.text.replace("*", "").strip()
        return cleaned_text

    except Exception:
        return "- No action items available."

SMTP_EMAIL = "dhanushnani25042005@gmail.com"
SMTP_PASSWORD = "vewbnxzshafgqqbw"  # App password, not Gmail login password

# === Flask App Setup ===
app = Flask("__name__")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ADMIN_PASSWORD = "admin123"

# === Feedback Model ===
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))  # Add email column
    feedback = db.Column(db.Text)
    sentiment = db.Column(db.String(20))  # positive/negative/neutral
    actions = db.Column(db.Text)  # ✅ New column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# === Routes ===
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        feedback = request.form.get('feedback')
        email = request.form.get('email')
        sentiment = analyze_sentiment(feedback)
        actions = extract_actions(feedback)  # ✅ Extract actions

        new_entry = Feedback(
            name=name,
            feedback=feedback,
            email = request.form.get('email'),
            sentiment=sentiment,
            actions=actions  # ✅ Save to DB
        )
        db.session.add(new_entry)
        db.session.commit()

        if email:
            send_sentiment_email(email, name, sentiment)

        return redirect(url_for('thank_you', name=name))

    return render_template('form.html')

@app.route('/admin/export-csv')
def export_csv():
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()

    def generate():
        data = io.StringIO()
        writer = csv.writer(data)

        # Header
        writer.writerow(('ID', 'Name', 'Feedback', 'Sentiment', 'Created At'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # Rows
        for fb in feedbacks:
            writer.writerow((fb.id, fb.name, fb.feedback, fb.sentiment, fb.created_at))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=feedback.csv'}
    )

def send_sentiment_email(to_email, user_name, sentiment):
    msg = EmailMessage()
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email
    msg['Subject'] = "Thank you for your feedback!"

    if sentiment == 'positive':
        msg.set_content(f"Hi {user_name},\n\nThank you for your kind feedback! We're thrilled to hear you're satisfied with our service.\n\n- Team")
    elif sentiment == 'negative':
        msg.set_content(f"Hi {user_name},\n\nWe're sorry to hear you had a bad experience. Your feedback is valuable and we'll work hard to improve.\n\nThank you for letting us know.\n- Team")
    else:
        msg.set_content(f"Hi {user_name},\n\nThank you for your honest feedback. We appreciate you taking the time to share your thoughts.\n\n- Team")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/thank-you')
def thank_you():
    name = request.args.get('name', 'User')
    return render_template('thank_you.html', name=name)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            all_feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
            sentiment_counts = get_sentiment_counts()
            pie_chart_image = generate_pie_chart(sentiment_counts)

            return render_template('admin.html', feedbacks=all_feedback,
                                   sentiment_counts=sentiment_counts,
                                   pie_chart_image=pie_chart_image)
        else:
            return redirect(url_for('admin'))

    return render_template('admin_login.html')

def get_sentiment_counts():
    positive_count = Feedback.query.filter_by(sentiment='positive').count()
    negative_count = Feedback.query.filter_by(sentiment='negative').count()
    neutral_count = Feedback.query.filter_by(sentiment='neutral').count()

    total_feedback = positive_count + negative_count + neutral_count

    if total_feedback == 0:
        overall_review = "No feedback available yet."
    elif positive_count > negative_count and positive_count > neutral_count:
        overall_review = "Overall Positive Feedback!"
    elif negative_count > positive_count and negative_count > neutral_count:
        overall_review = "Overall Negative Feedback."
    else:
        overall_review = "Overall Neutral Feedback."

    return {
        'positive': positive_count,
        'negative': negative_count,
        'neutral': neutral_count,
        'overall_review': overall_review
    }

def generate_pie_chart(sentiment_counts):
    labels = ['Positive', 'Negative', 'Neutral']
    sizes = [sentiment_counts['positive'], sentiment_counts['negative'], sentiment_counts['neutral']]
    colors = ['green', 'red', 'orange']

    fig, ax = plt.subplots()
    if sum(sizes) == 0:
        sizes = [1, 1, 1]  # Avoid empty chart
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax.axis('equal')

    img_io = io.BytesIO()
    FigureCanvas(fig).print_png(img_io)
    img_io.seek(0)

    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return img_base64

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)