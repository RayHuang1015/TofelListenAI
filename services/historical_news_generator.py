"""
Historical News Content Generator

Creates realistic international news content for historical dates (2018-2025)
when real RSS feeds don't have historical data.
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Any
import random
import json

class HistoricalNewsGenerator:
    """Generate realistic historical news content for any date"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # News categories for international content
        self.categories = {
            'world': ['Politics', 'Diplomacy', 'International Relations', 'Global Economy'],
            'business': ['Markets', 'Trade', 'Corporate', 'Technology', 'Energy'],
            'technology': ['Innovation', 'AI', 'Cybersecurity', 'Digital Transformation'],
            'politics': ['Elections', 'Policy', 'Government', 'International Affairs']
        }
        
        # International news sources
        self.sources = [
            'BBC World Service',
            'Reuters International', 
            'AP News International',
            'CNN International',
            'Bloomberg Global',
            'Financial Times'
        ]
        
        # Major global events and topics by year for realistic content
        self.yearly_themes = {
            2018: ['Trade Wars', 'Brexit Negotiations', 'World Cup Russia', 'Tech Regulations'],
            2019: ['Climate Change Summit', 'Hong Kong Protests', 'US-China Relations', 'European Elections'],
            2020: ['COVID-19 Pandemic', 'Remote Work Revolution', 'Economic Recovery', 'Vaccine Development'],
            2021: ['Global Vaccination', 'Supply Chain Crisis', 'Climate Commitments', 'Digital Currency'],
            2022: ['Ukraine Conflict', 'Energy Crisis', 'Inflation Concerns', 'Space Exploration'],
            2023: ['AI Revolution', 'Economic Stability', 'Green Energy Transition', 'Global Cooperation'],
            2024: ['Election Year', 'Technology Innovation', 'Climate Action', 'International Trade'],
            2025: ['Future Planning', 'Sustainable Development', 'Global Partnerships', 'Digital Society']
        }
    
    def generate_news_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Generate realistic news articles for a specific historical date"""
        try:
            year = target_date.year
            themes = self.yearly_themes.get(year, ['International News', 'Global Affairs', 'World Events'])
            
            # Generate enough articles to reach approximately 3 hours (10800 seconds)
            target_duration = 10800  # 3 hours in seconds
            articles = []
            total_duration = 0
            article_index = 0
            
            while total_duration < target_duration and article_index < 50:  # Max 50 articles per day
                article = self._create_article(target_date, themes, article_index)
                articles.append(article)
                total_duration += article.get('duration', 300)  # Default 5 minutes if not specified
                article_index += 1
            
            self.logger.info(f"Generated {len(articles)} historical news articles for {target_date}")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error generating news for {target_date}: {e}")
            return []
    
    def _create_article(self, target_date: date, themes: List[str], index: int) -> Dict[str, Any]:
        """Create a single realistic news article"""
        
        # Select category and theme
        category = random.choice(list(self.categories.keys()))
        theme = random.choice(themes)
        source = random.choice(self.sources)
        
        # Generate realistic content
        title = self._generate_title(theme, category)
        content = self._generate_content(title, theme, target_date)
        
        # Calculate realistic reading time for listening (slower than reading)
        word_count = len(content.split())
        # Assuming 150-180 words per minute for listening comprehension
        estimated_duration = max(180, min(600, word_count * 0.4))  # 3-10 minutes per article
        
        # Format compatible with ContentSource model
        return {
            'title': title,
            'name': title[:50],  # Max 50 chars for database name field
            'url': f"https://example-news.com/{target_date.strftime('%Y/%m/%d')}/article-{index+1}",
            'type': 'news_article',
            'language': 'en',
            'duration': int(estimated_duration),  # seconds
            'description': content[:200] + '...' if len(content) > 200 else content,
            'topic': theme,
            'category': category,
            'published_date': datetime.combine(target_date, datetime.min.time()),
            'transcript_text': content,
            'region': 'global',
            'source': source,
            'content_metadata': {
                'provider': 'HistoricalNewsGenerator',
                'word_count': word_count,
                'theme': theme,
                'generated_for_date': target_date.strftime('%Y-%m-%d')
            }
        }
    
    def _generate_title(self, theme: str, category: str) -> str:
        """Generate realistic news title"""
        
        title_templates = {
            'world': [
                f"Global Leaders Discuss {theme}",
                f"{theme} Shapes International Policy", 
                f"World Markets React to {theme}",
                f"Community Responds to {theme}"
            ],
            'business': [
                f"Corporations Adapt to {theme}",
                f"Markets Respond to {theme}",
                f"Trade Affected by {theme}",
                f"Leaders Navigate {theme}"
            ],
            'technology': [
                f"{theme} Technology Breakthrough",
                f"Tech Leaders Advance {theme}", 
                f"Technology Summit on {theme}",
                f"Major {theme} Partnership"
            ],
            'politics': [
                f"Relations Strengthen via {theme}",
                f"Political Shifts in {theme}",
                f"{theme} Agreement Reached",
                f"Leaders Unite on {theme}"
            ]
        }
        
        templates = title_templates.get(category, title_templates['world'])
        return random.choice(templates)
    
    def _generate_content(self, title: str, theme: str, target_date: date) -> str:
        """Generate realistic news article content"""
        
        # Create structured content for 3+ minute read
        intro = f"In a significant development regarding {theme}, international experts and leaders gathered to address key challenges and opportunities. "
        
        main_content = f"""
        The latest developments in {theme} have captured global attention as stakeholders work together to find innovative solutions. 
        International cooperation continues to play a crucial role in addressing these complex issues that affect communities worldwide.
        
        Key stakeholders emphasized the importance of sustainable approaches and long-term planning. The international community has shown 
        strong commitment to collaborative efforts that promote global stability and prosperity.
        
        Economic implications of these developments are being carefully monitored by financial markets and policy makers. 
        Experts suggest that these changes could have far-reaching effects on international trade and cooperation.
        
        Environmental considerations remain at the forefront of discussions, with leaders emphasizing the need for 
        responsible development and sustainable practices. The global community continues to work toward solutions that 
        balance economic growth with environmental protection.
        
        Technology plays an increasingly important role in addressing these challenges, with innovative solutions 
        being developed by international teams of researchers and engineers. Digital transformation continues to 
        create new opportunities for global cooperation and communication.
        
        Social and cultural impacts are also being considered as communities adapt to changing global conditions. 
        Education and public awareness campaigns help ensure that people understand the importance of these developments 
        and their role in creating positive change.
        
        Looking ahead, international organizations are developing comprehensive strategies to address long-term 
        challenges and opportunities. These efforts require sustained commitment from governments, businesses, 
        and civil society organizations around the world.
        """
        
        conclusion = f"""
        As the global community continues to address {theme}, the importance of international cooperation becomes 
        increasingly clear. These developments represent significant steps toward a more sustainable and prosperous future 
        for all nations and communities.
        
        The ongoing dialogue between international partners demonstrates the value of collaborative problem-solving 
        and shared commitment to positive change. Regular monitoring and assessment will help ensure that progress 
        continues in the months and years ahead.
        """
        
        return intro + main_content + conclusion
    
    def get_estimated_total_duration(self, articles: List[Dict[str, Any]]) -> int:
        """Calculate total estimated listening duration for articles"""
        return sum(article.get('estimated_duration', 300) for article in articles)