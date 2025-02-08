from fastapi import FastAPI
import feedparser
from datetime import datetime, timedelta
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import time
from threading import Thread

# FastAPI app instance
app = FastAPI()

# Setup for the Google News fetch function
def fetch_google_news(keywords):
    base_url = "https://news.google.com/rss/search?q={}&hl=en-NG&gl=NG&ceid=NG:en"
    all_articles = []
    
    # Get today's date and the date 7 days ago
    today_date = datetime.now()
    week_ago_date = today_date - timedelta(days=7)
    
    # Format the dates to match the RSS feed format
    today_str = today_date.strftime("%Y-%m-%d")
    week_ago_str = week_ago_date.strftime("%Y-%m-%d")

    for keyword in keywords:
        url = base_url.format(keyword.replace(" ", "+"))  # Format keyword for URL
        news_feed = feedparser.parse(url)

        for entry in news_feed.entries[:100]:  # Limit articles per keyword
            pub_date = entry.get("published", entry.get("updated", None))

            if pub_date:
                try:
                    parsed_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                except ValueError:
                    continue
                article_date = parsed_date.strftime("%Y-%m-%d")  # Convert to YYYY-MM-DD

                if week_ago_str <= article_date <= today_str:  # Check if within the past week
                    all_articles.append({
                        "keyword": keyword,
                        "title": entry.title,
                        "summary": entry.summary,
                        "link": entry.link,
                        "date": article_date
                    })

    return all_articles


# Sentiment analysis function
analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    scores = analyzer.polarity_scores(text)
    if scores['compound'] < -0.05:
        return "Negative"
    elif scores['compound'] > 0.05:
        return "Positive"
    else:
        return "Neutral"


# Email sending function
def send_email(subject, body, to_email):
    from_email = "israelbosun1@gmail.com"  # Replace with your email
    from_password = "pxmfasofzlevqikk"  # Replace with your email password (or use App Passwords)

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add body to email
    msg.attach(MIMEText(body, 'plain'))

    server = None  # Initialize server to prevent UnboundLocalError

    try:
        # Connect to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure connection
        server.login(from_email, from_password)

        # Send the email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)

        print("Email sent successfully")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if server:  # Only quit if server was initialized
            server.quit()


# News check function
def check_news():
    print(f"\nChecking news at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    keywords = [
        "Access Bank",
        "Access Corporation",
        "Access Holdings",
        "Bolaji Agbede",
        "Roosevelt Ogbonna",
        "Aigboje Aig-Imoukhuede"
    ]
    news_articles = fetch_google_news(keywords)

    negative_news = []

    for article in news_articles:
        sentiment = analyze_sentiment(article['title'] + " " + article['summary'])
        if sentiment == "Negative":
            negative_news.append(article)

    if negative_news:
        print("\n🚨 Negative News Found:")
        body = "🚨 Negative News Found:\n\n"
        for news in negative_news:
            body += f"- {news['title']}\n  {news['link']}\n"

        send_email("Negative News Alert", body, "israelbosun1@gmail.com")
    else:
        print("\n✅ No negative news found.")


# Schedule job to run every 6 hours
def run_scheduled_job():
    schedule.every(6).hours.do(check_news)

    while True:
        schedule.run_pending()
        time.sleep(1)


# Start the background thread to run scheduled jobs
def start_scheduled_jobs():
    thread = Thread(target=run_scheduled_job)
    thread.daemon = True
    thread.start()


# FastAPI endpoint to manually check the news
@app.get("/check_news")
def manual_check_news():
    check_news()
    return {"message": "News checked!"}


# Initialize the scheduler when the server starts
@app.on_event("startup")
def startup():
    start_scheduled_jobs()


# Run the FastAPI app with Uvicorn (Use this in your command line)
# uvicorn app_name:app --reload
