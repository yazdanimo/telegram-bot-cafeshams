import json
import os
import logging
import re
from bs4 import BeautifulSoup
from langdetect import detect
import asyncio

def load_sources():
    """Load news sources from sources.json"""
    try:
        with open("sources.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("sources.json not found")
        return []
    except Exception as e:
        logging.error(f"Error loading sources: {e}")
        return []

def load_set(filename: str) -> set:
    """Load a set from JSON file"""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return set(json.load(f))
    except Exception as e:
        logging.error(f"Error loading {filename}: {e}")
    return set()

def save_set(data: set, filename: str):
    """Save a set to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(list(data), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving {filename}: {e}")

def extract_full_content(html: str) -> str:
    """Extract main content from HTML"""
    if not html:
        return ""
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # Try to find main content
        content = ""
        
        # Look for common content containers
        for selector in [
            'article', 
            '.content', 
            '.post-content', 
            '.entry-content',
            '.article-content',
            '.news-content',
            'main',
            '.main-content'
        ]:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                break
        
        # If no main content found, get all text
        if not content:
            content = soup.get_text(strip=True)
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n+', '\n', content)
        
        return content[:2000]  # Limit length
        
    except Exception as e:
        logging.error(f"Error extracting content: {e}")
        return ""

def summarize_fa(text: str) -> str:
    """Summarize Persian text"""
    if not text:
        return ""
    
    try:
        # Simple summarization: take first few sentences
        sentences = text.split('.')
        summary_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 20:
                summary_sentences.append(sentence)
                if len(summary_sentences) >= 3:
                    break
        
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary[:500]  # Limit length
        
    except Exception as e:
        logging.error(f"Error summarizing Persian text: {e}")
        return text[:300]

def summarize_en(text: str) -> str:
    """Summarize English text"""
    if not text:
        return ""
    
    try:
        # Simple summarization: take first few sentences
        sentences = text.split('.')
        summary_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 20:
                summary_sentences.append(sentence)
                if len(summary_sentences) >= 3:
                    break
        
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary[:500]  # Limit length
        
    except Exception as e:
        logging.error(f"Error summarizing English text: {e}")
        return text[:300]

def format_news(source_name: str, title: str, summary: str, link: str) -> str:
    """Format news for sending"""
    try:
        # Clean title
        title = title.strip()
        if len(title) > 100:
            title = title[:97] + "..."
        
        # Clean summary
        summary = summary.strip()
        if len(summary) > 400:
            summary = summary[:397] + "..."
        
        # Format message
        formatted = f"📰 {source_name}\n\n"
        formatted += f"🔸 {title}\n\n"
        formatted += f"{summary}\n\n"
        formatted += f"🔗 {link}"
        
        return formatted
        
    except Exception as e:
        logging.error(f"Error formatting news: {e}")
        return f"📰 {source_name}\n\n{title}\n\n{link}"

def is_garbage(text: str) -> bool:
    """Check if text is garbage/low quality"""
    if not text or len(text.strip()) < 50:
        return True
    
    try:
        # Check for common garbage patterns
        garbage_patterns = [
            r'^[\s\W]+$',  # Only whitespace and symbols
            r'^\d+$',      # Only numbers
            r'^[a-zA-Z\s]+$' if len(text) < 20 else None,  # Very short English
        ]
        
        for pattern in garbage_patterns:
            if pattern and re.match(pattern, text):
                return True
        
        # Check for repetitive content
        words = text.split()
        if len(words) > 0:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:  # Too repetitive
                return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error checking garbage: {e}")
        return False

async def safe_send(bot, chat_id: int, text: str, **kwargs):
    """Safely send message with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=chat_id, text=text, **kwargs)
            return
        except Exception as e:
            logging.error(f"Send attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.error(f"Failed to send message after {max_retries} attempts")
                raise e
